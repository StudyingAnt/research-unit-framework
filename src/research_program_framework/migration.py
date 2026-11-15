"""Conservative v0.5 adoption with external verified backups and guarded undo."""

import base64
from dataclasses import dataclass
import hashlib
from pathlib import Path
import uuid

from .initialization import installation
from .manifests import validate_legacy_baseline, validate_release_manifest, verify_release
from .paths import ValidationError, validate_payload, validate_path_set, MAX_FILE_BYTES
from .release import fingerprint
from .storage import Store
from .updates import Action, RECEIPT, MAX_METADATA, _compare, _digest_value, encode, decode, manifest_dict
from .merge import diff_text, has_markers


BRIDGE = (b'# Framework v1.1 policy entry point\n\n'
          b'Explicitly read `.research-framework/policy/AGENTS.md` and '\
          b'`.research-framework/policy/REPORTING.md` before work.\n'
          b'The shared v1.1 reporting contract supersedes obsolete generic reporting rules below; '\
          b'preserve all project-specific scientific instructions and researcher decisions.\n'
          b'Use `python3 .research-framework/runtime.pyz --help` for v1.1 tools.\n\n'
          b'<!-- Preserved prior project instructions follow unchanged. -->\n\n')


def _checkpoint(event, index=None):
    """Failure-injection seam for synthetic acceptance tests."""


@dataclass(frozen=True)
class MigrationPlan:
    project: str
    payload: str
    root_identity: tuple
    release: object
    source_files: tuple
    legacy_manifest: dict
    legacy_files: tuple
    actions: tuple
    resolutions: tuple
    bridge: bool

    @property
    def digest(self):
        return hashlib.sha256(encode(_digest_value(self))).hexdigest()

    @property
    def conflicts(self):
        return tuple(a.path for a in self.actions if a.disposition == 'CONFLICT')

    def describe(self):
        return {'plan_digest': self.digest, 'project': self.project,
                'version': self.release.framework_version, 'conflicts': list(self.conflicts),
                'legacy': 'Observed Starter v3 / Framework v0.5; historical installed revision unknown',
                'actions': [{'path': a.path, 'action': a.disposition, 'reason': a.reason,
                             'before': a.before.fingerprint() if a.before else None,
                             'after': fingerprint(a.content, a.mode) if a.content is not None else None,
                             'diff': diff_text(a.before.data, a.content) if a.before and a.changes_file else ''}
                            for a in self.actions]}


def plan_migration(project, payload, release, legacy_manifest, legacy_files, resolutions=None, bridge=False):
    """Read-only plan; the observed ancestor is never claimed as installed metadata.

    Explicit keep-local resolutions are limited to recognized legacy managed
    paths. Root bridges require a separate reviewed administrative choice.
    Scientific seed records are never introduced into an existing project.
    """
    verify_release(payload, release)
    legacy = validate_legacy_baseline(legacy_manifest)
    if set(legacy_files) != {f.path for f in legacy.files}:
        raise ValidationError('Legacy ancestor inventory mismatch')
    for f in legacy.files:
        if fingerprint(legacy_files[f.path], f.mode) != {'size': f.size, 'sha256': f.sha256, 'mode': f.mode}:
            raise ValidationError('Legacy ancestor content mismatch')
    resolutions = dict(resolutions or {})
    validate_path_set(resolutions)
    old = {f.path: f for f in legacy.files}
    with Store(project) as target, Store(payload) as source:
        if target.directory('.research-framework') is not None:
            raise ValidationError('Existing framework state requires inspection, recovery or update, not adoption')
        if target.read('AGENTS.md').data is None or target.read('tools/new_unit.py').data is None:
            raise ValidationError('Missing legacy entry points; unknown projects require a separate reviewed adapter')
        incoming = {f.path: source.read(f.path) for f in release.files}
        actions, consumed, total = [], set(), 0
        for f in release.files:
            if f.ownership == 'D' and f.project_owner == 'B':
                actions.append(Action(f.path, 'SKIP_SCIENCE', 'Never introduce scientific records during adoption', None, None, None))
                continue
            before = target.read(f.path)
            total += len(before.data or b'')
            if total > 256 * 1024 * 1024:
                raise ValidationError('Migration content exceeds bounds')
            data, mode = incoming[f.path].data, f.mode
            if f.ownership == 'D':
                result = before.data if before.data is not None else data
                mode = before.mode or mode
                disposition, reason = 'KEEP_PROJECT' if before.data is not None else 'ADD_CONFIG', 'Preserve project-specific configuration'
                if bridge and f.path in {'AGENTS.md', 'CLAUDE.md', 'REPORT_TEMPLATE.md'} and before.data is not None:
                    result = BRIDGE + before.data
                    disposition, reason = 'BRIDGE', 'Explicitly reviewed policy loader; original bytes preserved'
            else:
                previous = old.get(f.path)
                disposition, reason, result, mode = _compare(f.path, before,
                    legacy_files.get(f.path), previous.mode if previous else None, data, f.mode)
                if f.path in resolutions:
                    if previous is None:
                        raise ValidationError('Cannot resolve an unknown destination collision by adoption')
                    value = resolutions[f.path]
                    if value is not None and (type(value) is not bytes or len(value) > MAX_FILE_BYTES or has_markers(value)):
                        raise ValidationError('Invalid or unresolved adoption resolution')
                    result = before.data if value is None else value
                    mode = (before.mode or f.mode) if result is not None else None
                    disposition, reason = 'KEEP_LOCAL' if value is None else 'RESOLVED', 'Explicit reviewed legacy resolution'
                    consumed.add(f.path)
            actions.append(Action(f.path, disposition, reason, before, result, mode))
        if consumed != set(resolutions):
            raise ValidationError('Resolution targets an initialization seed or unknown legacy file')
        verify_release(payload, release)
        return MigrationPlan(str(target.root), str(source.root), target.identity, release,
                             tuple(sorted(incoming.items())), legacy_manifest, tuple(sorted(legacy_files.items())),
                             tuple(actions), tuple(sorted(resolutions.items())), bool(bridge))


