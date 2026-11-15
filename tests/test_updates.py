from dataclasses import replace
import os
import json
from unittest import mock

from research_program_framework import transactions
from research_program_framework.paths import ValidationError
from research_program_framework.storage import Store
from research_program_framework.updates import plan_update, RECEIPT, read_receipt, encode
from research_program_framework.transactions import (apply_update, plan_rollback, apply_rollback,
    plan_recovery, TransactionError, pending_operations)
from update_support import UpdateCase, put, fingerprint


class Interrupted(BaseException):
    """Simulate process interruption that cannot execute exception recovery."""


class UpdateTests(UpdateCase):
    def plan(self, **options):
        return plan_update(self.project, self.payload, self.release, **options)

    def receipt_now(self):
        with Store(self.project) as store:
            return read_receipt(store)[0]

    def crash(self, event, index=None):
        def fail(point, number=None):
            if point == event and (index is None or number == index):
                raise Interrupted()
        with mock.patch.object(transactions, '_checkpoint', side_effect=fail), self.assertRaises(Interrupted):
            apply_update(self.plan())
        with Store(self.project) as store:
            operations = pending_operations(store)
        self.assertEqual(len(operations), 1)
        return operations[0]

    def test_basic_apply_and_rollback(self):
        plan = self.plan()
        self.assertFalse(plan.conflicts)
        self.assertIn('UPDATE', [a.disposition for a in plan.actions])
        result = apply_update(plan)
        self.assertEqual(result.status, 'COMMITTED')
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), self.new_files['templates/unit.md'])
        self.assertEqual((self.project / 'README.md').read_bytes(), self.original['README.md'])
        self.assertEqual(self.receipt_now()['generation'], 1)
        recovery = plan_rollback(self.project, result.operation_id)
        self.assertEqual(apply_rollback(recovery).status, 'ROLLED_BACK')
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), self.original['templates/unit.md'])
        self.assertEqual(self.receipt_now(), self.receipt)
        self.assertEqual(apply_rollback(plan_rollback(self.project, result.operation_id)).status, 'NO_CHANGE')

    def test_disjoint_merge_and_exact_new_baseline(self):
        put(self.project, 'templates/unit.md', b'first\nmiddle\nLOCAL\n')
        plan = self.plan()
        self.assertEqual(next(a for a in plan.actions if a.path == 'templates/unit.md').disposition, 'MERGE')
        result = apply_update(plan)
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), b'NEW\nmiddle\nLOCAL\n')
        path = '.research-framework/baselines/' + fingerprint(self.new_files['templates/unit.md'])['sha256']
        self.assertEqual((self.project / path).read_bytes(), self.new_files['templates/unit.md'])
        apply_rollback(plan_rollback(self.project, result.operation_id))
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), b'first\nmiddle\nLOCAL\n')

    def test_conflict_blocks_every_write(self):
        put(self.project, 'templates/unit.md', b'LOCAL\nmiddle\nlast\n')
        before = (self.project / RECEIPT).read_bytes()
        plan = self.plan()
        self.assertEqual(plan.conflicts, ('templates/unit.md',))
        with self.assertRaises(ValidationError):
            apply_update(plan)
        self.assertEqual((self.project / RECEIPT).read_bytes(), before)
        self.assertFalse((self.project / '.research-framework/transactions').exists())

    def test_explicit_resolutions_and_keep_local(self):
        put(self.project, 'templates/unit.md', b'LOCAL\nmiddle\nlast\n')
        plan = self.plan(resolutions={'templates/unit.md': b'REVIEWED\n'})
        self.assertFalse(plan.conflicts)
        apply_update(plan)
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), b'REVIEWED\n')

    def test_keep_local_resolution(self):
        put(self.project, 'templates/unit.md', b'LOCAL\nmiddle\nlast\n')
        apply_update(self.plan(resolutions={'templates/unit.md': None}))
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), b'LOCAL\nmiddle\nlast\n')

    def test_local_deletion_preserved_or_conflicted(self):
        (self.project / 'templates/unit.md').unlink()
        self.assertIn('templates/unit.md', self.plan().conflicts)
        self.release = self.bundle(self.original)
        plan = self.plan()
        self.assertFalse(plan.conflicts)
        apply_update(plan)
        self.assertFalse((self.project / 'templates/unit.md').exists())

    def test_new_file_and_parent_rollback(self):
        self.release = self.bundle({**self.new_files, 'tools/new/helper.py': b'new source\n'})
        result = apply_update(self.plan())
        self.assertTrue((self.project / 'tools/new/helper.py').is_file())
        apply_rollback(plan_rollback(self.project, result.operation_id))
        self.assertFalse((self.project / 'tools').exists())

    def test_unmanaged_collision_even_if_identical(self):
        self.release = self.bundle({**self.new_files, 'tools/helper.py': b'local source\n'})
        put(self.project, 'tools/helper.py', b'local source\n')
        self.assertIn('tools/helper.py', self.plan().conflicts)
        with self.assertRaises(ValidationError):
            self.plan(resolutions={'tools/helper.py': None})

    def test_removed_unmodified_file_and_modified_retirement(self):
        self.release = self.bundle({'README.md': b'seed only\n', 'tools/other.py': b'other\n'})
        result = apply_update(self.plan())
        self.assertFalse((self.project / 'templates/unit.md').exists())
        apply_rollback(plan_rollback(self.project, result.operation_id))
        put(self.project, 'templates/unit.md', b'custom\n')
        self.assertIn('templates/unit.md', self.plan().conflicts)

    def test_stale_plan_content_mode_parent_and_receipt(self):
        for change in ['content', 'mode', 'parent', 'receipt']:
            with self.subTest(change=change):
                put(self.project, 'templates/unit.md', self.original['templates/unit.md'])
                put(self.project, RECEIPT, encode(self.receipt))
                plan = self.plan()
                self.assertFalse(plan.conflicts)
                target = self.project / 'templates/unit.md'
                if change == 'content':
                    target.write_bytes(b'edited after planning\n')
                elif change == 'mode':
                    target.chmod(0o755)
                elif change == 'parent':
                    (self.project / 'templates').rename(self.project / 'saved')
                    put(self.project, 'templates/unit.md', target.parent.parent.joinpath('saved/unit.md').read_bytes())
                else:
                    value = self.receipt_now(); value['generation'] += 1
                    put(self.project, RECEIPT, encode(value))
                with self.assertRaises(ValidationError):
                    apply_update(plan)

    def test_stale_bundle_and_forged_plan(self):
        plan = self.plan()
        forged = replace(plan, actions=tuple(replace(a, content=b'forged\n') if a.path == 'templates/unit.md' else a
                                            for a in plan.actions))
        with self.assertRaises(ValidationError):
            apply_update(forged)
        put(self.payload, 'templates/unit.md', b'tampered\n')
        with self.assertRaises(ValidationError):
            apply_update(plan)

    def test_no_initializer_or_unknown_baseline(self):
        (self.project / RECEIPT).unlink()
        with self.assertRaises(ValidationError):
            self.plan()
        self.assertFalse((self.project / '.research-framework/transactions').exists())

    def test_corrupt_baseline_refused(self):
        baseline = next((self.project / '.research-framework/baselines').iterdir())
        baseline.write_bytes(b'wrong ancestor')
        with self.assertRaises(ValidationError):
            self.plan()

    def test_nested_git_and_symlink_paths_refused(self):
        put(self.project, 'templates/.git', b'gitdir: external\n')
        with self.assertRaises(ValidationError):
            self.plan()
        (self.project / 'templates/.git').unlink()
        (self.project / 'templates').rename(self.root / 'outside')
        (self.project / 'templates').symlink_to(self.root / 'outside', target_is_directory=True)
        with self.assertRaises(ValidationError):
            self.plan()

    def test_post_update_local_modification_blocks_entire_rollback(self):
        self.release = self.bundle({**self.new_files, 'tools/new.py': b'new\n'})
        result = apply_update(self.plan())
        put(self.project, 'templates/unit.md', b'later local work\n')
        with self.assertRaises(ValidationError):
            plan_rollback(self.project, result.operation_id)
        self.assertTrue((self.project / 'tools/new.py').exists())
        self.assertEqual(self.receipt_now()['generation'], 1)

    def test_stale_rollback_plan(self):
        result = apply_update(self.plan())
        plan = plan_rollback(self.project, result.operation_id)
        put(self.project, 'templates/unit.md', b'newer local work\n')
        with self.assertRaises(ValidationError):
            apply_rollback(plan)

    def test_backup_corruption_refuses_rollback(self):
        result = apply_update(self.plan())
        put(self.project, f'.research-framework/backups/{result.operation_id}/0.bin', b'corrupt')
        with self.assertRaises(ValidationError):
            plan_rollback(self.project, result.operation_id)

    def test_backup_failure_never_changes_payload(self):
        original = Store.create
        def fail(store, path, *args, **kwargs):
            if '/backups/' in path:
                raise OSError('synthetic backup failure')
            return original(store, path, *args, **kwargs)
        with mock.patch.object(Store, 'create', fail), self.assertRaises(TransactionError):
            apply_update(self.plan())
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), self.original['templates/unit.md'])
        self.assertEqual(self.receipt_now(), self.receipt)
        with Store(self.project) as store:
            self.assertFalse(pending_operations(store))

    def test_interrupted_before_and_after_file_write(self):
        operation = self.crash('after_write', 0)
        with self.assertRaises(ValidationError):
            self.plan()
        apply_rollback(plan_recovery(self.project, operation))
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), self.original['templates/unit.md'])
        self.assertEqual(self.receipt_now(), self.receipt)

    def test_prepared_interruption_aborts_without_modification(self):
        operation = self.crash('prepared')
        self.assertEqual(apply_rollback(plan_recovery(self.project, operation)).status, 'ABORTED')
        self.assertEqual(self.receipt_now(), self.receipt)

    def test_interrupted_after_receipt_write(self):
        operation = self.crash('after_write', 1)
        self.assertEqual(self.receipt_now()['generation'], 1)
        apply_rollback(plan_recovery(self.project, operation))
        self.assertEqual(self.receipt_now(), self.receipt)

    def test_interrupted_rollback_resumes(self):
        result = apply_update(self.plan())
        plan = plan_rollback(self.project, result.operation_id)
        def fail(event, index=None):
            if event == 'after_restore' and index == 0:
                raise Interrupted()
        with mock.patch.object(transactions, '_checkpoint', side_effect=fail), self.assertRaises(Interrupted):
            apply_rollback(plan)
        apply_rollback(plan_recovery(self.project, result.operation_id))
        self.assertEqual(self.receipt_now(), self.receipt)

    def test_concurrent_edit_at_write_boundary_is_preserved(self):
        def edit(event, index=None):
            if event == 'before_write' and index == 0:
                put(self.project, 'templates/unit.md', b'concurrent local work\n')
        with mock.patch.object(transactions, '_checkpoint', side_effect=edit), self.assertRaises(TransactionError):
            apply_update(self.plan())
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), b'concurrent local work\n')
        self.assertEqual(self.receipt_now(), self.receipt)

    def test_scientific_records_and_git_unchanged(self):
        before = {p: (self.project / p).read_bytes() for p in ['reports/kept.md', '.git/HEAD']}
        result = apply_update(self.plan())
        apply_rollback(plan_rollback(self.project, result.operation_id))
        self.assertEqual(before, {p: (self.project / p).read_bytes() for p in ['reports/kept.md', '.git/HEAD']})

    def test_dry_run_has_no_metadata_or_access_time_changes(self):
        known = [self.project, self.payload, *self.project.rglob('*'), *self.payload.rglob('*')]
        for path in known:
            os.utime(path, ns=(1000000000, path.stat().st_mtime_ns), follow_symlinks=False)
        before = {str(path): tuple(path.lstat()) + (path.lstat().st_atime_ns, path.lstat().st_mtime_ns,
                  path.lstat().st_ctime_ns) for path in known}
        plan = self.plan()
        plan.describe()
        after = {str(path): tuple(path.lstat()) + (path.lstat().st_atime_ns, path.lstat().st_mtime_ns,
                 path.lstat().st_ctime_ns) for path in known}
        self.assertEqual(before, after)
        self.assertFalse((self.project / '.research-framework/transactions').exists())

    def test_repeat_identical_release_is_noop(self):
        apply_update(self.plan())
        self.assertEqual(apply_update(self.plan()).status, 'NO_CHANGE')

    def test_later_update_prevents_old_rollback(self):
        first = apply_update(self.plan())
        self.release = self.bundle({**self.new_files, 'templates/unit.md': b'new release\n'}, '1.1.2')
        second = apply_update(self.plan())
        with self.assertRaises(ValidationError):
            plan_rollback(self.project, first.operation_id)
        apply_rollback(plan_rollback(self.project, second.operation_id))
        apply_rollback(plan_rollback(self.project, first.operation_id))

    def test_direct_rewrite_is_not_trusted_as_completed_child_rollback(self):
        result = apply_update(self.plan())
        content = (self.project / 'templates/unit.md').read_bytes()
        put(self.project, 'templates/unit.md', content)
        with self.assertRaises(ValidationError):
            plan_rollback(self.project, result.operation_id)

    def test_binary_conflict_never_overwrites(self):
        old = b'\0old'
        self.original['templates/unit.md'] = old
        # Register this synthetic ancestor explicitly in the fixture metadata.
        from update_support import manifest
        from research_program_framework.updates import manifest_dict
        put(self.project, 'templates/unit.md', b'\0local')
        put(self.project, '.research-framework/baselines/' + fingerprint(old)['sha256'], old)
        self.receipt['release'] = manifest_dict(manifest(self.original, '1.1.0'))
        self.receipt['installed']['templates/unit.md'] = fingerprint(old)
        put(self.project, RECEIPT, encode(self.receipt))
        self.release = self.bundle({**self.new_files, 'templates/unit.md': b'\0new'})
        with self.assertRaises(ValidationError):
            apply_update(self.plan())
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), b'\0local')

    def test_modes_are_merged_and_restored(self):
        (self.project / 'templates/unit.md').chmod(0o755)
        result = apply_update(self.plan())
        self.assertEqual((self.project / 'templates/unit.md').stat().st_mode & 0o777, 0o755)
        apply_rollback(plan_rollback(self.project, result.operation_id))
        self.assertEqual((self.project / 'templates/unit.md').stat().st_mode & 0o777, 0o755)

    def test_seed_deletions_customizations_and_new_seeds_are_preserved(self):
        from dataclasses import replace
        put(self.project, 'README.md', b'project-specific instructions\n')
        self.new_files['docs/compute.md'] = b'new seed\n'
        self.release = self.bundle(self.new_files)
        self.release = replace(self.release, files=tuple(replace(f, ownership='D', project_owner='C')
                               if f.path == 'docs/compute.md' else f for f in self.release.files))
        apply_update(self.plan())
        self.assertEqual((self.project / 'README.md').read_bytes(), b'project-specific instructions\n')
        self.assertFalse((self.project / 'docs/compute.md').exists())
        (self.project / 'README.md').unlink()
        self.assertEqual(apply_update(self.plan()).status, 'NO_CHANGE')
        self.assertFalse((self.project / 'README.md').exists())

    def test_ownership_promotion_is_a_conflict(self):
        from dataclasses import replace
        from research_program_framework.updates import manifest_dict
        old = replace(self.old_release, files=tuple(replace(f, ownership='D', project_owner='C')
                      if f.path == 'templates/unit.md' else f for f in self.old_release.files))
        self.receipt['release'] = manifest_dict(old); self.receipt['installed'] = {}
        put(self.project, RECEIPT, encode(self.receipt))
        self.assertIn('templates/unit.md', self.plan().conflicts)

    def test_missing_and_corrupt_receipts_do_not_initialize(self):
        for data in [b'{}', b'{"schema_version":1,"schema_version":2}', b'not JSON']:
            put(self.project, RECEIPT, data)
            with self.assertRaises(ValidationError):
                self.plan()
            self.assertFalse((self.project / '.research-framework/transactions').exists())

    def test_lock_prevents_another_mutation(self):
        plan = self.plan()
        with Store(self.project) as store, store.lock():
            with self.assertRaises(ValidationError):
                apply_update(plan)

    def test_rollback_dry_run_has_no_access_time_or_directory_changes(self):
        for path in [self.project, self.payload, *self.project.rglob('*'), *self.payload.rglob('*')]:
            os.utime(path, ns=(1000000000, path.stat().st_mtime_ns), follow_symlinks=False)
        result = apply_update(self.plan())
        known = [self.project, *self.project.rglob('*')]
        before = {str(p): (p.stat().st_atime_ns, p.stat().st_mtime_ns, p.stat().st_ctime_ns) for p in known}
        plan_rollback(self.project, result.operation_id).describe()
        after = {str(p): (p.stat().st_atime_ns, p.stat().st_mtime_ns, p.stat().st_ctime_ns) for p in known}
        self.assertEqual(before, after)

    def test_added_directory_with_new_user_files_is_not_removed(self):
        self.release = self.bundle({**self.new_files, 'tools/new.py': b'generic tool\n'})
        result = apply_update(self.plan())
        put(self.project, 'tools/user.py', b'later user addition\n')
        apply_rollback(plan_rollback(self.project, result.operation_id))
        self.assertEqual((self.project / 'tools/user.py').read_bytes(), b'later user addition\n')

    def test_deleted_post_update_file_blocks_rollback(self):
        result = apply_update(self.plan())
        (self.project / 'templates/unit.md').unlink()
        with self.assertRaises(ValidationError):
            plan_rollback(self.project, result.operation_id)

    def test_journal_corruption_and_illegal_targets_are_rejected(self):
        result = apply_update(self.plan())
        path = f'.research-framework/transactions/{result.operation_id}/journal.json'
        original = (self.project / path).read_bytes()
        put(self.project, path, b'{}')
        with self.assertRaises(ValidationError):
            plan_rollback(self.project, result.operation_id)
        journal = json.loads(original)
        journal['entries'][0]['path'] = 'reports/kept.md'
        put(self.project, path, encode(transactions._signed(journal)))
        with self.assertRaises(ValidationError):
            plan_rollback(self.project, result.operation_id)

    def test_backup_symlink_is_not_followed(self):
        result = apply_update(self.plan())
        path = self.project / f'.research-framework/backups/{result.operation_id}/0.bin'
        outside = self.root / 'outside'; outside.write_bytes(path.read_bytes())
        path.unlink(); path.symlink_to(outside)
        with self.assertRaises(ValidationError):
            plan_rollback(self.project, result.operation_id)

    def test_staged_write_failure_recovers_earlier_changes(self):
        def fail(event, index=None):
            if event == 'before_write' and index == 1:
                raise OSError('synthetic write failure after first file')
        with mock.patch.object(transactions, '_checkpoint', side_effect=fail), self.assertRaises(TransactionError):
            apply_update(self.plan())
        self.assertEqual(self.receipt_now(), self.receipt)
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), self.original['templates/unit.md'])

    def test_interrupted_addition_recovers_and_removes_only_owned_empty_parents(self):
        self.release = self.bundle({**self.new_files, 'tools/new/helper.py': b'new\n'})
        operation = self.crash('after_write', 1)
        apply_rollback(plan_recovery(self.project, operation))
        self.assertFalse((self.project / 'tools').exists())
        self.assertEqual(self.receipt_now(), self.receipt)

    def test_concurrent_rollback_edit_is_preserved_and_journal_remains_pending(self):
        result = apply_update(self.plan())
        plan = plan_rollback(self.project, result.operation_id)
        def edit(event, index=None):
            if event == 'before_restore' and index == 0:
                put(self.project, 'templates/unit.md', b'new local edit during rollback\n')
        with mock.patch.object(transactions, '_checkpoint', side_effect=edit), self.assertRaises(ValidationError):
            apply_rollback(plan)
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), b'new local edit during rollback\n')
        with Store(self.project) as store:
            self.assertIn(result.operation_id, pending_operations(store))

    def test_large_journal_refused_before_operation_storage(self):
        plan = self.plan()
        with mock.patch.object(transactions, 'MAX_METADATA', 16), self.assertRaises(ValidationError):
            apply_update(plan)
        self.assertFalse((self.project / '.research-framework/transactions').exists())

    def test_corrupt_backup_at_prepare_boundary_prevents_payload_changes(self):
        def corrupt(event, index=None):
            if event == 'prepared':
                backup = next((self.project / '.research-framework/backups').glob('*/0.bin'))
                backup.write_bytes(b'corrupt after backup verification')
        with mock.patch.object(transactions, '_checkpoint', side_effect=corrupt), self.assertRaises(TransactionError):
            apply_update(self.plan())
        self.assertEqual(self.receipt_now(), self.receipt)
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), self.original['templates/unit.md'])
        with Store(self.project) as store:
            self.assertFalse(pending_operations(store))

    def test_swapped_stage_is_rejected_without_following_link(self):
        outside = self.root / 'outside'; outside.write_bytes(b'synthetic outside source\n')
        original = Store.publish
        swapped = False
        def publish(store, source, target, expected, source_expected):
            nonlocal swapped
            if target == 'templates/unit.md' and not swapped:
                swapped = True
                stage = self.project / source
                stage.unlink(); stage.symlink_to(outside)
            return original(store, source, target, expected, source_expected)
        with mock.patch.object(Store, 'publish', publish), self.assertRaises(TransactionError):
            apply_update(self.plan())
        self.assertEqual(outside.read_bytes(), b'synthetic outside source\n')
        self.assertFalse((self.project / 'templates/unit.md').is_symlink())
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), self.original['templates/unit.md'])

    def test_locked_metadata_directory_replacement_stops_writes(self):
        saved = self.root / 'saved-state'
        def swap(event, index=None):
            if event == 'prepared':
                (self.project / '.research-framework').rename(saved)
                (self.project / '.research-framework').mkdir(mode=0o700)
        with mock.patch.object(transactions, '_checkpoint', side_effect=swap), self.assertRaises(TransactionError):
            apply_update(self.plan())
        self.assertFalse(any((self.project / '.research-framework').iterdir()))
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), self.original['templates/unit.md'])

    def test_parent_swap_at_apply_boundary_preserves_new_local_tree(self):
        def swap(event, index=None):
            if event == 'before_write' and index == 0:
                (self.project / 'templates').rename(self.root / 'old-templates')
                put(self.project, 'templates/unit.md', b'new local tree\n')
        with mock.patch.object(transactions, '_checkpoint', side_effect=swap), self.assertRaises(TransactionError):
            apply_update(self.plan())
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), b'new local tree\n')

    def test_rollback_refuses_a_post_update_permission_change(self):
        result = apply_update(self.plan())
        (self.project / 'templates/unit.md').chmod(0o755)
        with self.assertRaises(ValidationError):
            plan_rollback(self.project, result.operation_id)

    def test_hardlink_destination_stale_plan_is_rejected(self):
        plan = self.plan()
        target = self.project / 'templates/unit.md'
        target.rename(self.root / 'outside')
        os.link(self.root / 'outside', target)
        with self.assertRaises(ValidationError):
            apply_update(plan)
        self.assertFalse((self.project / '.research-framework/transactions').exists())

    def test_cross_filesystem_directories_fail_closed(self):
        from types import SimpleNamespace
        with Store(self.project) as store:
            with mock.patch('research_program_framework.storage.os.fstat',
                            return_value=SimpleNamespace(st_dev=store.identity[0] + 1)):
                with self.assertRaises(ValidationError):
                    store._check_directory(store.fd, False)

    def test_reading_dry_run_without_noatime_support_fails_without_writes(self):
        from research_program_framework import paths
        original = paths._directory_flags
        def flags(no_atime=False):
            if no_atime:
                raise ValidationError('Synthetic missing no-atime capability')
            return original(no_atime)
        with mock.patch.object(paths, '_directory_flags', side_effect=flags), self.assertRaises(ValidationError):
            self.plan()
        self.assertFalse((self.project / '.research-framework/transactions').exists())

    def test_interrupt_before_first_write_can_recover_without_payload_change(self):
        operation = self.crash('before_write', 0)
        self.assertEqual((self.project / 'templates/unit.md').read_bytes(), self.original['templates/unit.md'])
        apply_rollback(plan_recovery(self.project, operation))
        self.assertEqual(self.receipt_now(), self.receipt)

    def test_recovery_identifiers_and_forged_plans_are_rejected(self):
        result = apply_update(self.plan())
        for operation in ['../escape', 'a' * 31, '.git/HEAD']:
            with self.subTest(operation=operation), self.assertRaises(ValidationError):
                plan_rollback(self.project, operation)
        recovery = plan_rollback(self.project, result.operation_id)
        with self.assertRaises(ValidationError):
            apply_rollback(replace(recovery, targets=()))

    def test_preparation_failure_does_not_prevent_a_later_valid_update(self):
        original = Store.create
        def fail(store, path, *args, **kwargs):
            if '/backups/' in path:
                raise OSError('synthetic storage exhaustion')
            return original(store, path, *args, **kwargs)
        with mock.patch.object(Store, 'create', fail), self.assertRaises(TransactionError):
            apply_update(self.plan())
        self.assertEqual(apply_update(self.plan()).status, 'COMMITTED')

    def test_interruption_after_durable_commit_requires_explicit_rollback(self):
        def crash(event, index=None):
            if event == 'committed':
                raise Interrupted()
        with mock.patch.object(transactions, '_checkpoint', side_effect=crash), self.assertRaises(Interrupted):
            apply_update(self.plan())
        operation = self.receipt_now()['last_operation']
        with Store(self.project) as store:
            self.assertFalse(pending_operations(store))
        with self.assertRaises(ValidationError):
            plan_recovery(self.project, operation)
        apply_rollback(plan_rollback(self.project, operation))
        self.assertEqual(self.receipt_now(), self.receipt)

    def test_retired_seed_keeps_ownership_even_after_local_deletion(self):
        from research_program_framework.updates import manifest_dict
        old = replace(self.old_release, files=tuple(replace(item, ownership='D', project_owner='C')
                      if item.path == 'templates/unit.md' else item for item in self.old_release.files))
        self.receipt['release'], self.receipt['installed'] = manifest_dict(old), {}
        put(self.project, RECEIPT, encode(self.receipt))
        self.release = self.bundle({'README.md': b'seed\n', 'tools/other.py': b'generic\n'})
        apply_update(self.plan())
        self.assertEqual(self.receipt_now()['project_owned']['templates/unit.md'], 'C')
        (self.project / 'templates/unit.md').unlink()
        self.release = self.bundle({**self.new_files, 'tools/other.py': b'generic\n'}, '1.1.2')
        self.assertIn('templates/unit.md', self.plan().conflicts)
        with self.assertRaises(ValidationError):
            apply_update(self.plan())
        self.assertFalse((self.project / 'templates/unit.md').exists())

    def test_extended_attributes_are_not_silently_discarded(self):
        with mock.patch('research_program_framework.storage.os.listxattr', return_value=['user.synthetic']):
            with self.assertRaises(ValidationError):
                self.plan()
        self.assertFalse((self.project / '.research-framework/transactions').exists())

    def test_nondefault_filesystem_ownership_fails_closed(self):
        from types import SimpleNamespace
        from research_program_framework.storage import _metadata_supported
        for uid, gid in [(os.geteuid() + 1, os.getegid()), (os.geteuid(), os.getegid() + 1)]:
            with self.subTest(uid=uid, gid=gid):
                with mock.patch('research_program_framework.storage.os.fstat',
                                return_value=SimpleNamespace(st_uid=uid, st_gid=gid)):
                    with self.assertRaises(ValidationError):
                        _metadata_supported(0)
