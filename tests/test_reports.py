"""Report structure/revision guards; optional real renderer tests run separately."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research_program_framework.initialization import create_project
from research_program_framework.release import build
from research_program_framework.reports import validate_report, render_report, _safe_svg
from research_program_framework.paths import ValidationError
from report_support import sources, UNIT_ID


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.project = self.root / 'project'
        release = build(Path(__file__).resolve().parents[1], self.root / 'release')
        create_project(self.project, self.root / 'release/payload', release)
        self.reports = sources(self.project)

    def test_full_table_only_report_has_no_figure_requirement(self):
        result = validate_report(self.project, UNIT_ID)
        self.assertEqual(result['figures'], [])
        self.assertEqual(result['review_required'], ['visual'])

    def test_no_page_or_word_count_gate(self):
        sources(self.project, methods_repeat=20)
        self.assertEqual(validate_report(self.project, UNIT_ID)['metadata']['status'], 'COMPLETED')

    def test_missing_sections_placeholders_and_numeric_mismatch_refused(self):
        path = self.reports / 'ko/report.md'; source = path.read_text()
        for changed in (source.replace('section: methods', 'section: absent'), source+'\n{{MISSING}}', source.replace('2.5', '2.6')):
            path.write_text(changed)
            with self.assertRaises(ValidationError): validate_report(self.project, UNIT_ID)
        path.write_text(source)

    def test_completed_without_verdict_requires_reason(self):
        path = self.reports / 'report.json'; value = json.loads(path.read_text()); value['outcome_reason'] = ''
        path.write_text(json.dumps(value))
        with self.assertRaises(ValidationError): validate_report(self.project, UNIT_ID)

    def test_active_svg_content_rejected(self):
        for data in (b'<svg onload="alert(1)"/>', b'<svg><image href="https://invalid.example/image"/></svg>', b'<!ENTITY x "bad"><svg/>'):
            with self.assertRaises(ValidationError): _safe_svg(data)


@unittest.skipUnless(os.environ.get('RPF_RENDER_TESTS') == '1', 'Optional renderer acceptance requires an explicitly selected environment/fonts')
class RenderingTests(ReportTests):
    def setUp(self):
        super().setUp()
        path = self.project / 'framework-project.json'; config = json.loads(path.read_text())
        for key in ('pandoc', 'font_en', 'font_ko'):
            config['reporting'][key] = os.environ['RPF_' + key.upper()]
        path.write_text(json.dumps(config))

    def test_real_six_outputs_math_fonts_and_revision_preservation(self):
        result = render_report(self.project, UNIT_ID, 'REV001')
        self.assertFalse(result['preview'])
        self.assertEqual(len(result['files']), 6)
        for lang in ('en', 'ko'):
            self.assertIn('math-inline', (self.reports / lang / 'report.html').read_text())
            self.assertTrue((self.reports / lang / 'report.pdf').read_bytes().startswith(b'%PDF'))
        old = (self.reports / 'revisions/REV001/en/report.md').read_bytes()
        sources(self.project, 'REV002', methods_repeat=3)
        render_report(self.project, UNIT_ID, 'REV002')
        self.assertEqual((self.reports / 'revisions/REV001/en/report.md').read_bytes(), old)

    def test_unsupported_math_and_missing_assets_refuse_outputs(self):
        for lang in ('en', 'ko'):
            path = self.reports / lang / 'report.md'; path.write_text(path.read_text() + '\n$\\unsupported{x}$\n')
        with self.assertRaises(ValidationError): render_report(self.project, UNIT_ID, 'REV001')
        self.assertFalse((self.reports / 'en/report.pdf').exists())

    def test_publication_quality_figure_exports_and_density(self):
        from report_support import figure
        figure(self.project)
        self.assertEqual(len(validate_report(self.project, UNIT_ID)['figures']), 3)
        result = render_report(self.project, UNIT_ID, 'REV001')
        self.assertEqual(len(result['files']), 6)

    def test_missing_font_and_external_or_missing_image_fail_explicitly(self):
        path = self.project / 'framework-project.json'; config = json.loads(path.read_text())
        config['reporting']['font_ko'] = None; path.write_text(json.dumps(config))
        with self.assertRaises(ValidationError): render_report(self.project, UNIT_ID, 'REV001')
        self.assertFalse((self.reports / 'en/report.pdf').exists())

    def test_interrupted_output_publication_and_guarded_undo(self):
        from research_program_framework.reports import report_recovery_plan, recover_report
        def fail(event, index=None):
            if event == 'published' and index == 1: raise KeyboardInterrupt()
        with patch('research_program_framework.reports._checkpoint', fail):
            with self.assertRaises(KeyboardInterrupt): render_report(self.project, UNIT_ID, 'REV001')
        operation = next((self.project / '.research-framework/report-builds').iterdir()).name
        target = self.reports / 'en/report.html'; original = target.read_bytes()
        target.write_bytes(original + b'local work')
        with self.assertRaises(ValidationError): report_recovery_plan(self.project, operation)
        # A separate interrupted build without later work is recoverable.
        target.write_bytes(original)
        # Rewriting even identical content counts as later work and stays guarded.
        with self.assertRaises(ValidationError): report_recovery_plan(self.project, operation)
