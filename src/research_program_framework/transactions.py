"""Journaled updates and guarded recovery for existing framework installations."""

from dataclasses import dataclass
import hashlib
import re
from typing import Optional
import uuid

from .paths import ValidationError, validate_path_set, MAX_FILE_BYTES
from .storage import Store, Snapshot
from .updates import (UpdatePlan, RECEIPT, MAX_METADATA, ID_PATTERN, encode, decode,
                      manifest_dict, read_receipt, validate_receipt, plan_update, project_owners)
from .manifests import validate_release_manifest, _object, _file


FINAL = {'COMMITTED', 'ROLLED_BACK', 'ABORTED'}
ACTIVE = {'PREPARING', 'APPLYING', 'ROLLING_BACK'}


class TransactionError(ValidationError):
    def __init__(self, operation_id, message):
        self.operation_id = operation_id
        super().__init__(f'{message}; inspect operation {operation_id}')


def _checkpoint(event, index=None):
    """Internal failure-injection boundary used by deterministic tests."""


def _operation(value):
    if type(value) is not str or not re.fullmatch(ID_PATTERN, value):
        raise ValidationError('Invalid operation identifier')
    return value


def _directory(operation):
    return '.research-framework/transactions/' + _operation(operation)


def _journal_path(operation):
    return _directory(operation) + '/journal.json'


def _blob(operation, side, index):
    if side == 'before':
        return f'.research-framework/backups/{_operation(operation)}/{index}.bin'
    if side not in {'after', 'stage', 'restore'}:
        raise ValidationError('Invalid storage role')
    return f'{_directory(operation)}/{side}/{index}.bin'


def _signed(journal):
    clean = {key: value for key, value in journal.items() if key != 'checksum'}
    return {**clean, 'checksum': hashlib.sha256(encode(clean)).hexdigest()}


def _save(store, journal):
    path = _journal_path(journal['operation_id'])
    store.atomic(path, encode(_signed(journal)), store.read(path, MAX_METADATA))


def _fingerprint(value):
    if value is not None:
        _file({'path': 'record', **_object(value, {'size', 'sha256', 'mode'})}, False)


def _load(store, operation):
    try:
        return _load_checked(store, operation)
    except (KeyError, TypeError, IndexError, AttributeError) as exc:
        raise ValidationError('Malformed transaction journal; manual inspection required') from exc


