"""Diagnostics resolve project-relative resources without changing configuration."""

import json
from pathlib import Path
import tempfile
import unittest

from research_program_framework.diagnostics import doctor
from research_program_framework.initialization import create_project
from research_program_framework.release import build


class DiagnosticTests(unittest.TestCase):
    def test_font_presence_uses_project_root_from_any_working_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); project = root / 'project'
            release = build(Path(__file__).resolve().parents[1], root / 'release')
            create_project(project, root / 'release/payload', release)
            config_path = project / 'framework-project.json'
            config = json.loads(config_path.read_text())
            for lang in ('en', 'ko'):
                relative = 'resources/synthetic-font-' + lang + '.ttf'
                # Presence diagnostics do not claim these fixture bytes are a font.
                (project / relative).write_bytes(b'Synthetic presence fixture only.\n')
                config['reporting']['font_' + lang] = relative
            config_path.write_text(json.dumps(config))
            before = config_path.read_bytes()
            self.assertEqual(doctor(project)['font_files_present'], {'en': True, 'ko': True})
            self.assertEqual(config_path.read_bytes(), before)
