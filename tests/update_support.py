"""Construct synthetic registered installations; no initialization API is shipped."""

import hashlib
from pathlib import Path
import tempfile
import unittest

from research_program_framework.manifests import validate_release_manifest
from research_program_framework.updates import encode, RECEIPT


def fingerprint(data, mode='0644'):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'mode': mode}


def manifest(files, version):
    return validate_release_manifest({'schema_version': 1, 'kind': 'framework_release',
        'framework_version': version, 'specification_version': '1.1', 'source_revision': '1' * 40,
        'files': [{'path': path, **fingerprint(data), 'ownership': 'D' if path in {'README.md', 'docs/compute.md'} else 'A',
                   **({'project_owner': 'C'} if path in {'README.md', 'docs/compute.md'} else {})}
                  for path, data in sorted(files.items())]})


def put(root, path, data, mode=0o644):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    target.chmod(mode)


class UpdateCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / 'project'
        self.payload = self.root / 'payload'
        self.project.mkdir(); self.payload.mkdir()
        self.original = {'templates/unit.md': b'first\nmiddle\nlast\n', 'README.md': b'initial project seed\n'}
        self.old_release = manifest(self.original, '1.1.0')
        self.receipt = {'schema_version': 1, 'kind': 'framework_installation', 'project_id': 'a' * 32,
            'generation': 0, 'release': None, 'last_operation': None,
            'installed': {path: fingerprint(data) for path, data in self.original.items() if path != 'README.md'}}
        from research_program_framework.updates import manifest_dict
        self.receipt['release'] = manifest_dict(self.old_release)
        for path, data in self.original.items():
            put(self.project, path, data)
            if path != 'README.md':
                put(self.project, '.research-framework/baselines/' + fingerprint(data)['sha256'], data)
        (self.project / '.research-framework').chmod(0o700)
        put(self.project, RECEIPT, encode(self.receipt))
        put(self.project, 'reports/kept.md', b'Synthetic scientific record; preserve\n')
        put(self.project, '.git/HEAD', b'ref: refs/heads/synthetic\n')
        self.new_files = {'templates/unit.md': b'NEW\nmiddle\nlast\n', 'README.md': b'changed seed\n'}
        self.release = self.bundle(self.new_files)

    def bundle(self, files, version='1.1.1'):
        for target in self.payload.rglob('*'):
            if target.is_file():
                target.unlink()
        # Fixture reset only, never performed by framework code.
        for target in sorted(self.payload.rglob('*'), reverse=True):
            if target.is_dir():
                target.rmdir()
        for path, data in files.items():
            put(self.payload, path, data)
        return manifest(files, version)
