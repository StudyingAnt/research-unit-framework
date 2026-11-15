import json
from pathlib import Path
import re
import unittest

from support import ROOT, ProjectCase, apply_update
from audit_public import audit


class RepositoryTests(unittest.TestCase):
    def test_one_template_and_no_legacy_infrastructure(self):
        for path in ['compatibility','starter','src','schemas','pyproject.toml']:
            self.assertFalse((ROOT/path).exists(),path)
        manifest=json.loads((ROOT/'template-manifest.json').read_text())
        self.assertEqual(manifest['version'],(ROOT/'VERSION').read_text().strip())
        self.assertIn('coordination/COORDINATION.md',manifest['managed'])
        self.assertNotIn('framework-project.json',manifest['managed'])

    def test_document_links_and_scientific_alignment(self):
        for path in [ROOT/'README.md',*list((ROOT/'docs').glob('*.md'))]:
            for link in re.findall(r'\]\(([^)]+)\)',path.read_text()):
                if '://' in link or link.startswith('#'):
                    continue
                self.assertTrue((path.parent/link.split('#')[0]).exists(),str(path)+': '+link)
        for lang in ['en','ko']:
            text=(ROOT/'template/templates'/('report.'+lang+'.md')).read_text()
            self.assertEqual(len(re.findall(r'<!-- section:',text)),11)
        for suffix in ['', '_ko']:
            text=(ROOT/'docs'/('RESEARCH_PROGRAM_FRAMEWORK_v1.1'+suffix+'.md')).read_text()
            self.assertEqual(len(re.findall(r'^## [0-9]+\.',text,re.M)),16)
            self.assertIn('Coordination',text)

    def test_public_candidate_audit(self):
        self.assertGreater(audit(),0)


class SeedPreservationTests(ProjectCase):
    def test_deleted_project_seeds_not_recreated(self):
        for path in ['PROJECT_INSTRUCTIONS.md','README.md','framework-project.json','coordination/plans/RESEARCH_MAP.md']:
            (self.project/path).unlink()
        self.bump();apply_update(self.plan())
        for path in ['PROJECT_INSTRUCTIONS.md','README.md','framework-project.json','coordination/plans/RESEARCH_MAP.md']:
            self.assertFalse((self.project/path).exists())

    def test_downgrade_refused(self):
        self.bump('2.0.1');apply_update(self.plan());self.bump('2.0.0')
        with self.assertRaisesRegex(ValueError,'Downgrade'):self.plan()
