import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from support import ProjectCase, ROOT, contents, create_project
from new_unit import create_unit


class CreationTests(ProjectCase):
    def test_visible_complete_template(self):
        for path in ['AGENTS.md','CLAUDE.md','PROJECT_INSTRUCTIONS.md','REPORT_TEMPLATE.md',
                     'coordination/COORDINATION.md','coordination/plans/RESEARCH_MAP.md',
                     'analyses','reports','repos','data','resources','envs','notes','templates','tools']:
            self.assertTrue((self.project / path).exists(), path)
        self.assertFalse((self.project / '.git').exists())
        self.assertFalse((self.project / '.research-framework').exists())
        state = json.loads((self.project / '.framework/manifest.json').read_text())
        self.assertEqual(state['version'], '2.0.0')
        self.assertEqual(json.loads((self.project / 'coordination/plans/ID_REGISTRY.json').read_text())['units'], {})

    def test_existing_destination_never_overlaid(self):
        before = contents(self.project)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            create_project(self.project, self.source)
        self.assertEqual(contents(self.project), before)

    def test_default_coordination_and_durable_files(self):
        rules = (self.project / 'AGENTS.md').read_text()
        policy = (self.project / 'coordination/COORDINATION.md').read_text()
        for token in ['Coordination', 'explicit', 'researcher', 'persistent', 'AST']:
            self.assertIn(token, rules)
        for token in ['hypotheses', 'alternatives', 'priorities', 'approval', 'no required', 'reports']:
            self.assertIn(token, policy)
        self.assertIn('UNADOPTED', (self.project / 'coordination/plans/RESEARCH_MAP.md').read_text())

    def test_configured_parent_and_explicit_destination(self):
        env = {**os.environ, 'XDG_CONFIG_HOME': str(self.root / 'config')}
        env.pop('RPF_PROJECTS_DIR', None)
        parent = self.root / 'configured'
        result = subprocess.run([sys.executable, '-B', str(ROOT/'newproj'), '--configure', str(parent)], env=env, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        for args, destination in [(['alpha'], parent/'alpha'), (['beta','--destination',str(self.root/'elsewhere')], self.root/'elsewhere')]:
            result = subprocess.run([sys.executable, '-B', str(ROOT/'newproj'), *args], env=env, cwd='/tmp', capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((destination / 'AGENTS.md').is_file())

    def test_template_symlink_rejected(self):
        (self.source/'template/tools/link.py').symlink_to(self.root/'outside')
        with self.assertRaisesRegex(ValueError, 'Symbolic'):
            create_project(self.root/'another',self.source)

    def test_standalone_unit_helper_and_stable_ids(self):
        result = subprocess.run([sys.executable,'-B',str(self.project/'tools/new_unit.py'),'Synthetic task','--approved-by','Synthetic allocation approval'],cwd='/tmp',capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['unit_id'],'A001-S01-T01')
        first = contents(self.project/'reports/A001-S01-T01')
        self.assertEqual(create_unit(self.project,'Second synthetic task',approved_by='Synthetic approval')['unit_id'],'A001-S01-T02')
        self.assertEqual(contents(self.project/'reports/A001-S01-T01'),first)
        before = contents(self.project)
        resumed = subprocess.run([sys.executable,'-B',str(self.project/'tools/new_unit.py'),'--resume','A001-S01-T01'],cwd='/tmp',capture_output=True)
        self.assertEqual(resumed.returncode,0,resumed.stderr)
        self.assertEqual(contents(self.project),before)

    def test_approval_and_existing_id_protection(self):
        with self.assertRaisesRegex(ValueError,'approval'):
            create_unit(self.project,'Synthetic')
        create_unit(self.project,'Synthetic',approved_by='Synthetic')
        with self.assertRaises(ValueError):
            create_unit(self.project,'Reuse',approved_by='Synthetic',unit_id='A001-S01-T01')

    def test_occupied_and_retired_ids_not_recycled(self):
        registry = self.project/'coordination/plans/ID_REGISTRY.json'
        registry.write_text(json.dumps({'format':1,'units':{'A001-S01-T05':{'state':'retired'}}}))
        (self.project/'reports/A001-S01-T08_other').mkdir()
        self.assertEqual(create_unit(self.project,'Synthetic',approved_by='Synthetic')['unit_id'],'A001-S01-T09')

    def test_identity_capacity_and_distinct_strategy(self):
        (self.project/'analyses/A001-S01-T99').mkdir()
        with self.assertRaisesRegex(ValueError,'capacity'):
            create_unit(self.project,'Synthetic',approved_by='Synthetic')
        self.assertEqual(create_unit(self.project,'Synthetic',strategy='S02',approved_by='Synthetic')['unit_id'],'A001-S02-T01')

    def test_interrupted_creation_keeps_reserved_identity(self):
        from new_unit import write
        def fail(root,path,*args,**kwargs):
            if path.endswith('/en/report.md'):raise OSError('Synthetic copy interruption')
            return write(root,path,*args,**kwargs)
        with patch('new_unit.write',side_effect=fail),self.assertRaisesRegex(OSError,'interruption'):
            create_unit(self.project,'Synthetic',approved_by='Synthetic')
        registry=json.loads((self.project/'coordination/plans/ID_REGISTRY.json').read_text())
        self.assertEqual(registry['units']['A001-S01-T01']['state'],'reserved')
        self.assertEqual(create_unit(self.project,'Another distinct fixture',approved_by='Synthetic')['unit_id'],'A001-S01-T02')