def _load_checked(store, operation):
    snapshot = store.read(_journal_path(operation), MAX_METADATA)
    if snapshot.data is None:
        raise ValidationError('Missing operation journal; manual inspection required')
    journal = decode(snapshot.data)
    _object(journal, {'schema_version', 'operation_id', 'project_id', 'root_identity', 'plan_digest',
                      'before_receipt', 'after_release', 'status', 'entries', 'created_dirs', 'checksum'})
    if (type(journal['schema_version']) is not int or journal['schema_version'] != 1
            or journal['operation_id'] != operation or journal['status'] not in FINAL | ACTIVE
            or journal['checksum'] != _signed(journal)['checksum']
            or type(journal['plan_digest']) is not str or not re.fullmatch('[0-9a-f]{64}', journal['plan_digest'])
            or tuple(journal['root_identity']) != store.identity):
        raise ValidationError('Corrupt, unsupported, or displaced transaction journal')
    before = validate_receipt(journal['before_receipt'])
    after = validate_release_manifest(journal['after_release'])
    if journal['project_id'] != before['project_id']:
        raise ValidationError('Journal project identity mismatch')
    old = validate_release_manifest(before['release'])
    old_roles = {item.path: item.ownership for item in old.files}
    new_roles = {item.path: item.ownership for item in after.files}
    allowed = {p for p in old_roles.keys() | new_roles.keys()
               if old_roles.get(p, 'A') == 'A' and new_roles.get(p, 'A') == 'A'
               and p not in project_owners(before)}
    entries = journal['entries']
    if type(entries) is not list or not entries or entries[-1]['path'] != RECEIPT:
        raise ValidationError('Invalid transaction target list')
    validate_path_set(item['path'] for item in entries)
    for index, entry in enumerate(entries):
        _object(entry, {'path', 'before', 'after', 'before_token', 'after_token', 'before_parents',
                        'after_parents', 'progress', 'restore', 'restore_token'})
        if entry['path'] not in allowed and not (index == len(entries) - 1 and entry['path'] == RECEIPT):
            raise ValidationError('Journal attempts to modify an unregistered/project-owned path')
        _fingerprint(entry['before']); _fingerprint(entry['after'])
        if entry['progress'] not in {'pending', 'writing', 'done'} or entry['restore'] not in {'pending', 'writing', 'done'}:
            raise ValidationError('Invalid per-file transaction state')
        for field in ['before_token', 'after_token', 'restore_token']:
            token = entry[field]
            if token is not None and (type(token) not in (list, tuple) or len(token) != 7
                    or any(type(value) is not int for value in token)):
                raise ValidationError('Invalid recorded file identity')
        prefixes = ['', *('/'.join(entry['path'].split('/')[:n])
                          for n in range(1, len(entry['path'].split('/'))))]
        for field in ['before_parents', 'after_parents']:
            parents = entry[field]
            if parents is None and field == 'after_parents':
                continue
            if type(parents) not in (list, tuple) or [pair[0] for pair in parents] != prefixes:
                raise ValidationError('Invalid recorded parent chain')
            for name, token in parents:
                if token is not None and (type(token) not in (list, tuple) or len(token) != 3
                        or any(type(value) is not int for value in token)):
                    raise ValidationError('Invalid directory identity')
    if type(journal['created_dirs']) is not list:
        raise ValidationError('Invalid created-directory record')
    ancestors = {p.rsplit('/', n)[0] for p in (e['path'] for e in entries[:-1])
                 for n in range(1, len(p.split('/')))}
    for item in journal['created_dirs']:
        _object(item, {'path', 'identity'})
        if item['path'] not in ancestors:
            raise ValidationError('Journal directory is not a target ancestor')
        token = item['identity']
        if token is not None and (type(token) not in (list, tuple) or len(token) != 3
                or any(type(value) is not int for value in token)):
            raise ValidationError('Invalid created-directory identity')
    if len({item['path'] for item in journal['created_dirs']}) != len(journal['created_dirs']):
        raise ValidationError('Duplicate created-directory records')
    if journal['status'] not in {'PREPARING', 'ABORTED'}:
        index = len(entries) - 1
        old_receipt = validate_receipt(decode(_checked_blob(store, operation, 'before', index, entries[-1]['before'])))
        next_receipt = validate_receipt(decode(_checked_blob(store, operation, 'after', index, entries[-1]['after'])))
        if (old_receipt != before or next_receipt['project_id'] != before['project_id']
                or next_receipt['release'] != journal['after_release']
                or next_receipt['generation'] != before['generation'] + 1
                or next_receipt['last_operation'] != operation):
            raise ValidationError('Receipt lineage disagrees with operation journal')
    return journal, snapshot


def pending_operations(store):
    pending = []
    for name in store.names('.research-framework/transactions'):
        if re.fullmatch(ID_PATTERN, name):
            journal, _ = _load(store, name)
            if journal['status'] not in FINAL:
                pending.append(name)
    return tuple(pending)


def _matches(snapshot, fingerprint):
    return snapshot.fingerprint() == fingerprint


def _token_equal(token, recorded):
    return token == (None if recorded is None else tuple(recorded))


def _known_restoration(store, journal, entry, current):
    """Accept a new inode only when a completed child rollback recorded it."""
    for operation in store.names('.research-framework/transactions'):
        if not re.fullmatch(ID_PATTERN, operation) or operation == journal['operation_id']:
            continue
        later, _ = _load(store, operation)
        if (later['status'] != 'ROLLED_BACK'
                or later['before_receipt']['last_operation'] != journal['operation_id']
                or later['project_id'] != journal['project_id']
                or later['before_receipt']['generation'] != journal['before_receipt']['generation'] + 1):
            continue
        for restored in later['entries']:
            if (restored['path'] == entry['path'] and restored['restore'] == 'done'
                    and restored['before'] == entry['after']
                    and _token_equal(current.token, restored['restore_token'])):
                return True
    return False


