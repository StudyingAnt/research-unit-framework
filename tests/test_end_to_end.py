"""Release-archive-only installation, scientific records, migration and upgrade."""

import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

from research_program_framework.release import build, fingerprint, source_bundle
from research_program_framework.updates import manifest_dict
from test_records import DECISION


class EndToEndTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); source = Path(__file__).resolve().parents[1]
        self.release = build(source, self.root / 'release')
        unpacked = self.root / 'unpacked'; unpacked.mkdir()
        # Input is the just-built, trusted test archive; inspect all member types.
        with tarfile.open(self.root / 'release.tar.gz') as archive:
            for member in archive.getmembers():
                self.assertTrue(member.isfile() or member.isdir())
                path = unpacked / member.name
                self.assertTrue(path.absolute().is_relative_to(unpacked)) if hasattr(path, 'is_relative_to') else None
                if member.isdir(): path.mkdir(parents=True, exist_ok=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(archive.extractfile(member).read())
        self.distribution = unpacked / 'release'
        self.launcher = self.distribution / 'newproj.pyz'
        self.environment = {'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1'}
        self.project = self.root / 'project'
        self.decision = self.root / 'approval.json'; self.decision.write_text(json.dumps(DECISION))

    def cli(self, *arguments, ok=True, installed=False):
        launcher = self.project / '.research-framework/runtime.pyz' if installed else self.launcher
        result = subprocess.run([sys.executable, '-B', str(launcher), *map(str, arguments)], cwd=self.root,
                                env=self.environment, text=True, capture_output=True)
        if ok: self.assertEqual(result.returncode, 0, result.stderr)
        else: self.assertNotEqual(result.returncode, 0)
        return json.loads(result.stdout) if result.returncode == 0 else result.stderr

    def test_archive_only_new_unit_and_modality_independence(self):
        self.cli('new', self.project)
        self.assertFalse((self.project / '.git').exists())
        body = self.root / 'body.md'; body.write_text('Synthetic approved scope; no experiment performed.\n')
        aim = self.cli('record-new', self.project, 'A', '--title', 'Synthetic objective', '--body-file', body, '--approval-file', self.decision, installed=True)
        strategy = self.cli('record-new', self.project, 'S', '--title', 'Synthetic strategy', '--parent', aim['id'], '--body-file', body, '--approval-file', self.decision, installed=True)
        for modality in ('experimental', 'computational', 'theoretical', 'observational', 'hybrid'):
            body.write_text('## Question\n\nDemonstrate '+modality+' record administration.\n\n## Specifications\n\nSynthetic evidence references only; no actual study is performed.\n')
            unit = self.cli('new-unit', self.project, '--title', 'Synthetic '+modality, '--parent', strategy['id'], '--body-file', body, '--approval-file', self.decision, installed=True)
            identity = unit['record']['id']
            self.assertTrue((self.project / 'reports' / identity / 'en/report.md').exists())
            self.assertFalse((self.project / 'analyses' / identity / 'logs/runs').exists())
        self.assertEqual(len(self.cli('records', self.project, installed=True)['records']), 7)
        self.assertFalse(self.cli('inspect', self.project, installed=True)['pending_updates'])

    def test_archive_only_legacy_migration_preserves_local_and_science(self):
        source = source_bundle(Path(__file__).resolve().parents[1])
        self.project.mkdir()
        for path, encoded in source['legacy_files'].items():
            target = self.project / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(base64.b64decode(encoded))
        local = self.project / 'tools/build_reports.py'; local.write_bytes(local.read_bytes()+b'\n# Synthetic local reporting improvement\n')
        original = local.read_bytes()
        record = self.project / 'reports/legacy-science.md'; record.write_text('Synthetic prior evidence: do not regenerate.\n')
        backups = self.root / 'recovery'; backups.mkdir(mode=0o700)
        args = [self.project, '--release', self.distribution, '--bridge-policy-reviewed', '--keep-local', 'tools/build_reports.py']
        plan = self.cli('migrate-plan', *args)
        self.assertFalse(plan['conflicts']); self.assertFalse((self.project / '.research-framework').exists())
        applied = self.cli('migrate', *args, '--plan-digest', plan['plan_digest'], '--backup-root', backups)
        self.assertEqual(local.read_bytes(), original)
        self.assertEqual(record.read_text(), 'Synthetic prior evidence: do not regenerate.\n')
        self.assertEqual(self.cli('inspect', self.project, installed=True)['framework_version'], self.release.framework_version)
        undo = self.cli('migration-rollback-plan', applied['backup_directory'])
        self.cli('migration-rollback', applied['backup_directory'], '--plan-digest', undo['plan_digest'])
        self.assertEqual(local.read_bytes(), original)
        self.assertFalse((self.project / '.research-framework').exists())

    def test_archive_update_merge_conflict_and_guarded_rollback_commands(self):
        self.cli('new', self.project)
        payload = self.distribution / 'payload'; path = '.research-framework/policy/AGENTS.md'
        local = self.project / path; original = local.read_bytes(); local.write_bytes(b'Local approved instruction.\n'+original)
        upstream = payload / path; upstream.write_bytes(upstream.read_bytes()+b'\nNew generic policy.\n')
        release = manifest_dict(self.release); release['framework_version'] = '1.1.1'
        for item in release['files']:
            if item['path'] == path: item.update(fingerprint(upstream.read_bytes()))
        (self.distribution / 'manifest.json').write_text(json.dumps(release))
        plan = self.cli('update-plan', self.project, '--release', self.distribution)
        self.assertFalse(plan['conflicts'])
        result = self.cli('update', self.project, '--release', self.distribution, '--plan-digest', plan['plan_digest'])
        self.assertIn(b'Local approved instruction.', local.read_bytes()); self.assertIn(b'New generic policy.', local.read_bytes())
        undo = self.cli('rollback-plan', self.project, result['operation_id'])
        self.cli('rollback', self.project, result['operation_id'], '--plan-digest', undo['plan_digest'])
        self.assertEqual(local.read_bytes(), b'Local approved instruction.\n'+original)
        plan = self.cli('update-plan', self.project, '--release', self.distribution)
        result = self.cli('update', self.project, '--release', self.distribution, '--plan-digest', plan['plan_digest'])
        local.write_bytes(local.read_bytes()+b'Later scientific instruction.\n')
        self.cli('rollback-plan', self.project, result['operation_id'], ok=False)
