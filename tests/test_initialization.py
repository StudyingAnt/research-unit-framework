"""Independent release and fresh-project safety tests using synthetic data."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_program_framework.initialization import create_project
from research_program_framework.paths import ValidationError
from research_program_framework.release import build
from research_program_framework.updates import plan_update


class InitializationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.release = build(Path(__file__).resolve().parents[1], self.root / 'release')
        self.project = self.root / 'project'

    def test_independent_zipapp_and_new_project(self):
        process = subprocess.run([sys.executable, '-B', str(self.root / 'release/newproj.pyz'), 'new', str(self.project)],
                                 cwd=self.root, env={'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1'}, capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        receipt = json.loads((self.project / '.research-framework/installation.json').read_text())
        self.assertEqual(receipt['generation'], 0)
        self.assertTrue((self.root / 'release/schemas/report.schema.json').is_file())
        self.assertFalse((self.project / '.git').exists())
        self.assertEqual(json.loads((self.project / 'coordination/plans/ID_REGISTRY.json').read_text())['records'], [])
        self.assertFalse(plan_update(self.project, self.root / 'release/payload', self.release).conflicts)

    def test_existing_or_symlink_destination_untouched(self):
        self.project.mkdir(); (self.project / 'keep').write_text('keep')
        with self.assertRaises(ValidationError):
            create_project(self.project, self.root / 'release/payload', self.release)
        self.assertEqual((self.project / 'keep').read_text(), 'keep')
        linked = self.root / 'linked'; linked.symlink_to(self.project)
        with self.assertRaises((ValidationError, OSError)):
            create_project(linked, self.root / 'release/payload', self.release)

    def test_payload_corruption_rejected_before_destination(self):
        (self.root / 'release/payload/README.md').write_text('corrupt')
        with self.assertRaises(ValidationError):
            create_project(self.project, self.root / 'release/payload', self.release)
        self.assertFalse(self.project.exists())