def _checked_blob(store, operation, side, index, expected):
    snapshot = store.read(_blob(operation, side, index))
    if expected is None:
        return None
    if snapshot.data is None or snapshot.fingerprint() != {**expected, 'mode': '0644'}:
        raise ValidationError('Missing or corrupt verified transaction backup/stage')
    return snapshot.data


def _with_parents(store, path, before, created):
    parents = store.parents(path)
    old = dict(before.parents)
    made = {item['path']: item['identity'] for item in created}
    for name, token in parents:
        original = old.get(name)
        if original is not None and original != token:
            raise ValidationError('Target parent identity changed')
        if original is None and name and (name not in made or made[name] is None or tuple(made[name]) != token):
            raise ValidationError('Unverified target-parent creation')
    return Snapshot(before.data, before.mode, before.token, parents)


def _publish_content(store, operation, index, path, content, mode, expected, stage='stage'):
    if content is None:
        if expected.data is None:
            return expected
        return store.remove(path, expected)
    staged = _blob(operation, stage, index)
    # A previous interrupted recovery may have left an identical staged file.
    previous = store.read(staged)
    if previous.data is None:
        previous = store.create(staged, content, mode)
    elif previous.data != content or previous.mode != mode:
        raise ValidationError('Unexpected existing stage; preserve for inspection')
    return store.publish(staged, path, expected, previous)


