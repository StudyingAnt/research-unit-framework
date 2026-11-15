"""Template copying and small, explicit three-way project updates. No migration."""

from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import unified_diff
import json
import os
from pathlib import Path
import re
import sys
import uuid

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'template/tools'))
from project_common import digest, encode, fingerprint, load_json, lock, read, relative, safe_path, write
from _merge import has_markers, merge_text

STATE = '.framework/manifest.json'


def managed_path(path):
    relative(path)
    if path in {'AGENTS.md', 'CLAUDE.md', 'REPORT_TEMPLATE.md', 'coordination/COORDINATION.md',
                'docs/hpc.md', 'docs/figure_style.md'}:
        return path
    if path.split('/')[0] in {'tools', 'templates'} and all(not p.startswith('.') for p in path.split('/')):
        if Path(path).suffix in {'.py', '.md', '.css'}:
            return path
    raise ValueError('Scientific/configuration paths cannot be framework-managed: ' + path)


def release(source=ROOT):
    source = Path(source).absolute()
    manifest = load_json(source, 'template-manifest.json')
    if set(manifest) != {'format', 'version', 'managed'} or manifest['format'] != 2:
        raise ValueError('Expected the template-first baseline manifest (format 2)')
    if not re.fullmatch(r'2\.\d+\.\d+(?:-[a-z0-9.]+)?', manifest['version']):
        raise ValueError('Unsupported baseline version')
    if len(set(manifest['managed'])) != len(manifest['managed']):
        raise ValueError('Duplicate managed path')
    files = {}
    template = safe_path(source, 'template')
    for directory, folders, names in os.walk(template, followlinks=False):
        for name in folders + names:
            path = (Path(directory) / name).relative_to(template).as_posix()
            safe_path(template, path)
        for name in names:
            path = (Path(directory) / name).relative_to(template).as_posix()
            if '__pycache__' in path.split('/') or name.endswith('.pyc'):
                continue
            files[path] = read(template, path)
    for path in manifest['managed']:
        managed_path(path)
        if path not in files:
            raise ValueError('Managed template is missing: ' + path)
    return manifest, files


def state_for(manifest, files):
    return {'format': 2, 'version': manifest['version'],
            'files': {p: fingerprint(files[p]) for p in sorted(manifest['managed'])}}


def create_project(destination, source=ROOT):
    """Create only an absent destination. Leave a failed partial copy for inspection."""
    manifest, files = release(source)
    destination = Path(destination).expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('Destination already exists; choose a new project directory')
    # mkdir without exist_ok refuses a concurrent creator rather than overlaying it.
    destination.mkdir(parents=True)
    for path, snapshot in sorted(files.items()):
        write(destination, path, *snapshot)
    for path in manifest['managed']:
        data, _ = files[path]
        cache = '.framework/base/' + digest(data)
        if read(destination, cache) is None:
            write(destination, cache, data)
    state = state_for(manifest, files)
    write(destination, STATE, encode(state))
    return {'project': str(destination), 'version': manifest['version']}


@dataclass
class Plan:
    project: Path
    source: Path
    state: dict
    next_state: dict
    actions: list
    incoming: dict
    resolutions: dict

    def describe(self):
        rows = []
        for item in self.actions:
            row = {k: v for k, v in item.items() if k not in {'before', 'after'}}
            row.update(before=fingerprint(item['before']), after=fingerprint(item['after']))
            try:
                row['diff'] = ''.join(unified_diff((item['before'][0] if item['before'] else b'').decode().splitlines(True),
                    (item['after'][0] if item['after'] else b'').decode().splitlines(True), fromfile='local', tofile='proposed'))
            except UnicodeError:
                row['diff'] = 'Binary content; see hashes'
            rows.append(row)
        result = {'project': str(self.project), 'from_version': self.state['version'],
                  'to_version': self.next_state['version'], 'actions': rows,
                  'conflicts': [r['path'] for r in rows if r['action'] == 'CONFLICT'],
                  'state_sha256': digest(encode(self.state)), 'next_state_sha256': digest(encode(self.next_state))}
        result['plan_digest'] = digest(encode(result))
        return result


