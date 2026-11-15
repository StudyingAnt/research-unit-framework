import json
import os
from pathlib import Path
import stat
from unittest.mock import patch

from support import ProjectCase, contents, apply_update
from project_common import read


class UpdateTests(ProjectCase):
    PATH = 'templates/report.en.md'

    def test_preview_has_no_side_effects(self):
        self.source_file(self.PATH,b'Synthetic new template\n');self.bump()
        before = contents(self.project)
        tokens = {str(p):p.lstat() for p in self.project.rglob('*')}
        self.assertFalse(self.plan().describe()['conflicts'])
        self.assertEqual(contents(self.project),before)
        for p, token in tokens.items():
            current=Path(p).lstat()
            self.assertEqual((token.st_ino,token.st_mode,token.st_size,token.st_mtime_ns,token.st_ctime_ns),
                             (current.st_ino,current.st_mode,current.st_size,current.st_mtime_ns,current.st_ctime_ns))
        self.assertFalse((self.project/'.framework/lock').exists())

    def test_pristine_update_and_verified_backup(self):
        before = (self.project/self.PATH).read_bytes()
        self.source_file(self.PATH,b'Updated generic template\n');self.bump()
        result=apply_update(self.plan())
        self.assertEqual((self.project/self.PATH).read_bytes(),b'Updated generic template\n')
        backup=Path(result['backup'])
        self.assertEqual((backup/'before'/self.PATH).read_bytes(),before)
        self.assertEqual(json.loads((backup/'previous-manifest.json').read_text())['version'],'2.0.0')
        self.assertEqual(result['version'],'2.0.1')
        self.assertIsNone(apply_update(self.plan())['backup'])

    def test_preserve_local_change_and_deletion(self):
        (self.project/self.PATH).write_bytes(b'Locally improved template\n')
        (self.project/'tools/report.css').unlink()
        self.bump(); result=apply_update(self.plan())
        self.assertEqual((self.project/self.PATH).read_bytes(),b'Locally improved template\n')
        self.assertFalse((self.project/'tools/report.css').exists())
        self.assertNotIn(self.PATH,result['changed'])

    def custom_base(self):
        # Introduce a synthetic tracked tool through an ordinary update.
        self.add_managed('tools/synthetic.py',b'one\ntwo\nthree\nfour\n');self.bump()
        apply_update(self.plan())

    def test_disjoint_three_way_merge_and_official_base(self):
        self.custom_base();path='tools/synthetic.py'
        (self.project/path).write_bytes(b'LOCAL\ntwo\nthree\nfour\n')
        incoming=b'one\ntwo\nthree\nUPSTREAM\n';self.source_file(path,incoming);self.bump('2.0.2')
        plan=self.plan();self.assertEqual(next(a for a in plan.actions if a['path']==path)['action'],'MERGE')
        apply_update(plan)
        self.assertEqual((self.project/path).read_bytes(),b'LOCAL\ntwo\nthree\nUPSTREAM\n')
        state=json.loads((self.project/'.framework/manifest.json').read_text())
        self.assertEqual((self.project/'.framework/base'/state['files'][path]['sha256']).read_bytes(),incoming)

    def test_conflict_blocks_entire_apply(self):
        self.custom_base();path='tools/synthetic.py'
        (self.project/path).write_bytes(b'LOCAL\n');self.source_file(path,b'INCOMING\n');self.bump('2.0.2')
        self.source_file(self.PATH,b'Unrelated incoming update\n')
        before=contents(self.project);plan=self.plan()
        self.assertIn(path,plan.describe()['conflicts'])
        with self.assertRaisesRegex(ValueError,'conflicts'):apply_update(plan)
        self.assertEqual(contents(self.project),before)

    def test_explicit_resolution(self):
        self.custom_base();path='tools/synthetic.py'
        (self.project/path).write_bytes(b'LOCAL\n');self.source_file(path,b'INCOMING\n')
        merged=b'Explicit combined local and incoming behavior\n'
        plan=self.plan(resolutions={path:merged});self.assertFalse(plan.describe()['conflicts'])
        apply_update(plan);self.assertEqual((self.project/path).read_bytes(),merged)

    def test_binary_delete_change_and_marker_conflicts(self):
        self.custom_base();path='tools/synthetic.py'
        (self.project/path).write_bytes(b'\0LOCAL');self.source_file(path,b'\0INCOMING')
        self.assertIn(path,self.plan().describe()['conflicts'])
        with self.assertRaisesRegex(ValueError,'conflict markers'):
            self.plan(resolutions={path:b'<<<<<<< local\nUnresolved\n>>>>>>> upstream\n'})
        (self.project/path).unlink()
        self.assertIn(path,self.plan().describe()['conflicts'])

    def test_unmanaged_collision_and_scientific_targets(self):
        (self.project/'tools/private.py').write_bytes(b'local content\n')
        self.add_managed('tools/private.py',b'local content\n')
        self.assertIn('tools/private.py',self.plan().describe()['conflicts'])
        with self.assertRaisesRegex(ValueError,'unmanaged'):
            self.plan(resolutions={'tools/private.py':b'replace'})
        self.add_managed('reports/scientific.md',b'Forbidden\n')
        with self.assertRaisesRegex(ValueError,'cannot be framework-managed'):self.plan()

    def test_seed_science_and_git_preservation(self):
        paths=['framework-project.json','PROJECT_INSTRUCTIONS.md','coordination/plans/RESEARCH_MAP.md',
               'coordination/plans/A001.md','reports/scientific.md','analyses/results.tsv','repos/example/.git/HEAD',
               'data/synthetic.tsv','notes/proposal.md','tools/unmanaged.py']
        for path in paths:
            p=self.project/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'Synthetic protected local bytes\n')
        self.source_file(self.PATH,b'Updated\n');self.bump();apply_update(self.plan())
        for path in paths:self.assertEqual((self.project/path).read_bytes(),b'Synthetic protected local bytes\n')

    def test_stale_local_or_source_plan(self):
        self.source_file(self.PATH,b'Incoming\n');plan=self.plan()
        (self.project/self.PATH).write_bytes(b'Intervening work\n')
        with self.assertRaisesRegex(ValueError,'Stale'):apply_update(plan)
        (self.project/self.PATH).write_bytes((self.source/'template'/self.PATH).read_bytes())
        plan=self.plan();self.source_file('tools/report.css',b'New source\n')
        with self.assertRaisesRegex(ValueError,'Stale'):apply_update(plan)

    def test_wrong_reviewed_digest(self):
        with self.assertRaisesRegex(ValueError,'reviewed'):apply_update(self.plan(),'wrong')

    def test_unsafe_link_and_hardlink_refusal(self):
        outside=self.root/'outside';outside.write_bytes(b'Preserve external\n')
        p=self.project/self.PATH;p.unlink();p.symlink_to(outside)
        with self.assertRaisesRegex(ValueError,'Symbolic'):self.plan()
        p.unlink();os.link(outside,p)
        with self.assertRaisesRegex(ValueError,'single-link'):self.plan()
        self.assertEqual(outside.read_bytes(),b'Preserve external\n')

    def test_corrupt_baseline_and_old_installation_refused(self):
        state=self.project/'.framework/manifest.json';value=json.loads(state.read_text())
        (self.project/'.framework/base'/value['files'][self.PATH]['sha256']).write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'corrupt'):self.plan()
        value['format']=1;state.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'new baseline'):self.plan()

    def test_delete_pristine_but_keep_modified_on_conflict(self):
        self.custom_base();manifest=self.source/'template-manifest.json';value=json.loads(manifest.read_text())
        value['managed'].remove('tools/synthetic.py');manifest.write_text(json.dumps(value))
        (self.source/'template/tools/synthetic.py').unlink()
        apply_update(self.plan());self.assertFalse((self.project/'tools/synthetic.py').exists())

    def test_relinquished_file_becomes_project_owned(self):
        self.custom_base();manifest=self.source/'template-manifest.json';value=json.loads(manifest.read_text())
        value['managed'].remove('tools/synthetic.py');manifest.write_text(json.dumps(value))
        local=b'Locally improved scientific helper\n';(self.project/'tools/synthetic.py').write_bytes(local)
        apply_update(self.plan())
        self.assertEqual((self.project/'tools/synthetic.py').read_bytes(),local)
        self.assertNotIn('tools/synthetic.py',json.loads((self.project/'.framework/manifest.json').read_text())['files'])

    def test_interrupted_update_retains_usable_ancestor_and_backup(self):
        self.source_file(self.PATH,b'Incoming\n');self.source_file('tools/report.css',b'New css\n');self.bump()
        from _framework import write
        def fail(root,path,*args,**kwargs):
            if path=='tools/report.css':raise OSError('Synthetic write interruption')
            return write(root,path,*args,**kwargs)
        with patch('_framework.write',side_effect=fail), self.assertRaisesRegex(OSError,'interruption'):
            apply_update(self.plan())
        self.assertEqual(json.loads((self.project/'.framework/manifest.json').read_text())['version'],'2.0.0')
        self.assertTrue(list((self.project/'.framework/backups').glob('*/previous-manifest.json')))
        self.assertFalse(self.plan().describe()['conflicts'])
        apply_update(self.plan())
        self.assertEqual((self.project/'tools/report.css').read_bytes(),b'New css\n')

    def test_backup_failure_prevents_managed_modification(self):
        self.source_file(self.PATH,b'Incoming\n');original=(self.project/self.PATH).read_bytes()
        from _framework import write
        def fail(root,path,*args,**kwargs):
            if '/before/' in path:raise OSError('Synthetic backup failure')
            return write(root,path,*args,**kwargs)
        with patch('_framework.write',side_effect=fail), self.assertRaisesRegex(OSError,'backup'):
            apply_update(self.plan())
        self.assertEqual((self.project/self.PATH).read_bytes(),original)
