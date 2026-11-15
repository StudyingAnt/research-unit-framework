"""Synthetic metadata-free adoption, external backup and interrupted undo."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research_program_framework.migration import (plan_migration, apply_migration,
    plan_migration_rollback, rollback_migration)
from research_program_framework.paths import ValidationError
from research_program_framework.release import build, source_bundle
from research_program_framework.updates import plan_update


class MigrationTests(unittest.TestCase):
    def setUp(self):
        import base64
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.project = self.root / 'project'; self.project.mkdir()
        source = Path(__file__).resolve().parents[1]
        bundle = source_bundle(source)
        self.legacy_manifest = bundle['legacy_manifest']
        self.legacy_files = {p: base64.b64decode(data) for p, data in bundle['legacy_files'].items()}
        for path, data in self.legacy_files.items():
            target = self.project / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
        self.release = build(source, self.root / 'release')
        self.backups = self.root / 'backups'; self.backups.mkdir(mode=0o700)
        (self.project / 'reports/science.md').write_text('Synthetic scientific record: preserve exactly.\n')
        self.before = self.contents()

    def contents(self):
        return {p.relative_to(self.project).as_posix(): p.read_bytes() for p in self.project.rglob('*') if p.is_file()}

    def plan(self, **kwargs):
        return plan_migration(self.project, self.root / 'release/payload', self.release,
                              self.legacy_manifest, self.legacy_files, **kwargs)

    def test_migrate_update_and_guarded_rollback(self):
        plan = self.plan(bridge=True)
        self.assertEqual(self.contents(), self.before)
        self.assertFalse(plan.conflicts)
        result = apply_migration(plan, self.backups)
        self.assertEqual((self.project / 'reports/science.md').read_bytes(), self.before['reports/science.md'])
        self.assertFalse((self.project / 'coordination/plans/ID_REGISTRY.json').exists())
        self.assertIn(self.before['AGENTS.md'], (self.project / 'AGENTS.md').read_bytes())
        self.assertFalse(plan_update(self.project, self.root / 'release/payload', self.release).conflicts)
        directory = result['backup_directory']
        undo = plan_migration_rollback(directory)
        rollback_migration(directory, undo['plan_digest'])
        self.assertEqual(self.contents(), self.before)
        self.assertFalse((self.project / '.research-framework').exists())

    def test_conflict_and_explicit_preservation(self):
        path = self.project / 'tools/new_unit.py'; path.write_text('Locally developed helper\n')
        plan = self.plan()
        self.assertIn('tools/new_unit.py', plan.conflicts)
        with self.assertRaises(ValidationError): apply_migration(plan, self.backups)
        result = apply_migration(self.plan(resolutions={'tools/new_unit.py': None}), self.backups)
        self.assertEqual(path.read_text(), 'Locally developed helper\n')
        (self.project / 'tools/framework.py').write_text('A later local change\n')
        with self.assertRaises(ValidationError): plan_migration_rollback(result['backup_directory'])

    def test_stale_plan_and_unknown_collision(self):
        plan = self.plan(); (self.project / 'tools/new_unit.py').write_text('changed')
        with self.assertRaises(ValidationError): apply_migration(plan, self.backups)
        (self.project / 'tools/framework.py').write_text('unowned')
        self.assertIn('tools/framework.py', self.plan().conflicts)
        with self.assertRaises(ValidationError): self.plan(resolutions={'tools/framework.py': None})

    def test_backups_precede_target_writes(self):
        def fail(event, index=None):
            if event == 'backups_verified': raise KeyboardInterrupt()
        with patch('research_program_framework.migration._checkpoint', fail):
            with self.assertRaises(KeyboardInterrupt): apply_migration(self.plan(), self.backups)
        self.assertEqual(self.contents(), self.before)
        directory = next(self.backups.glob('migration-*'))
        rollback_migration(directory, plan_migration_rollback(directory)['plan_digest'])
        self.assertEqual(self.contents(), self.before)

    def test_interrupt_at_publication_and_resume_rollback(self):
        def fail(event, index=None):
            if event == 'published' and index == 2: raise KeyboardInterrupt()
        with patch('research_program_framework.migration._checkpoint', fail):
            with self.assertRaises(KeyboardInterrupt): apply_migration(self.plan(), self.backups)
        directory = next(self.backups.glob('migration-*'))
        def fail_restore(event, index=None):
            if event == 'restored': raise KeyboardInterrupt()
        with patch('research_program_framework.migration._checkpoint', fail_restore):
            with self.assertRaises(KeyboardInterrupt): rollback_migration(directory, plan_migration_rollback(directory)['plan_digest'])
        rollback_migration(directory, plan_migration_rollback(directory)['plan_digest'])
        self.assertEqual(self.contents(), self.before)

    def test_backup_corruption_and_later_modification_block_all_undo(self):
        result = apply_migration(self.plan(), self.backups)
        directory = Path(result['backup_directory'])
        next(directory.glob('before-*.bin')).write_bytes(b'corrupt')
        with self.assertRaises(ValidationError): plan_migration_rollback(directory)

    def test_unchanged_local_helper_can_change_without_rollback_overwrite(self):
        helper = self.project / 'tools/new_unit.py'; helper.write_text('local helper\n')
        result = apply_migration(self.plan(resolutions={'tools/new_unit.py': None}), self.backups)
        helper.write_text('later work\n')
        directory = result['backup_directory']
        rollback_migration(directory, plan_migration_rollback(directory)['plan_digest'])
        self.assertEqual(helper.read_text(), 'later work\n')

    def test_unowned_git_and_symlink_paths_are_preserved_or_rejected(self):
        repo = self.project / 'repos/science/.git'; repo.mkdir(parents=True)
        (repo / 'HEAD').write_text('synthetic history')
        before = (repo / 'HEAD').read_bytes()
        result = apply_migration(self.plan(), self.backups)
        self.assertEqual((repo / 'HEAD').read_bytes(), before)
        self.assertEqual((self.project / 'reports/science.md').read_bytes(), self.before['reports/science.md'])

    def test_external_backup_must_not_be_inside_target(self):
        with self.assertRaises(ValidationError): apply_migration(self.plan(), self.project / 'backup')
        self.assertEqual(self.contents(), self.before)