def apply_update(plan):
    """Apply exactly a fresh conflict-free plan; preserve all backup/audit records."""
    if not isinstance(plan, UpdatePlan) or plan.conflicts:
        raise ValidationError('A conflict-free reviewed update plan is required')
    with Store(plan.project) as store, store.lock():
        fresh = plan_update(plan.project, plan.payload, plan.release, dict(plan.resolutions))
        if fresh != plan:
            raise ValidationError('Stale or modified update plan; generate and review a fresh plan')
        receipt, _ = read_receipt(store)
        changed = [action for action in plan.actions if action.changes_file]
        same_release = receipt['release'] == manifest_dict(plan.release)
        if not changed and same_release:
            return OperationResult(None, 'NO_CHANGE')
        operation = uuid.uuid4().hex
        installed = {action.path: None if action.content is None else {
            'size': len(action.content), 'sha256': hashlib.sha256(action.content).hexdigest(), 'mode': action.mode}
            for action in plan.actions if any(item.path == action.path and item.ownership == 'A'
                                             for item in plan.release.files)}
        next_receipt = {**receipt, 'generation': receipt['generation'] + 1,
                        'release': manifest_dict(plan.release), 'installed': installed, 'last_operation': operation}
        next_receipt['project_owned'] = {**project_owners(receipt), **{
            item.path: item.project_owner for item in plan.release.files if item.ownership == 'D'}}
        validate_receipt(next_receipt)
        after_receipt = encode(next_receipt)
        targets = [(a.path, a.before, a.content, a.mode) for a in changed]
        targets.append((RECEIPT, plan.receipt, after_receipt, '0644'))
        journal = {'schema_version': 1, 'operation_id': operation, 'project_id': receipt['project_id'],
                   'root_identity': list(store.identity), 'plan_digest': plan.digest,
                   'before_receipt': receipt, 'after_release': manifest_dict(plan.release),
                   'status': 'PREPARING', 'created_dirs': [], 'entries': []}
        for path, before, data, mode in targets:
            after = None if data is None else {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'mode': mode}
            journal['entries'].append({'path': path, 'before': before.fingerprint(), 'after': after,
                'before_token': before.token, 'after_token': None, 'before_parents': before.parents,
                'after_parents': None, 'progress': 'pending', 'restore': 'pending', 'restore_token': None})
        if len(encode(_signed(journal))) > MAX_METADATA:
            raise ValidationError('Transaction journal exceeds metadata bounds')
        try:
            for path in ['.research-framework/transactions', '.research-framework/backups',
                         _directory(operation), f'.research-framework/backups/{operation}',
                         *(_directory(operation) + '/' + side for side in ['after', 'stage', 'restore'])]:
                store.ensure_dir(path)
            _save(store, journal)
            for index, (path, before, data, mode) in enumerate(targets):
                store.check(path, before)
                if before.data is not None:
                    store.create(_blob(operation, 'before', index), before.data)
                    _checked_blob(store, operation, 'before', index, before.fingerprint())
                if data is not None:
                    store.create(_blob(operation, 'after', index), data)
                    _checked_blob(store, operation, 'after', index, journal['entries'][index]['after'])
            # Retain new upstream bytes separately from locally merged results.
            for item in plan.release.files:
                if item.ownership == 'A':
                    data = dict(plan.source_files)[item.path].data
                    path = '.research-framework/baselines/' + item.sha256
                    existing = store.read(path)
                    if existing.data is None:
                        store.create(path, data)
                    elif existing.data != data or existing.mode != '0644':
                        raise ValidationError('Corrupt existing content-addressed baseline')
            _checkpoint('prepared')
            for index, entry in enumerate(journal['entries']):
                if entry['before'] is not None:
                    _checked_blob(store, operation, 'before', index, entry['before'])
                if entry['after'] is not None:
                    _checked_blob(store, operation, 'after', index, entry['after'])
            journal['status'] = 'APPLYING'
            _save(store, journal)
            def created(path, token):
                found = next((item for item in journal['created_dirs'] if item['path'] == path), None)
                if found is None:
                    journal['created_dirs'].append({'path': path, 'identity': token})
                else:
                    found['identity'] = token
                _save(store, journal)
            for index, (path, before, data, mode) in enumerate(targets):
                _checkpoint('before_write', index)
                if data is not None and '/' in path:
                    store.ensure_dir(path.rsplit('/', 1)[0], created)
                expected = _with_parents(store, path, before, journal['created_dirs'])
                store.check(path, expected)
                entry = journal['entries'][index]
                entry['progress'] = 'writing'
                _save(store, journal)
                if entry['before'] is not None:
                    _checked_blob(store, operation, 'before', index, entry['before'])
                current = _publish_content(store, operation, index, path, data, mode, expected)
                _checkpoint('after_write', index)
                if not _matches(current, entry['after']):
                    raise ValidationError('Post-write content verification failed')
                entry['after_token'], entry['after_parents'], entry['progress'] = current.token, current.parents, 'done'
                _save(store, journal)
            # Recheck all results, including changes to earlier files.
            for entry in journal['entries']:
                current = store.read(entry['path'], MAX_METADATA if entry['path'] == RECEIPT else MAX_FILE_BYTES)
                if not _matches(current, entry['after']) or not _token_equal(current.token, entry['after_token']):
                    raise ValidationError('Post-write external modification detected')
            journal['status'] = 'COMMITTED'
            _save(store, journal)
            _checkpoint('committed')
            return OperationResult(operation, 'COMMITTED')
        except Exception as exc:
            try:
                if store.read(_journal_path(operation), MAX_METADATA).data is not None:
                    _recover_locked(store, operation, unfinished_only=True)
            except Exception as recovery_error:
                raise TransactionError(operation, f'Update failed; guarded recovery refused: {recovery_error}') from exc
            raise TransactionError(operation, 'Update failed; recovery attempted without overwriting later edits') from exc


@dataclass(frozen=True)
class OperationResult:
    operation_id: Optional[str]
    status: str


@dataclass(frozen=True)
class RecoveryPlan:
    project: str
    operation_id: str
    journal: Snapshot
    targets: tuple
    mode: str

    def describe(self):
        return {'project': self.project, 'operation_id': self.operation_id, 'mode': self.mode,
                'targets': [{'path': path, 'current': snapshot.fingerprint()}
                            for path, snapshot in self.targets]}


