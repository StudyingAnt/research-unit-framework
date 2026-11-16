"""Isolated synthetic projects; no real scientific content or reference writes."""
from pathlib import Path
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'template/tools'))
from _framework import create_project, plan_update, apply_update
from project_common import encode


def contents(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


class ProjectCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='rpf-v2-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        shutil.copytree(ROOT / 'template', self.source / 'template', ignore=shutil.ignore_patterns('__pycache__'))
        # Version-transition tests start at a fixed synthetic version, independent
        # of the current release number. This is not a historical template copy.
        manifest = json.loads((ROOT / 'template-manifest.json').read_text())
        manifest['version'] = '2.0.0'
        (self.source / 'template-manifest.json').write_bytes(encode(manifest))
        self.project = self.root / 'project'
        create_project(self.project, self.source)

    def source_file(self, path, content):
        p = self.source / 'template' / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)

    def bump(self, version='2.0.1'):
        p = self.source / 'template-manifest.json'
        value = json.loads(p.read_text()); value['version'] = version; p.write_bytes(encode(value))

    def add_managed(self, path, content):
        self.source_file(path, content)
        p = self.source / 'template-manifest.json'
        value = json.loads(p.read_text()); value['managed'].append(path); p.write_bytes(encode(value))

    def plan(self, **kwargs):
        return plan_update(self.project, self.source, **kwargs)
