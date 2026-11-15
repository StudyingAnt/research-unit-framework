"""Human-adopted, tool-neutral scientific records with durable ID reservations."""

from datetime import date
import hashlib
from pathlib import Path
import re
import uuid

from .paths import ValidationError, validate_relative_path, MAX_FILE_BYTES
from .storage import Store
from .updates import encode, decode, read_receipt


PATTERNS = {'W': r'W(?:0[1-9]|[1-9][0-9])', 'A': r'A(?:00[1-9]|0[1-9][0-9]|[1-9][0-9]{2})',
            'S': r'A[0-9]{3}-S(?:0[1-9]|[1-9][0-9])',
            'T': r'A[0-9]{3}-S[0-9]{2}-T(?:0[1-9]|[1-9][0-9])',
            'M': r'M(?:0[1-9]|[1-9][0-9])'}
STATUS = ('PLANNING', 'APPROVED', 'EXECUTING', 'WAITING', 'BLOCKED', 'FAILED', 'COMPLETED')
OUTCOME = ('NOT_EVALUATED', 'SUPPORTED', 'NOT_SUPPORTED', 'INCONCLUSIVE')


def approval(value):
    if type(value) is not dict or set(value) != {'by', 'reference', 'date'}:
        raise ValidationError('Explicit researcher approval requires by, reference and date')
    for key in ('by', 'reference'):
        if type(value[key]) is not str or not value[key].strip() or value[key].strip().lower() in {'todo', 'unknown', 'researcher', 'approved'}:
            raise ValidationError('Approval must identify the actual researcher and approval evidence')
    try: date.fromisoformat(value['date'])
    except (TypeError, ValueError): raise ValidationError('Approval date must be an ISO date')
    return dict(value)


def configuration(store):
    raw = store.read('framework-project.json', 1024 * 1024)
    if raw.data is None: raise ValidationError('Project configuration is missing')
    result = decode(raw.data)
    if result.get('schema_version') != 1 or type(result.get('paths')) is not dict:
        raise ValidationError('Unsupported project configuration')
    paths = result['paths']
    if set(paths) != {'plans', 'reports', 'analyses', 'manuscripts'}:
        raise ValidationError('Project path mappings must name plans/reports/analyses/manuscripts')
    from .paths import validate_path_set
    validate_path_set(paths.values())
    for path in paths.values():
        validate_relative_path(path)
        if path.split('/')[0] in {'.research-framework', 'tools', 'templates'}:
            raise ValidationError('Scientific path maps into framework-owned state')
    result['paths'] = dict(paths)
    return result


def registry_path(store):
    return configuration(store)['paths']['plans'] + '/ID_REGISTRY.json'


def validate_registry(value):
    if (type(value) is not dict or set(value) != {'schema_version', 'revision', 'records'}
            or value['schema_version'] != 1 or type(value['revision']) is not int or value['revision'] < 0
            or type(value['records']) is not list or len(value['records']) > 10000):
        raise ValidationError('Invalid scientific ID registry')
    seen = set()
    for record in value['records']:
        required = {'id', 'kind', 'parent', 'title', 'path', 'links', 'approval', 'state', 'sha256', 'history'}
        if type(record) is not dict or set(record) != required:
            raise ValidationError('Invalid scientific registration fields')
        if record['kind'] not in PATTERNS or not re.fullmatch(PATTERNS[record['kind']], record['id']):
            raise ValidationError('Invalid stable scientific identity')
        if record['id'] in seen: raise ValidationError('Scientific IDs cannot be reused')
        seen.add(record['id']); validate_relative_path(record['path']); approval(record['approval'])
        if record['state'] not in {'pending', 'active', 'retired'} or not re.fullmatch(r'[0-9a-f]{64}', record['sha256']):
            raise ValidationError('Invalid scientific registration state')
        if type(record['links']) is not list or len(set(record['links'])) != len(record['links']):
            raise ValidationError('Invalid scientific associations')
    records = {r['id']: r for r in value['records']}
    for record in records.values():
        kind, parent = record['kind'], record['parent']
        if kind in {'S', 'T'}:
            if parent not in records or records[parent]['kind'] != ('A' if kind == 'S' else 'S') or not record['id'].startswith(parent + '-'):
                raise ValidationError('AST parent registration missing or inconsistent')
        elif parent is not None: raise ValidationError('Workstreams/Aims/manuscripts have independent identity')
        for linked in record['links']:
            if linked not in records or not ({kind, records[linked]['kind']} == {'W', 'A'} or kind == 'M' and records[linked]['kind'] == 'T'):
                raise ValidationError('Unsupported scientific relationship')
    return value