def _recovery_plan(store, operation, unfinished_only):
    journal, journal_snapshot = _load(store, operation)
    if journal['status'] in {'ABORTED', 'ROLLED_BACK'}:
        return RecoveryPlan(str(store.root), operation, journal_snapshot, (), 'NO_CHANGE')
    if unfinished_only and journal['status'] == 'COMMITTED':
        raise ValidationError('Operation committed; request an explicit rollback instead')
    receipt, _ = read_receipt(store)
    if receipt['project_id'] != journal['project_id']:
        raise ValidationError('Recovery project mismatch')
    if journal['status'] == 'COMMITTED' and receipt['last_operation'] != operation:
        raise ValidationError('A later operation exists; rollback the current head first')
    targets = []
    for index, entry in enumerate(journal['entries']):
        current = store.read(entry['path'], MAX_METADATA if entry['path'] == RECEIPT else MAX_FILE_BYTES)
        before, after = entry['before'], entry['after']
        if entry['restore'] == 'done':
            valid = _matches(current, before) and _token_equal(current.token, entry['restore_token'])
        elif entry['restore'] == 'writing':
            valid = _matches(current, before) or (_matches(current, after) and
                     (entry['after_token'] is None or _token_equal(current.token, entry['after_token'])))
        elif entry['progress'] == 'pending':
            valid = _matches(current, before) and _token_equal(current.token, entry['before_token'])
        elif entry['progress'] == 'done':
            valid = _matches(current, after) and (_token_equal(current.token, entry['after_token'])
                or journal['status'] == 'COMMITTED' and _known_restoration(store, journal, entry, current))
        else:
            valid = (_matches(current, before) and _token_equal(current.token, entry['before_token'])
                     or _matches(current, after))
        if not valid:
            raise ValidationError(f'Rollback would overwrite later local modifications: {entry["path"]}')
        if before is not None and journal['status'] != 'PREPARING':
            _checked_blob(store, operation, 'before', index, before)
        # Require the approved parent identities, including any journaled dirs.
        old_parents = {p: token for p, token in entry['before_parents']}
        created = {item['path']: item['identity'] for item in journal['created_dirs']}
        for path, token in current.parents:
            expected = old_parents.get(path) or created.get(path)
            if expected is not None and token != tuple(expected):
                raise ValidationError('Recovery parent identity changed')
        targets.append((entry['path'], current))
    return RecoveryPlan(str(store.root), operation, journal_snapshot, tuple(targets),
                        'ABORT' if journal['status'] == 'PREPARING' else 'ROLLBACK')


def plan_rollback(project, operation):
    with Store(project) as store:
        return _recovery_plan(store, _operation(operation), False)


def plan_recovery(project, operation):
    with Store(project) as store:
        return _recovery_plan(store, _operation(operation), True)


def _recover_locked(store, operation, unfinished_only):
    plan = _recovery_plan(store, operation, unfinished_only)
    if plan.mode == 'NO_CHANGE':
        return OperationResult(operation, 'NO_CHANGE')
    journal, _ = _load(store, operation)
    if plan.mode == 'ABORT':
        journal['status'] = 'ABORTED'
        _save(store, journal)
        return OperationResult(operation, 'ABORTED')
    journal['status'] = 'ROLLING_BACK'
    _save(store, journal)
    targets = dict(plan.targets)
    # Restore receipt last, just as it was finalized last on forward apply.
    order = list(reversed(range(len(journal['entries']) - 1))) + [len(journal['entries']) - 1]
    for index in order:
        entry = journal['entries'][index]
        if entry['restore'] == 'done' or entry['progress'] == 'pending':
            continue
        path = entry['path']
        _checkpoint('before_restore', index)
        expected = targets[path]
        store.check(path, expected)
        entry['restore'] = 'writing'
        _save(store, journal)
        data = _checked_blob(store, operation, 'before', index, entry['before'])
        mode = entry['before']['mode'] if entry['before'] else None
        current = _publish_content(store, operation, index, path, data, mode, expected, 'restore')
        _checkpoint('after_restore', index)
        entry['restore_token'], entry['restore'] = current.token, 'done'
        _save(store, journal)
    for item in reversed(journal['created_dirs']):
        store.remove_empty(item['path'], item['identity'])
    journal['status'] = 'ROLLED_BACK'
    _save(store, journal)
    return OperationResult(operation, 'ROLLED_BACK')


def apply_rollback(plan):
    if not isinstance(plan, RecoveryPlan):
        raise ValidationError('A reviewed rollback/recovery plan is required')
    with Store(plan.project) as store, store.lock():
        fresh = _recovery_plan(store, plan.operation_id, plan.mode == 'ABORT')
        if fresh != plan:
            raise ValidationError('Stale recovery plan; inspect current state again')
        return _recover_locked(store, plan.operation_id, unfinished_only=False)
