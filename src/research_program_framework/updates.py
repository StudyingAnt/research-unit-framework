"""Read-only update plans for existing registered framework installations."""

from dataclasses import asdict, dataclass, is_dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Optional

from .manifests import (ReleaseManifest, _object, _unique_object, _constant,
                        validate_release_manifest, verify_release, _file)
from .merge import merge_text, diff_text, has_markers
from .paths import ValidationError, MAX_FILE_BYTES, MAX_TOTAL_BYTES, validate_path_set
from .storage import Store, Snapshot


RECEIPT = '.research-framework/installation.json'
MAX_METADATA = 16 * 1024 * 1024
ID_PATTERN = r'[0-9a-f]{32}'


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode()


def decode(value):
    try:
        return json.loads(value.decode('utf-8'), object_pairs_hook=_unique_object, parse_constant=_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValidationError('Invalid framework state JSON') from exc


def manifest_dict(value):
    result = asdict(value)
    result['files'] = list(result['files'])
    for item in result['files']:
        if item['project_owner'] is None:
            del item['project_owner']
    return result


def validate_receipt(value):
    data = _object(value, {'schema_version', 'kind', 'project_id', 'generation',
                           'release', 'installed', 'last_operation'}, {'project_owned'})
    if (type(data['schema_version']) is not int or data['schema_version'] != 1
            or data['kind'] != 'framework_installation'
            or type(data['project_id']) is not str or not re.fullmatch(ID_PATTERN, data['project_id'])
            or type(data['generation']) is not int or data['generation'] < 0
            or data['last_operation'] is not None and (type(data['last_operation']) is not str
                or not re.fullmatch(ID_PATTERN, data['last_operation']))):
        raise ValidationError('Unsupported or corrupt installation receipt')
    release = validate_release_manifest(data['release'])
    managed = {item.path for item in release.files if item.ownership == 'A'}
    if type(data['installed']) is not dict or set(data['installed']) != managed:
        raise ValidationError('Installation file tracking does not match its release')
    for path, fingerprint in data['installed'].items():
        if fingerprint is not None:
            _file({'path': path, **_object(fingerprint, {'size', 'mode', 'sha256'})}, False)
    protected = data.get('project_owned', {})
    if type(protected) is not dict or any(owner not in ('B', 'C') for owner in protected.values()):
        raise ValidationError('Invalid persistent project ownership registry')
    validate_path_set(protected)
    for item in release.files:
        if item.path in protected and (item.ownership != 'D' or item.project_owner != protected[item.path]):
            raise ValidationError('Release contradicts persistent project ownership')
    return data


def project_owners(receipt):
    owners = {item.path: item.project_owner for item in validate_release_manifest(receipt['release']).files
              if item.ownership == 'D'}
    owners.update(receipt.get('project_owned', {}))
    return owners


def read_receipt(store):
    snapshot = store.read(RECEIPT, MAX_METADATA)
    if snapshot.data is None:
        raise ValidationError('Registered installation required; initialization and v0.5 migration are not implemented')
    return validate_receipt(decode(snapshot.data)), snapshot


def _digest_value(value):
    if is_dataclass(value):
        return _digest_value(asdict(value))
    if isinstance(value, bytes):
        return {'size': len(value), 'sha256': hashlib.sha256(value).hexdigest()}
    if isinstance(value, dict):
        return {key: _digest_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_digest_value(item) for item in value]
    return value


@dataclass(frozen=True)
class Action:
    path: str
    disposition: str
    reason: str
    before: Optional[Snapshot]
    content: Optional[bytes]
    mode: Optional[str]

    @property
    def changes_file(self):
        return self.before is not None and (self.before.data, self.before.mode) != (self.content, self.mode)


@dataclass(frozen=True)
class UpdatePlan:
    project: str
    payload: str
    root_identity: tuple
    receipt: Snapshot
    release: ReleaseManifest
    source_files: tuple
    actions: tuple[Action, ...]
    resolutions: tuple

    @property
    def digest(self):
        return hashlib.sha256(encode(_digest_value(self))).hexdigest()

    @property
    def conflicts(self):
        return tuple(item.path for item in self.actions if item.disposition == 'CONFLICT')

    def describe(self):
        incoming = dict(self.source_files)
        return {'plan_digest': self.digest, 'project': self.project,
                'from_receipt_sha256': hashlib.sha256(self.receipt.data).hexdigest(),
                'to_version': self.release.framework_version, 'conflicts': list(self.conflicts),
                'actions': [{'path': item.path, 'action': item.disposition, 'reason': item.reason,
                             'before': item.before.fingerprint() if item.before else None,
                             'after': None if item.content is None else {
                                 'size': len(item.content), 'sha256': hashlib.sha256(item.content).hexdigest(),
                                 'mode': item.mode},
                             'diff': diff_text(item.before.data, item.content)
                                     if item.before is not None and item.changes_file else '',
                             'upstream_diff': diff_text(item.before.data, incoming[item.path].data)
                                     if item.before is not None and item.path in incoming else ''}
                            for item in self.actions]}


def _compare(path, before, base, old_mode, incoming, new_mode):
    local = before.data
    if incoming is None:
        if local is None:
            return 'PRESERVE_DELETE', 'Already absent', None, None
        if (local, before.mode) == (base, old_mode):
            return 'REMOVE', 'Explicit retirement of unmodified managed file', None, None
        return 'CONFLICT', 'Upstream removed a locally modified file', local, before.mode
    if base is None:
        if local is not None:
            return 'CONFLICT', 'Unmanaged destination collision', local, before.mode
        return 'ADD', 'New managed file', incoming, new_mode
    if local is None:
        if (incoming, new_mode) == (base, old_mode):
            return 'PRESERVE_DELETE', 'Keep the local deletion', None, None
        return 'CONFLICT', 'Upstream changed a locally deleted file', None, None
    merged = merge_text(base, local, incoming)
    mode = (new_mode if before.mode == old_mode else before.mode
            if new_mode == old_mode or new_mode == before.mode else None)
    if merged.content is None or mode is None:
        return 'CONFLICT', merged.reason, local, before.mode
    result = (merged.content, mode)
    if result == (local, before.mode):
        return ('KEEP_LOCAL' if result != (incoming, new_mode) else 'UNCHANGED',
                'Preserve local content or already current', *result)
    return ('UPDATE' if (local, before.mode) == (base, old_mode) else 'MERGE', merged.reason, *result)


def plan_update(project, payload, release, resolutions=None):
    """Plan entirely in memory. Explicit resolution bytes or None (keep local).

    Resolutions apply only to already managed paths, never unmanaged collisions,
    seeds, or ownership changes. No state is repaired, created, or initialized.
    """
    from .transactions import pending_operations
    if not isinstance(release, ReleaseManifest):
        raise ValidationError('A Phase 2 release manifest is required')
    release = validate_release_manifest(manifest_dict(release))
    verify_release(payload, release)
    resolutions = dict(resolutions or {})
    if any(value is not None and (type(value) is not bytes or len(value) > MAX_FILE_BYTES)
           for value in resolutions.values()):
        raise ValidationError('Resolutions must be explicit bytes or None to keep local')
    validate_path_set(resolutions)
    with Store(project) as store, Store(payload) as source:
        receipt, receipt_snapshot = read_receipt(store)
        if pending_operations(store):
            raise ValidationError('An interrupted framework operation requires recovery first')
        old = validate_release_manifest(receipt['release'])
        if old.specification_version != release.specification_version:
            raise ValidationError('Specification-version changes require a separate compatibility decision')
        old_files, new_files = {i.path: i for i in old.files}, {i.path: i for i in release.files}
        protected = project_owners(receipt)
        validate_path_set(sorted(set(old_files) | set(new_files)))
        incoming = {item.path: source.read(item.path) for item in release.files}
        bases, total = {}, 0
        for item in old.files:
            if item.ownership == 'A':
                base = store.read('.research-framework/baselines/' + item.sha256)
                if base.data is None or base.fingerprint() != {'size': item.size, 'sha256': item.sha256, 'mode': '0644'}:
                    raise ValidationError('Missing or corrupt exact upstream baseline')
                bases[item.path] = base.data
                total += len(base.data)
        if total > MAX_TOTAL_BYTES:
            raise ValidationError('Installed baseline exceeds validation bounds')
        actions, consumed, local_total, planned_total = [], set(), 0, 0
        for path in sorted(set(old_files) | set(new_files)):
            previous, next_file = old_files.get(path), new_files.get(path)
            if (path in protected and next_file and (next_file.ownership != 'D'
                    or next_file.project_owner != protected[path])
                    or previous and next_file and (previous.ownership, previous.project_owner)
                    != (next_file.ownership, next_file.project_owner)):
                actions.append(Action(path, 'CONFLICT', 'Ownership change requires separate reviewed adoption', None, None, None))
                continue
            if previous and previous.ownership == 'D' or next_file and next_file.ownership == 'D':
                actions.append(Action(path, 'SKIP_SEED', 'Initialization-only; preserve project ownership', None, None, None))
                continue
            before = store.read(path)
            local_total += len(before.data or b'')
            if local_total > MAX_TOTAL_BYTES:
                raise ValidationError('Managed local content exceeds validation bounds')
            data = incoming[path].data if next_file else None
            disposition, reason, result, mode = _compare(path, before, bases.get(path),
                previous.mode if previous else None, data, next_file.mode if next_file else None)
            if path in resolutions:
                if previous is None or previous.ownership != 'A':
                    raise ValidationError('Cannot resolve an unmanaged destination through update')
                consumed.add(path)
                value = resolutions[path]
                if value is not None and has_markers(value):
                    raise ValidationError('Resolution contains unresolved conflict markers')
                disposition, reason = 'KEEP_LOCAL' if value is None else 'RESOLVED', 'Explicit reviewed resolution'
                result = before.data if value is None else value
                mode = (before.mode or (next_file or previous).mode) if result is not None else None
            planned_total += len(result or b'')
            if planned_total > MAX_TOTAL_BYTES:
                raise ValidationError('Planned managed content exceeds validation bounds')
            actions.append(Action(path, disposition, reason, before, result, mode))
        if consumed != set(resolutions):
            raise ValidationError('Resolution targets a seed, ownership change, or unknown path')
        if store.read(RECEIPT, MAX_METADATA) != receipt_snapshot or pending_operations(store):
            raise ValidationError('Installation changed during planning')
        verify_release(payload, release)
        return UpdatePlan(str(store.root), str(source.root), store.identity, receipt_snapshot, release,
                          tuple(sorted(incoming.items())), tuple(actions), tuple(sorted(resolutions.items())))
