"""Read-only installation/record diagnostics and reporting dependency discovery."""

import hashlib
import importlib.metadata
from pathlib import Path
import shutil

from .paths import ValidationError, validate_relative_path
from .records import configuration, read_registry
from .storage import Store
from .updates import read_receipt, project_owners
from .transactions import pending_operations


def inspect_project(project):
    with Store(project) as store:
        receipt, _ = read_receipt(store)
        files = []
        for item in receipt['release']['files']:
            if item['ownership'] != 'A': continue
            base = store.read('.research-framework/baselines/' + item['sha256'])
            if base.data is None or len(base.data) != item['size'] or hashlib.sha256(base.data).hexdigest() != item['sha256']:
                raise ValidationError('Missing/corrupt exact upstream ancestor')
            current = store.read(item['path']).fingerprint()
            files.append({'path': item['path'], 'current': current,
                          'modified_since_installation': current != receipt['installed'][item['path']],
                          'differs_from_upstream': current != {k: item[k] for k in ('size', 'sha256', 'mode')}})
        registry, _ = read_registry(store)
        records = []
        for record in registry['records']:
            current = store.read(record['path'])
            records.append({'id': record['id'], 'state': record['state'], 'path': record['path'],
                            'body_matches_adopted_hash': current.data is not None and hashlib.sha256(current.data).hexdigest() == record['sha256']})
        return {'project_id': receipt['project_id'], 'framework_version': receipt['release']['framework_version'],
                'source_revision': receipt['release']['source_revision'], 'generation': receipt['generation'],
                'pending_updates': list(pending_operations(store)), 'managed_files': files,
                'project_owned': project_owners(receipt), 'scientific_records': records,
                'limits': 'Local edits are preserved, not automatically adopted. Inspect pending scientific/report operations and project-specific policies before work.'}


def doctor(project):
    with Store(project) as store:
        config = configuration(store).get('reporting', {})
        fonts = {}
        for lang in ('en', 'ko'):
            location = config.get('font_' + lang)
            if not location:
                fonts[lang] = False
                continue
            path = Path(location)
            if not path.is_absolute():
                validate_relative_path(location)
                path = store.root / path
            fonts[lang] = path.is_file()
        versions = {}
        for name in ('weasyprint', 'matplotlib', 'Pillow', 'fonttools'):
            try: versions[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError: versions[name] = None
        return {'pandoc': shutil.which(config.get('pandoc', 'pandoc')), 'optional_dependencies': versions,
                'font_files_present': fonts,
                'environment_modified': False, 'remote_access_attempted': False}
