"""Public artifact inspection includes embedded runtime starter/base64 content."""

import base64
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from research_program_framework.privacy import audit_bytes, audit_archive
from research_program_framework.release import build


class PrivacyTests(unittest.TestCase):
    def test_secret_and_local_context_patterns_are_reported_without_values(self):
        secret = ('gh' + 'p_' + 'x'*40).encode()
        issues = audit_bytes(secret, 'fixture.txt')
        self.assertEqual(issues[0]['category'], 'credential-pattern')
        self.assertNotIn(secret.decode(), json.dumps(issues))
        self.assertTrue(audit_bytes(b'/synthetic/private/context', 'test', ['/synthetic/private']))

    def test_base64_bundle_inside_runtime_is_inspected(self):
        data = json.dumps({'files': {'example.txt': base64.b64encode(b'private-fixture-marker').decode()}}).encode()
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as archive: archive.writestr('bundle.json', data)
        self.assertTrue(audit_bytes(output.getvalue(), 'runtime.pyz', ['private-fixture-marker']))

    def test_release_has_normalized_headers_and_no_local_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); build(Path(__file__).resolve().parents[1], root / 'release')
            result = audit_archive(root / 'release.tar.gz')
            self.assertFalse(result['issues']); self.assertGreater(result['entries'], 20)