def _external(project, backup_root):
    project, backup_root = Path(project).absolute(), Path(backup_root).absolute()
    if backup_root == project or project in backup_root.parents or backup_root in project.parents:
        raise ValidationError('Migration recovery storage must be separate from the project and its ancestors')
    return backup_root


def _save(backup, directory, journal):
    path = directory + '/journal.json'
    body = dict(journal)
    body['checksum'] = hashlib.sha256(encode(journal)).hexdigest()
    backup.atomic(path, encode(body), backup.read(path, MAX_METADATA))


def _blob(backup, directory, side, index, expected):
    snapshot = backup.read(f'{directory}/{side}-{index}.bin')
    if snapshot.data is None or fingerprint(snapshot.data, expected['mode']) != expected:
        raise ValidationError('Missing or corrupt migration recovery blob')
    return snapshot.data


def _write(store, path, data, mode, expected, stage, created):
    store.ensure_dir(path.rsplit('/', 1)[0], created) if '/' in path else None
    store.ensure_dir(stage.rsplit('/', 1)[0], created)
    # Journaled parent creation legitimately changes a missing-parent snapshot.
    current = store.read(path)
    if (current.data, current.mode, current.token) != (expected.data, expected.mode, expected.token):
        raise ValidationError('Migration target changed before publication')
    for parent, token in expected.parents:
        if token is not None and dict(current.parents).get(parent) != token:
            raise ValidationError('Migration target parent changed')
    staged = store.create(stage, data, mode)
    return store.publish(stage, path, current, staged)