def plan_update(project, source=ROOT, resolutions=None):
    project = Path(project).expanduser().absolute()
    manifest, files = release(source)
    state = load_json(project, STATE)
    if set(state) != {'format', 'version', 'files'} or state['format'] != 2:
        raise ValueError('Only projects created from the new baseline are supported')
    if not isinstance(state['files'], dict) or not re.fullmatch(r'2\.\d+\.\d+(?:-[a-z0-9.]+)?', state['version']):
        raise ValueError('Invalid baseline-2 project state')
    if tuple(map(int, manifest['version'].split('-')[0].split('.'))) < tuple(map(int, state['version'].split('-')[0].split('.'))):
        raise ValueError('Downgrade is not supported; select the intended newer framework')
    incoming = {p: files[p] for p in manifest['managed']}
    resolutions = resolutions or {}
    if set(resolutions) - (set(state['files']) | set(incoming)):
        raise ValueError('Resolution does not name a managed file')
    actions = []
    for path in sorted(set(state['files']) | set(incoming)):
        managed_path(path)
        before = read(project, path)
        info = state['files'].get(path)
        base = None
        if info is not None:
            if set(info) != {'sha256', 'mode'} or not re.fullmatch('[0-9a-f]{64}', info['sha256']):
                raise ValueError('Invalid recorded baseline: ' + path)
            cached = read(project, '.framework/base/' + info['sha256'])
            if cached is None or digest(cached[0]) != info['sha256']:
                raise ValueError('Previous template snapshot is missing/corrupt: ' + path)
            base = cached[0], info['mode']
        new = incoming.get(path)
        after = before
        if new is None and path in files:
            action = 'RELINQUISH'  # It is now a seed/project file; retain existing content.
        elif base is None and before is not None:
            action = 'CONFLICT'  # An unknown local file never becomes owned silently.
        elif before == new:
            action = 'UNCHANGED'
        elif before == base:
            after = new; action = 'DELETE' if new is None else 'ADD' if base is None else 'UPDATE'
        elif new == base:
            action = 'KEEP_LOCAL'
        elif before is None or new is None:
            action = 'CONFLICT'
        else:
            merged = merge_text(base[0], before[0], new[0])
            if merged.content is None or before[1] != base[1] and new[1] != base[1] and before[1] != new[1]:
                action = 'CONFLICT'
            else:
                after = merged.content, before[1] if before[1] != base[1] else new[1]
                action = 'MERGE'
        if path in resolutions:
            if base is None:
                raise ValueError('An unmanaged collision cannot be resolved by adopting it: ' + path)
            if has_markers(resolutions[path]):
                raise ValueError('Resolution contains unresolved conflict markers')
            after = resolutions[path], before[1] if before else new[1] if new else base[1]
            action = 'RESOLVED'
        actions.append({'path': path, 'action': action, 'before': before, 'after': after})
    return Plan(project, Path(source).absolute(), state, state_for(manifest, files), actions, incoming, resolutions)


def apply_update(plan, expected_digest=None):
    description = plan.describe()
    if description['conflicts']:
        raise ValueError('Unresolved conflicts; no project files changed')
    if expected_digest and expected_digest != description['plan_digest']:
        raise ValueError('Plan differs from the reviewed digest')
    with lock(plan.project):
        fresh = plan_update(plan.project, plan.source, plan.resolutions)
        if fresh.describe() != description:
            raise ValueError('Stale plan; inspect a fresh preview')
        changes = [a for a in plan.actions if a['before'] != a['after']]
        if not changes and plan.state == plan.next_state:
            return {'version': plan.state['version'], 'changed': [], 'backup': None}
        name = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8]
        backup = '.framework/backups/' + name
        safe_path(plan.project, backup).mkdir(parents=True, mode=0o700)
        state_before = read(plan.project, STATE)
        write(plan.project, backup + '/previous-manifest.json', state_before[0], 0o600)
        entries = []
        for action in changes:
            before = action['before']
            if before is not None:
                write(plan.project, backup + '/before/' + action['path'], before[0], before[1])
                if read(plan.project, backup + '/before/' + action['path']) != before:
                    raise ValueError('Affected-file backup verification failed: ' + action['path'])
            entries.append({'path': action['path'], 'before': fingerprint(before), 'after': fingerprint(action['after'])})
        write(plan.project, backup + '/changes.json', encode({'plan': description, 'files': entries}), 0o600)
        if read(plan.project, backup + '/previous-manifest.json')[0] != state_before[0]:
            raise ValueError('Backup verification failed')
        # All affected originals have been verified before the first managed write.
        if plan_update(plan.project, plan.source, plan.resolutions).describe() != description:
            raise ValueError('Project/source changed during backup; preview again')
        for action in changes:
            path, before, after = action['path'], action['before'], action['after']
            if after is None:
                if read(plan.project, path) != before:
                    raise ValueError('Local file changed before removal: ' + path)
                safe_path(plan.project, path).unlink()
            else:
                write(plan.project, path, *after, expected=before, replace=before is not None)
        # Immutable snapshot objects leave the old manifest usable after interruption.
        for data, _ in plan.incoming.values():
            cache = '.framework/base/' + digest(data)
            cached = read(plan.project, cache)
            if cached is None:
                write(plan.project, cache, data)
            elif cached[0] != data:
                raise ValueError('Template snapshot collision/corruption')
        write(plan.project, STATE, encode(plan.next_state), expected=state_before, replace=True)
        return {'version': plan.next_state['version'], 'changed': [a['path'] for a in changes],
                'backup': str(plan.project / backup)}
