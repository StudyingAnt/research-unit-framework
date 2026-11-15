import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from support import ProjectCase, ROOT, contents
from new_unit import create_unit
from build_reports import validate_report, render_report
from report_support import UNIT_ID, sources, figure


class ReportChecks(ProjectCase):
    def setUp(self):
        super().setUp()
        create_unit(self.project,'Synthetic evidence',approved_by='Synthetic fixture approval')
        self.report = sources(self.project)

    def test_table_only_completed_not_evaluated(self):
        self.assertTrue(validate_report(self.project,UNIT_ID))
        self.assertEqual(validate_report(self.project,UNIT_ID)['metadata']['outcome'],'NOT_EVALUATED')

    def test_missing_section_or_placeholder_refused(self):
        p=self.report/'en/report.md';p.write_text(p.read_text().replace('<!-- section: methods -->',''))
        with self.assertRaisesRegex(ValueError,'eleven'):validate_report(self.project,UNIT_ID)
        sources(self.project);p.write_text(p.read_text()+'\n{{UNRESOLVED}}\n')
        with self.assertRaisesRegex(ValueError,'placeholder'):validate_report(self.project,UNIT_ID)

    def test_numeric_or_metadata_mismatch_refused(self):
        p=self.report/'ko/report.md';p.write_text(p.read_text().replace('2.5','2.6'))
        with self.assertRaisesRegex(ValueError,'numeric'):validate_report(self.project,UNIT_ID)
        sources(self.project);p.write_text(p.read_text().replace('**Status:** COMPLETED','**Status:** WAITING'))
        with self.assertRaisesRegex(ValueError,'metadata mismatch'):validate_report(self.project,UNIT_ID)

    def test_outcome_reason_and_review_reference_required(self):
        p=self.report/'report.json';d=json.loads(p.read_text());d['outcome_reason']='';p.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'reason'):validate_report(self.project,UNIT_ID)
        d['outcome_reason']='No scientific verdict';d['review']['references']=[];p.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'review references'):validate_report(self.project,UNIT_ID)

    def test_check_is_read_only_and_sources_not_auto_adopted(self):
        before=contents(self.project)
        p=subprocess.run([sys.executable,'-B',str(self.project/'tools/build_reports.py'),UNIT_ID,'--check'],cwd='/tmp',capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(contents(self.project),before)

    def test_no_page_restriction_on_deep_methods(self):
        sources(self.project,methods_repeat=20)
        self.assertTrue(validate_report(self.project,UNIT_ID))


@unittest.skipUnless(os.environ.get('RPF_RENDER_TESTS')=='1','Optional real renderer acceptance; set RPF_RENDER_TESTS=1')
class RenderTests(ProjectCase):
    def setUp(self):
        super().setUp()
        create_unit(self.project,'Synthetic evidence',approved_by='Synthetic fixture approval')
        self.report = sources(self.project)
        config=self.project/'framework-project.json';value=json.loads(config.read_text())
        for setting,variable in [('pandoc','RPF_PANDOC'),('font_en','RPF_FONT_EN'),('font_ko','RPF_FONT_KO')]:
            if os.environ.get(variable):value['reporting'][setting]=os.environ[variable]
        config.write_text(json.dumps(value))

    def test_six_outputs_revision_history_and_figure_size(self):
        figure(self.project)
        result=render_report(self.project,UNIT_ID)
        self.assertEqual(len(result['files']),6)
        for lang in ['en','ko']:
            self.assertTrue((self.report/lang/'report.pdf').read_bytes().startswith(b'%PDF'))
            self.assertIn('width:85mm',(self.report/lang/'report.html').read_text())
        old=contents(self.report/'revisions/REV001')
        with self.assertRaisesRegex(ValueError,'already exists'):render_report(self.project,UNIT_ID)
        sources(self.project,revision='REV002');render_report(self.project,UNIT_ID)
        self.assertEqual(contents(self.report/'revisions/REV001'),old)
        self.assertEqual(json.loads((self.report/'current.json').read_text())['revision'],'REV002')
        self.assertEqual(len(json.loads((self.project/'coordination/plans/ID_REGISTRY.json').read_text())['units']),1)

    def test_missing_font_has_no_published_outputs(self):
        p=self.project/'framework-project.json';d=json.loads(p.read_text());d['reporting']['font_ko']=str(self.root/'missing.ttf');p.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'font'):render_report(self.project,UNIT_ID)
        self.assertFalse((self.report/'revisions').exists())

    def test_preview_isolated_from_final_revisions(self):
        result=render_report(self.project,UNIT_ID,preview=True)
        self.assertTrue(result['preview']);self.assertIn('/previews/',result['revision_directory'])
        self.assertFalse((self.report/'en/report.pdf').exists())
        self.assertFalse((self.report/'revisions').exists())

    def test_unsupported_math_and_raw_html_refused(self):
        p=self.report/'en/report.md';p.write_text(p.read_text()+'\n$\\unsupportedcommand{x}$\n')
        with self.assertRaisesRegex(ValueError,'Unsupported mathematical'):render_report(self.project,UNIT_ID)
        sources(self.project);p.write_text(p.read_text()+'\n<script>alert("synthetic")</script>\n')
        with self.assertRaisesRegex(ValueError,'Raw HTML'):render_report(self.project,UNIT_ID)
        self.assertFalse((self.report/'revisions').exists())

    def test_low_dpi_image_refused(self):
        figure(self.project)
        from PIL import Image
        p=self.project/'analyses'/UNIT_ID/'figures/synthetic.png'
        with Image.open(p) as image:image.save(p.with_name('low.png'),dpi=(100,100))
        p.write_bytes(p.with_name('low.png').read_bytes())
        with self.assertRaisesRegex(ValueError,'600 dpi'):validate_report(self.project,UNIT_ID)

    def test_unarchived_local_output_preserved(self):
        render_report(self.project,UNIT_ID)
        output=self.report/'en/report.pdf';output.write_bytes(output.read_bytes()+b'\nSynthetic local annotation\n')
        local=output.read_bytes();sources(self.project,revision='REV002')
        with self.assertRaisesRegex(ValueError,'unarchived local changes'):render_report(self.project,UNIT_ID)
        self.assertEqual(output.read_bytes(),local)
        self.assertFalse((self.report/'revisions/REV002').exists())