def apply_migration(plan, backup_root):
    if plan.conflicts:
        raise ValidationError('Unresolved migration conflicts; project remains unchanged')
    backup_root = _external(plan.project, backup_root)
    with Store(plan.project) as store, Store(backup_root) as backup, store.bootstrap_lock(), backup.bootstrap_lock():
        fresh = plan_migration(plan.project, plan.payload, plan.release, plan.legacy_manifest,
                               dict(plan.legacy_files), dict(plan.resolutions), plan.bridge)
        if fresh != plan:
            raise ValidationError('Migration plan is stale')
        operation = uuid.uuid4().hex
        directory = 'migration-' + operation
        backup.ensure_dir(directory)
        entries = [a for a in plan.actions if a.changes_file]
        installed = {a.path: fingerprint(a.content, a.mode) if a.content is not None else None
                     for a in plan.actions if a.path in {f.path for f in plan.release.files if f.ownership == 'A'}}
        # Cache exact new upstream ancestors separately from retained local bytes.
        sources = dict(plan.source_files)
        for digest, data in sorted({f.sha256: sources[f.path].data for f in plan.release.files if f.ownership == 'A'}.items()):
            path = '.research-framework/baselines/' + digest
            entries.append(Action(path, 'BASE', 'Exact upstream ancestor', store.read(path), data, '0644'))
        adoption = {'schema_version': 1, 'operation_id': operation, 'backup_root': str(backup_root),
                    'plan_digest': plan.digest, 'legacy_baseline_sha256': hashlib.sha256(encode(plan.legacy_manifest)).hexdigest(),
                    'historical_installed_revision': None, 'preserved_local': [a.path for a in plan.actions if a.disposition == 'KEEP_LOCAL']}
        path = '.research-framework/adoption.json'
        entries.append(Action(path, 'STATE', 'Adoption provenance', store.read(path), encode(adoption), '0644'))
        receipt = installation(plan.release, installed)
        entries.append(Action(RECEIPT, 'STATE', 'Installation receipt last', store.read(RECEIPT), encode(receipt), '0644'))
        journal = {'schema_version': 1, 'kind': 'framework_adoption', 'project': plan.project,
                   'root_identity': list(store.identity), 'operation': operation, 'plan_digest': plan.digest,
                   'release': manifest_dict(plan.release), 'status': 'PREPARING', 'created': [],
                   'entries': [{'path': a.path, 'before': a.before.fingerprint(), 'before_token': a.before.token,
                                'before_parents': a.before.parents, 'after': fingerprint(a.content, a.mode),
                                'after_token': None, 'progress': 'pending', 'restore': 'pending', 'restore_token': None}
                               for a in entries]}
        _save(backup, directory, journal)
        for index, action in enumerate(entries):
            if action.before.data is not None:
                backup.create(f'{directory}/before-{index}.bin', action.before.data)
                _blob(backup, directory, 'before', index, action.before.fingerprint())
            backup.create(f'{directory}/after-{index}.bin', action.content)
            _blob(backup, directory, 'after', index, fingerprint(action.content, action.mode))
        # Every recoverable original and after-image is verified before any
        # directory/file is created in the target project.
        for action in entries: store.check(action.path, action.before)
        _checkpoint('backups_verified')
        journal['status'] = 'APPLYING'; _save(backup, directory, journal)
        def created(path, token):
            if token is None:
                journal['created'].append({'path': path, 'identity': None})
            else:
                journal['created'][-1]['identity'] = token
            _save(backup, directory, journal)
        try:
            for index, action in enumerate(entries):
                journal['entries'][index]['progress'] = 'writing'; _save(backup, directory, journal)
                _checkpoint('before_write', index)
                content = _blob(backup, directory, 'after', index, journal['entries'][index]['after'])
                after = _write(store, action.path, content, action.mode, action.before,
                               f'.research-framework/bootstrap-stage-{operation}/{index}.bin', created)
                _checkpoint('published', index)
                journal['entries'][index].update(progress='done', after_token=after.token)
                _save(backup, directory, journal)
            for entry in journal['entries']:
                current = store.read(entry['path'])
                if current.fingerprint() != entry['after'] or current.token != tuple(entry['after_token']):
                    raise ValidationError('Migration post-state changed')
            for path, expected in installed.items():
                if store.read(path).fingerprint() != expected:
                    raise ValidationError('Tracked local file changed during migration')
            journal['status'] = 'COMMITTED'; _save(backup, directory, journal)
            return {'operation_id': operation, 'status': 'COMMITTED', 'backup_directory': str(backup_root / directory),
                    'version': plan.release.framework_version}
        except Exception:
            # Explicit recovery is retained externally even if the target has
            # no complete installation metadata. Do not obscure the operation.
            raise ValidationError('Migration interrupted; retain and recover from ' + str(backup_root / directory))


def _load_recovery(directory):
    directory = Path(directory).absolute()
    with Store(directory.parent) as backup:
        raw = backup.read(directory.name + '/journal.json', MAX_METADATA)
        journal = decode(raw.data)
        checksum = journal.pop('checksum', None)
        if checksum != hashlib.sha256(encode(journal)).hexdigest():
            raise ValidationError('Migration journal checksum mismatch')
        if journal.get('schema_version') != 1 or journal.get('kind') != 'framework_adoption':
            raise ValidationError('Unsupported migration recovery journal')
        if journal.get('status') not in {'PREPARING', 'APPLYING', 'COMMITTED', 'ROLLING_BACK', 'ROLLED_BACK'}:
            raise ValidationError('Unknown migration transaction state')
        release = validate_release_manifest(journal['release'])
        allowed = {f.path for f in release.files if f.ownership == 'A' or f.project_owner == 'C'}
        allowed.update('.research-framework/baselines/' + f.sha256 for f in release.files if f.ownership == 'A')
        allowed.update({RECEIPT, '.research-framework/adoption.json'})
        paths = [e['path'] for e in journal['entries']]
        validate_path_set(paths)
        if len(paths) != len(set(paths)) or not set(paths) <= allowed or paths[-1] != RECEIPT:
            raise ValidationError('Unregistered migration recovery targets')
        allowed_dirs = {p.rsplit('/', 1)[0] for p in paths if '/' in p}
        allowed_dirs.add('.research-framework/bootstrap-stage-' + journal['operation'])
        allowed_dirs.update('/'.join(p.split('/')[:n]) for p in list(allowed_dirs) for n in range(1, len(p.split('/'))))
        if any(item['path'] not in allowed_dirs for item in journal['created']):
            raise ValidationError('Unregistered migration recovery directory')
        return journal, raw


