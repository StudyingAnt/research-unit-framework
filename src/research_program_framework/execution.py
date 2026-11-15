"""Provenance, optional execution instances, and durable human-operated handoffs."""

from datetime import datetime
import hashlib
import re
import shlex

from .paths import ValidationError, validate_relative_path, read_payload_file
from .records import configuration, read_registry, approval, _replace, STATUS
from .storage import Store
from .updates import encode, decode


VERIFICATION = ('planned', 'source_default', 'reconstructed', 'verified_effective', 'unknown')


def validate_provenance(item):
    fields = {'category', 'verification', 'reference', 'description', 'producing_revision', 'available_revision', 'dirty_source_hashes'}
    if type(item) is not dict or set(item) != fields or item['verification'] not in VERIFICATION:
        raise ValidationError('Provenance must distinguish planned/default/reconstructed/effective/unknown')
    if item['category'] not in {'protocol', 'sample', 'acquisition', 'computation', 'environment', 'input', 'output', 'interpretation', 'approval'}:
        raise ValidationError('Unsupported provenance category')
    if any(type(item[k]) is not str or not item[k].strip() for k in ('reference', 'description')):
        raise ValidationError('Provenance requires an explicit primary-system/source reference and description')
    for key in ('producing_revision', 'available_revision'):
        if item[key] is not None and (type(item[key]) is not str or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', item[key])):
            raise ValidationError('Source revisions must be verified hashes or explicitly null')
    if item['verification'] in {'unknown', 'planned', 'source_default', 'reconstructed'} and item['producing_revision'] is not None:
        raise ValidationError('Unverified history cannot assert a producing revision')
    if type(item['dirty_source_hashes']) is not dict: raise ValidationError('Dirty-source hashes must be a mapping')
    for path, digest in item['dirty_source_hashes'].items():
        validate_relative_path(path)
        if not re.fullmatch(r'[0-9a-f]{64}', digest): raise ValidationError('Dirty-source hash must be SHA-256')
    return item


def _time(value):
    if value is None: return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None: raise ValueError()
    except (AttributeError, TypeError, ValueError): raise ValidationError('Execution timestamps require timezone-aware ISO values or null')
    return parsed


def validate_run(value):
    fields = {'schema_version', 'unit_id', 'run_id', 'status', 'performer', 'started_at', 'completed_at',
              'command', 'external_id', 'provenance', 'outputs', 'validation'}
    if type(value) is not dict or set(value) != fields or type(value['schema_version']) is not int or value['schema_version'] != 1:
        raise ValidationError('Invalid optional Run record')
    if not re.fullmatch(r'A[0-9]{3}-S[0-9]{2}-T[0-9]{2}', value['unit_id']) or not re.fullmatch(r'R(?:00[1-9]|0[1-9][0-9]|[1-9][0-9]{2})', value['run_id']):
        raise ValidationError('Run identity must be nested under its Tactic')
    if value['status'] not in STATUS or not isinstance(value['performer'], str) or not value['performer'].strip():
        raise ValidationError('Execution status and actual performer are required')
    start, end = _time(value['started_at']), _time(value['completed_at'])
    if start and end and end < start: raise ValidationError('Execution ends before it starts')
    if value['status'] == 'COMPLETED' and (start is None or end is None):
        raise ValidationError('Completion requires actual start/end evidence')
    for key in ('command', 'external_id'):
        if value[key] is not None and (type(value[key]) is not str or not value[key].strip()): raise ValidationError('Unknown execution identity/command must be null')
    if type(value['provenance']) is not list or type(value['outputs']) is not list: raise ValidationError('Invalid Run provenance/outputs')
    for item in value['provenance']: validate_provenance(item)
    for item in value['outputs']:
        if type(item) is not dict or set(item) != {'reference', 'verification', 'sha256'} or item['verification'] not in VERIFICATION or not item['reference']:
            raise ValidationError('Invalid Run output evidence')
        if item['sha256'] is not None and not re.fullmatch(r'[0-9a-f]{64}', item['sha256']): raise ValidationError('Invalid output checksum')
    checks = value['validation']
    if type(checks) is not dict or set(checks) != {'expected', 'received', 'checks', 'missing'} or any(type(v) is not list for v in checks.values()):
        raise ValidationError('Execution validation must distinguish expected, received, checked and missing evidence')
    if any(type(item) is not str or not item.strip() for items in checks.values() for item in items):
        raise ValidationError('Execution validation entries must name actual evidence/checks')
    if value['status'] == 'COMPLETED' and (checks['missing'] or not checks['checks'] or not set(checks['expected']) <= set(checks['received'])):
        raise ValidationError('Cannot mark incomplete/unvalidated required execution complete')
    return value


def _tactic(store, unit):
    registry, _ = read_registry(store)
    record = next((r for r in registry['records'] if r['id'] == unit and r['kind'] == 'T' and r['state'] == 'active'), None)
    if record is None: raise ValidationError('Use the existing approved Tactic; register inspected legacy records explicitly')
    return record


def record_run(project, record, decision=None, expected_sha256=None):
    validate_run(record)
    with Store(project) as store, store.lock():
        tactic = _tactic(store, record['unit_id'])
        root = configuration(store)['paths']['analyses'] + '/' + record['unit_id'] + '/logs/runs'
        path = root + '/' + record['run_id'] + '.json'
        current = store.read(path)
        actual = hashlib.sha256(current.data).hexdigest() if current.data is not None else None
        if actual != expected_sha256: raise ValidationError('Run changed or ID already exists; resume the same record using its current hash')
        if current.data is None or record['status'] == 'APPROVED': approval(decision)
        # Keep immutable prior run records; R IDs are not report revisions.
        registry_path = root + '/RUN_REGISTRY.json'; registry_snapshot = store.read(registry_path)
        registry = decode(registry_snapshot.data) if registry_snapshot.data else {'schema_version': 1, 'ids': [], 'pending': {}}
        if type(registry) is not dict or set(registry) != {'schema_version', 'ids', 'pending'} or registry['schema_version'] != 1:
            raise ValidationError('Corrupt Run registry')
        data = encode(record)
        if current.data is None and record['run_id'] in registry['ids']:
            if registry['pending'].get(record['run_id']) != hashlib.sha256(data).hexdigest():
                raise ValidationError('Previously registered Run ID cannot be reused after deletion')
        archive = '.research-framework/execution-operations/' + record['unit_id'] + '/' + record['run_id']
        store.ensure_dir(archive)
        for content in ([current.data] if current.data else []) + [data]:
            destination = archive + '/' + hashlib.sha256(content).hexdigest() + '.json'
            if store.read(destination).data is None: store.create(destination, content)
        if record['run_id'] not in registry['ids']:
            registry['ids'].append(record['run_id']); registry['pending'][record['run_id']] = hashlib.sha256(data).hexdigest()
            registry_snapshot = _replace(store, registry_path, encode(registry), registry_snapshot)
        _replace(store, path, data, current)
        if record['run_id'] in registry['pending']:
            del registry['pending'][record['run_id']]
            _replace(store, registry_path, encode(registry), registry_snapshot)
        return {'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'approved_scope_reference': tactic['approval']['reference']}


def handoff(project, value, expected_sha256=None):
    fields = {'schema_version', 'unit_id', 'resume_id', 'status', 'approved_scope_reference', 'known_execution_ids',
              'evidence_received', 'evidence_missing', 'expected_outputs', 'next_human_step', 'updated_at'}
    if type(value) is not dict or set(value) != fields or type(value['schema_version']) is not int or value['schema_version'] != 1:
        raise ValidationError('Invalid cross-agent handoff')
    if value['resume_id'] != value['unit_id'] or value['status'] not in {'WAITING', 'BLOCKED', 'FAILED', 'EXECUTING', 'PLANNING', 'APPROVED', 'COMPLETED'}:
        raise ValidationError('Handoff must preserve the existing Tactic identity and actual status')
    for key in ('approved_scope_reference', 'next_human_step'):
        if type(value[key]) is not str or not value[key].strip(): raise ValidationError('Handoff requires approved scope and a concrete next step')
    for key in ('known_execution_ids', 'evidence_received', 'evidence_missing', 'expected_outputs'):
        if type(value[key]) is not list: raise ValidationError('Handoff evidence/identity fields must be explicit lists')
    if _time(value['updated_at']) is None: raise ValidationError('Handoff update time must be an actual timezone-aware timestamp')
    if value['status'] == 'COMPLETED' and value['evidence_missing']:
        raise ValidationError('A completed handoff cannot conceal missing required evidence')
    with Store(project) as store, store.lock():
        _tactic(store, value['unit_id'])
        path = configuration(store)['paths']['analyses'] + '/' + value['unit_id'] + '/logs/handoff.json'
        current = store.read(path)
        actual = hashlib.sha256(current.data).hexdigest() if current.data else None
        if actual != expected_sha256: raise ValidationError('Handoff changed; review current evidence before replacing it')
        if current.data:
            archive = '.research-framework/handoffs/' + value['unit_id']; store.ensure_dir(archive)
            target = archive + '/' + actual + '.json'
            if store.read(target).data is None: store.create(target, current.data)
        _replace(store, path, encode(value), current)
        return {'path': path, 'resume_id': value['unit_id'], 'status': value['status']}


def hpc_commands(project, config):
    """Prepare commands only. Never connects, transfers, pulls or submits."""
    required = {'verified', 'evidence_reference', 'remote_host', 'remote_repository', 'working_directory', 'launcher',
                'local_launcher', 'remote_outputs', 'local_destination', 'slurm_available', 'slurm_module', 'job_id'}
    if type(config) is not dict or set(config) != required or config['verified'] is not True or not config['evidence_reference']:
        raise ValidationError('HPC command preparation requires verified project-specific context and evidence')
    for key in ('remote_repository', 'working_directory', 'remote_outputs', 'local_destination'):
        if type(config[key]) is not str or not config[key].startswith('/') or '\n' in config[key] or '\x00' in config[key]:
            raise ValidationError('HPC paths must be verified absolute paths')
    if not re.fullmatch(r'[A-Za-z0-9_.@-]+', config['remote_host']) or config['remote_host'].startswith('-'):
        raise ValidationError('Invalid verified remote endpoint')
    validate_relative_path(config['local_launcher']); validate_relative_path(config['launcher'])
    script = read_payload_file(project, config['local_launcher']).decode()
    validate_launcher(script)
    module = ''
    if config['slurm_available'] is not True:
        if not config['slurm_module']: raise ValidationError('Verify Slurm availability or the required module before preparing commands')
        module = 'module load ' + shlex.quote(config['slurm_module']) + ' && '
    quote = shlex.quote
    commands = {'human_operated': True, 'verification_reference': config['evidence_reference'],
        'pull': 'cd ' + quote(config['remote_repository']) + ' && git pull --ff-only',
        'submit': module + 'cd ' + quote(config['working_directory']) + ' && sbatch ' + quote(config['launcher']),
        'monitor': module + 'squeue -u "$USER"',
        'retrieve': 'rsync -avh --progress -- ' + quote(config['remote_host'] + ':' + config['remote_outputs'].rstrip('/') + '/') + ' ' + quote(config['local_destination'].rstrip('/') + '/')}
    if config['job_id'] is not None:
        if not re.fullmatch(r'[0-9]+(?:_[0-9]+)?', config['job_id']): raise ValidationError('Use the actual returned scheduler job ID')
        commands['accounting'] = module + 'sacct -j ' + quote(config['job_id']) + ' --format=JobID,State,ExitCode,Elapsed,MaxRSS,AllocCPUS'
    return commands


def validate_launcher(script):
    lines = script.splitlines()
    if not lines or not re.fullmatch(r'#!(?:/bin/bash|/usr/bin/env bash)', lines[0]): raise ValidationError('Expected a Bash batch launcher')
    executable = False
    for line in lines[1:]:
        stripped = line.strip()
        if stripped.startswith('#SBATCH') and executable: raise ValidationError('All SBATCH directives must precede executable statements')
        if stripped and not stripped.startswith('#'): executable = True
    if re.search(r'\b(?:pip|conda|mamba)\s+(?:install|create|update)\b|<<\s*[\'\"]?(?:PY|PYTHON|EOF)', script):
        raise ValidationError('Science launchers must not provision environments or embed scientific programs')
    if re.search(r'\bconda\s+activate\b', script):
        if not re.search(r'^\s*module\s+load\s+\S+', script, re.M) or not re.search(r'conda\s+shell\.bash\s+hook|(?:source|\.)\s+[^\n]*conda\.sh', script):
            raise ValidationError('Conda jobs require verified module loading and Conda initialization inside the job')
        if not re.search(r'conda\s+activate\s+[\'\"]?/', script):
            raise ValidationError('Conda jobs activate the existing environment by absolute prefix')
    return {'validated': True, 'limits': 'Static ordering/environment checks only; remote policy, resources, imports and scientific entry point require project-specific review.'}