def read_registry(store):
    path = registry_path(store); snapshot = store.read(path, 8 * 1024 * 1024)
    if snapshot.data is None:
        return {'schema_version': 1, 'revision': 0, 'records': []}, snapshot
    return validate_registry(decode(snapshot.data)), snapshot


def _replace(store, path, data, expected):
    """Atomic record write; the scientific operation is separately recoverable."""
    parent = path.rsplit('/', 1)[0] if '/' in path else None
    if parent: store.ensure_dir(parent)
    current = store.read(path)
    if (current.data, current.mode, current.token) != (expected.data, expected.mode, expected.token):
        raise ValidationError('Scientific record changed; review before writing')
    temporary = (parent + '/' if parent else '') + '.record-' + uuid.uuid4().hex
    staged = store.create(temporary, data, expected.mode or '0644')
    return store.publish(temporary, path, current, staged)


def _occupied(store):
    """Inspect only identity-bearing coordination/output locations, never repos/data."""
    found, count = set(), 0
    paths = configuration(store)['paths']
    def visit(path, depth=0):
        nonlocal count
        if depth > 8: raise ValidationError('Identity discovery depth exceeded; review existing records')
        for name in store.names(path):
            count += 1
            if count > 10000: raise ValidationError('Identity discovery bound exceeded')
            candidate = path + '/' + name
            for match in re.finditer(r'(?<![A-Za-z0-9])(?:A[0-9]{3}(?:-S[0-9]{2}(?:-T[0-9]{2})?)?|[WM][0-9]{2})(?![0-9])', name):
                identity = match.group()
                found.add(identity)
                pieces = identity.split('-')
                found.update('-'.join(pieces[:n]) for n in range(1, len(pieces)))
            with store.parent(candidate) as (fd, leaf):
                import os, stat
                info = os.stat(leaf, dir_fd=fd, follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode): visit(candidate, depth + 1)
                elif stat.S_ISLNK(info.st_mode):
                    raise ValidationError('Identity-bearing locations contain a symlink; inspect before allocation')
                elif name.endswith('.md') and path.startswith(paths['plans']):
                    text = store.read(candidate, 1024 * 1024).data.decode('utf-8')
                    found.update(re.findall(r'\bA[0-9]{3}(?:-S[0-9]{2}(?:-T[0-9]{2})?)?\b', text))
                    # Legacy Aim plans may abbreviate local Strategy/Tactic IDs.
                    aim = re.search(r'\bA[0-9]{3}\b', name)
                    if aim:
                        strategies = set(re.findall(r'\bS[0-9]{2}\b', text))
                        tactics = set(re.findall(r'\bT[0-9]{2}\b', text))
                        found.update(aim.group() + '-' + s for s in strategies)
                        found.update(aim.group() + '-' + s + '-' + t for s in strategies for t in tactics)
    for path in paths.values(): visit(path)
    found.update(store.names('.research-framework/record-operations'))
    return found


def _path(config, kind, identity):
    plans = config['paths']['plans']
    return { 'W': plans + '/workstreams/' + identity + '.md', 'A': plans + '/' + identity + '.md',
             'S': plans + '/strategies/' + identity + '.md', 'T': plans + '/units/' + identity + '.md',
             'M': config['paths']['manuscripts'] + '/' + identity + '.md'}[kind]


def _checkpoint(event):
    """Synthetic interruption seam."""


