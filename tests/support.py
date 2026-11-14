"""Synthetic fixtures; never read or mutate local scientific projects."""

import hashlib
from pathlib import Path
import tempfile
import unittest

from research_program_framework.paths import FileFingerprint


def record(path='templates/report.en.md', data=b'Synthetic template\n', **extra):
    return {'path': path, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'mode': '0644', **extra}


def release(files=None):
    return {'schema_version': 1, 'kind': 'framework_release', 'framework_version': '1.1.0-rc.1',
            'specification_version': '1.1', 'source_revision': '1' * 40,
            'files': files if files is not None else [record(ownership='A')]}


def legacy(files=None):
    return {'schema_version': 1, 'kind': 'legacy_baseline', 'framework_version': '0.5',
            'distribution': 'Starter v3', 'observed_on': '2026-11-14', 'source_revision': None,
            'content_review': 'reviewed_generic', 'files': files if files is not None else [record()]}


class PayloadCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.payload = self.root / 'payload'
        self.payload.mkdir()

    def write(self, path='templates/report.en.md', data=b'Synthetic template\n', mode=0o644):
        target = self.payload / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(mode)
        return FileFingerprint(**{**record(path, data), 'mode': f'{mode:04o}'})