def plan_migration_rollback(directory):
    journal, raw = _load_recovery(directory)
    with Store(journal['project']) as store, Store(Path(directory).parent) as backup:
        if list(store.identity) != journal['root_identity']:
            raise ValidationError('Migration project identity changed')
        if journal['status'] == 'ROLLED_BACK':
            return {'plan_digest': hashlib.sha256(raw.data).hexdigest(), 'status': 'NO_CHANGE', 'targets': []}
        targets = []
        created = {item['path']: item['identity'] for item in journal['created']}
        for index, entry in enumerate(journal['entries']):
            current = store.read(entry['path'])
            expected = entry['before'] if entry['restore'] == 'done' or entry['progress'] == 'pending' else entry['after']
            token = entry['restore_token'] if entry['restore'] == 'done' else entry['before_token'] if entry['progress'] == 'pending' else entry['after_token']
            gap = entry['progress'] == 'writing' or entry['restore'] == 'writing'
            valid = current.fingerprint() == expected and (token is None or current.token == tuple(token))
            if gap:
                valid = valid or current.fingerprint() == entry['before'] and (entry['before_token'] is None or current.token == tuple(entry['before_token']))
            if entry['restore'] == 'writing':
                valid = valid or current.fingerprint() == entry['before']
            if not valid:
                raise ValidationError('Migration rollback would overwrite later local changes: ' + entry['path'])
            original_parents = dict(entry['before_parents'])
            for path, identity in current.parents:
                known = original_parents.get(path) or created.get(path)
                if known is not None and identity != tuple(known):
                    raise ValidationError('Migration recovery parent changed')
            if entry['before'] is not None and entry['progress'] != 'pending':
                _blob(backup, Path(directory).name, 'before', index, entry['before'])
            targets.append((entry['path'], _digest_value(current)))
        return {'plan_digest': hashlib.sha256(encode({'journal': hashlib.sha256(raw.data).hexdigest(), 'targets': targets})).hexdigest(),
                'status': journal['status'], 'targets': targets}


def rollback_migration(directory, digest):
    directory = Path(directory).absolute()
    journal, raw = _load_recovery(directory)
    with Store(journal['project']) as store, Store(directory.parent) as backup, store.bootstrap_lock(), backup.bootstrap_lock():
        plan = plan_migration_rollback(directory)
        if plan['plan_digest'] != digest: raise ValidationError('Migration recovery plan is stale')
        if plan['status'] == 'NO_CHANGE': return {'status': 'NO_CHANGE'}
        journal['status'] = 'ROLLING_BACK'; _save(backup, directory.name, journal)
        order = list(reversed(range(len(journal['entries']) - 1))) + [len(journal['entries']) - 1]
        for index in order:
            entry = journal['entries'][index]
            if entry['restore'] == 'done': continue
            current = store.read(entry['path'])
            entry['restore'] = 'writing'; _save(backup, directory.name, journal)
            if current.fingerprint() != entry['before']:
                if entry['before'] is None:
                    store.remove(entry['path'], current)
                else:
                    data = _blob(backup, directory.name, 'before', index, entry['before'])
                    store.create('.research-framework/bootstrap-stage-' + journal['operation'] + '/restore.bin', data, entry['before']['mode'])
                    stage = '.research-framework/bootstrap-stage-' + journal['operation'] + '/restore.bin'
                    store.publish(stage, entry['path'], current, store.read(stage))
            restored = store.read(entry['path'])
            entry.update(restore='done', restore_token=restored.token)
            _save(backup, directory.name, journal)
            _checkpoint('restored', index)
        for item in reversed(journal['created']):
            store.remove_empty(item['path'], item['identity'])
        journal['status'] = 'ROLLED_BACK'; _save(backup, directory.name, journal)
        return {'status': 'ROLLED_BACK', 'backup_directory': str(directory)}