def adopt_record(project, kind, title, body, decision, parent=None, links=(), identity=None):
    decision = approval(decision)
    if kind not in PATTERNS or not title.strip() or not body.strip() or '{{' in body:
        raise ValidationError('Supply a concrete researcher-approved title and record body')
    if kind == 'T' and not all(h in body for h in ('## Question', '## Specifications')):
        raise ValidationError('A Tactic requires its bounded Question and material Specifications')
    if kind == 'M' and not all(h in body for h in ('## Claims', '## Supporting Evidence', '## Contradictory Evidence', '## Limitations', '## Decisions')):
        raise ValidationError('Manuscript records require claims, evidence, contradictions, limitations and decisions')
    with Store(project) as store, store.lock():
        read_receipt(store)
        registry, before = read_registry(store)
        if any(r['state'] == 'pending' for r in registry['records']):
            raise ValidationError('Resume the pending registration under its existing ID first')
        existing = {r['id']: r for r in registry['records']}
        if kind in {'S', 'T'}:
            if parent not in existing or existing[parent]['kind'] != ('A' if kind == 'S' else 'S') or existing[parent]['state'] != 'active':
                raise ValidationError('An active, approved parent record is required')
        elif parent is not None: raise ValidationError('This record has independent identity')
        occupied = _occupied(store) | set(existing)
        prefix = parent + '-' + kind if parent else kind
        width = 3 if kind == 'A' else 2
        if identity is None:
            identity = next((prefix + str(n).zfill(width) for n in range(1, 10 ** width)
                             if prefix + str(n).zfill(width) not in occupied), None)
        if identity is None: raise ValidationError('Identifier capacity exhausted; researcher format decision required')
        if not re.fullmatch(PATTERNS[kind], identity) or identity in occupied or not identity.startswith(prefix):
            raise ValidationError('ID is invalid, reserved, registered or already present on disk')
        config = configuration(store); path = _path(config, kind, identity)
        content = ('# ' + identity + ': ' + title + '\n\n' + body.rstrip() + '\n\n'
                   '## Adoption Record\n\n' + decision['date'] + ': ' + decision['by'] + '; ' + decision['reference'] + '\n').encode()
        if len(content) > MAX_FILE_BYTES: raise ValidationError('Record exceeds size bounds')
        if store.read(path).data is not None: raise ValidationError('Record destination already exists')
        record = {'id': identity, 'kind': kind, 'parent': parent, 'title': title, 'path': path,
                  'links': sorted(set(links)), 'approval': decision, 'state': 'pending',
                  'sha256': hashlib.sha256(content).hexdigest(), 'history': []}
        registry['records'].append(record); registry['revision'] += 1
        validate_registry(registry)
        operation = '.research-framework/record-operations/' + identity
        store.ensure_dir(operation)
        store.create(operation + '/' + record['sha256'] + '.md', content)
        _replace(store, registry_path(store), encode(registry), before)
        _checkpoint('reserved')
        _resume(store, identity)
        return record


def _resume(store, identity):
    registry, before = read_registry(store)
    record = next((r for r in registry['records'] if r['id'] == identity), None)
    if record is None: raise ValidationError('Unknown scientific ID; do not allocate a replacement')
    if record['state'] != 'pending': return record
    content = store.read('.research-framework/record-operations/' + identity + '/' + record['sha256'] + '.md').data
    if content is None or hashlib.sha256(content).hexdigest() != record['sha256']:
        raise ValidationError('Pending scientific record source is unavailable or changed')
    current = store.read(record['path'])
    if current.data is None:
        _replace(store, record['path'], content, current)
    elif current.data != content:
        prior = record['history'][-1].get('previous_sha256') if record['history'] else None
        if prior is None or hashlib.sha256(current.data).hexdigest() != prior:
            raise ValidationError('Pending record destination has local work; preserve it and resolve explicitly')
        _replace(store, record['path'], content, current)
    _checkpoint('published')
    record['state'] = 'active'; registry['revision'] += 1
    _replace(store, registry_path(store), encode(registry), before)
    return record


def resume_record(project, identity):
    with Store(project) as store, store.lock(): return _resume(store, identity)


def revise_record(project, identity, text, decision, expected_sha256):
    decision = approval(decision)
    with Store(project) as store, store.lock():
        registry, before = read_registry(store)
        record = next((r for r in registry['records'] if r['id'] == identity and r['state'] == 'active'), None)
        if record is None or any(r['state'] == 'pending' for r in registry['records']):
            raise ValidationError('Resolve pending records before an approved revision')
        current = store.read(record['path'])
        if current.data is None or hashlib.sha256(current.data).hexdigest() != expected_sha256:
            raise ValidationError('Scientific record changed; review its current contents')
        content = text.encode()
        if not text.strip() or '{{' in text: raise ValidationError('Concrete approved content required')
        operation = '.research-framework/record-operations/' + identity
        store.ensure_dir(operation)
        for data in (current.data, content):
            path = operation + '/' + hashlib.sha256(data).hexdigest() + '.md'
            if store.read(path).data is None: store.create(path, data)
            elif store.read(path).data != data: raise ValidationError('Revision archive mismatch')
        record['history'].append({'previous_sha256': expected_sha256, 'approval': decision})
        record.update(sha256=hashlib.sha256(content).hexdigest(), state='pending', approval=decision)
        registry['revision'] += 1
        _replace(store, registry_path(store), encode(registry), before)
        return _resume(store, identity)


def register_existing(project, kind, identity, path, title, decision, parent=None, links=()):
    """Explicit registration of inspected legacy records; never rewrites their body."""
    decision = approval(decision); validate_relative_path(path)
    if kind not in PATTERNS or not re.fullmatch(PATTERNS[kind], identity):
        raise ValidationError('Invalid existing identity')
    with Store(project) as store, store.lock():
        registry, before = read_registry(store)
        config = configuration(store)
        if not any(path.startswith(prefix + '/') for prefix in config['paths'].values()):
            raise ValidationError('Existing record must lie within configured scientific record locations')
        if any(r['id'] == identity for r in registry['records']): raise ValidationError('Identity already registered')
        content = store.read(path).data
        if content is None: raise ValidationError('Existing scientific record is missing')
        record = {'id': identity, 'kind': kind, 'parent': parent, 'title': title, 'path': path,
                  'links': sorted(set(links)), 'approval': decision, 'state': 'active',
                  'sha256': hashlib.sha256(content).hexdigest(), 'history': [{'registered_existing': True}]}
        registry['records'].append(record); registry['revision'] += 1
        validate_registry(registry)
        _replace(store, registry_path(store), encode(registry), before)
        return record


def set_links(project, identity, links, decision, expected_revision):
    decision = approval(decision)
    with Store(project) as store, store.lock():
        registry, before = read_registry(store)
        if registry['revision'] != expected_revision: raise ValidationError('Registry revision changed')
        record = next((r for r in registry['records'] if r['id'] == identity and r['state'] == 'active'), None)
        if record is None: raise ValidationError('Active scientific record required')
        record['history'].append({'links': record['links'], 'approval': decision})
        record['links'] = sorted(set(links)); registry['revision'] += 1
        validate_registry(registry)
        _replace(store, registry_path(store), encode(registry), before)
        return registry


def retire_record(project, identity, decision, expected_revision):
    decision = approval(decision)
    with Store(project) as store, store.lock():
        registry, before = read_registry(store)
        if registry['revision'] != expected_revision: raise ValidationError('Registry revision changed')
        record = next((r for r in registry['records'] if r['id'] == identity and r['state'] == 'active'), None)
        if record is None: raise ValidationError('Active record required')
        record['state'] = 'retired'; record['history'].append({'retired': decision}); registry['revision'] += 1
        _replace(store, registry_path(store), encode(registry), before)
        return record


def adopt_map(project, text, decision, expected_sha256):
    """An explicit approved program revision, without allocating an AST identity."""
    decision = approval(decision)
    headings = ('## Research Narrative', '### Question', '### Hypothesis', '### Observation',
                '### Inference', '### Alternative', '### Synthesis', '## Workstreams and Aim Associations',
                '## Priorities, Dependencies, and Gaps', '## Dated Decisions and Revisions')
    if any(h not in text for h in headings) or '{{' in text:
        raise ValidationError('Research Map must retain scientific categories, relationships and decisions')
    with Store(project) as store, store.lock():
        config = configuration(store); path = config['paths']['plans'] + '/RESEARCH_MAP.md'
        current = store.read(path)
        digest = hashlib.sha256(current.data).hexdigest() if current.data is not None else None
        if digest != expected_sha256: raise ValidationError('Research Map changed; review the current version')
        operation = uuid.uuid4().hex
        archive = 'coordination/revisions/map-' + operation
        store.ensure_dir(archive)
        if current.data is not None: store.create(archive + '/before.md', current.data, current.mode)
        store.create(archive + '/decision.json', encode({'approval': decision, 'previous_sha256': digest,
            'new_sha256': hashlib.sha256(text.encode()).hexdigest(), 'target': path}))
        _replace(store, path, text.encode(), current)
        return {'path': path, 'revision_record': archive, 'sha256': hashlib.sha256(text.encode()).hexdigest()}
