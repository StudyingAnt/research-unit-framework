"""Scientific administration requires explicit adoption; examples are synthetic."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research_program_framework.initialization import create_project
from research_program_framework.release import build
from research_program_framework.paths import ValidationError
from research_program_framework.records import (adopt_record, adopt_map, set_links,
    retire_record, resume_record, revise_record, register_existing, read_registry)
from research_program_framework.storage import Store


DECISION = {'by': 'Synthetic Investigator', 'reference': 'Synthetic acceptance approval 001', 'date': '2026-11-14'}
TACTIC = '## Question\n\nDescribe a synthetic measurement.\n\n## Specifications\n\nA table-only demonstration; no experiment is performed.\n'
MANUSCRIPT = '## Claims\n\nUnadopted illustrative claim.\n\n## Supporting Evidence\n\nNone yet.\n\n## Contradictory Evidence\n\nUnknown.\n\n## Limitations\n\nSynthetic only.\n\n## Decisions\n\nApproved administrative demonstration.\n'


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.project = self.root / 'project'
        release = build(Path(__file__).resolve().parents[1], self.root / 'release')
        create_project(self.project, self.root / 'release/payload', release)

    def add(self, kind, body='Synthetic approved scientific purpose.\n', **kwargs):
        return adopt_record(self.project, kind, 'Synthetic ' + kind, body, DECISION, **kwargs)

    def registry(self):
        with Store(self.project) as store: return read_registry(store)[0]

    def test_ast_workstream_and_multiple_manuscript_network(self):
        a1 = self.add('A'); a2 = self.add('A')
        self.assertEqual(a1['state'], 'active')
        w1 = self.add('W', links=[a1['id'], a2['id']]); w2 = self.add('W', links=[a1['id']])
        strategy = self.add('S', parent=a1['id']); tactic = self.add('T', body=TACTIC, parent=strategy['id'])
        m1 = self.add('M', body=MANUSCRIPT, links=[tactic['id']]); m2 = self.add('M', body=MANUSCRIPT, links=[tactic['id']])
        self.assertEqual(tactic['id'], 'A001-S01-T01')
        self.assertEqual(len(self.registry()['records']), 8)
        self.assertFalse((self.project / '.git').exists())

    def test_approval_parent_and_specifications_required(self):
        with self.assertRaises(ValidationError): adopt_record(self.project, 'A', 'Aim', 'body', {})
        with self.assertRaises(ValidationError): self.add('S', parent='A001')
        a = self.add('A'); s = self.add('S', parent=a['id'])
        with self.assertRaises(ValidationError): self.add('T', parent=s['id'])
        with self.assertRaises(ValidationError): self.add('M')

    def test_retirement_and_disk_collision_never_reuse_ids(self):
        a = self.add('A'); retire_record(self.project, a['id'], DECISION, self.registry()['revision'])
        self.assertEqual(self.add('A')['id'], 'A002')
        (self.project / 'reports/A003_existing').mkdir()
        self.assertEqual(self.add('A')['id'], 'A004')
        with self.assertRaises(ValidationError): self.add('A', identity='A001')

    def test_interrupted_registration_resumes_same_id(self):
        def fail(event):
            if event == 'reserved': raise KeyboardInterrupt()
        with patch('research_program_framework.records._checkpoint', fail):
            with self.assertRaises(KeyboardInterrupt): self.add('A')
        with self.assertRaises(ValidationError): self.add('A')
        self.assertEqual(resume_record(self.project, 'A001')['id'], 'A001')
        self.assertEqual(self.add('A')['id'], 'A002')

    def test_approved_revision_preserves_prior_body_and_guards_local_edits(self):
        a = self.add('A'); path = self.project / a['path']; original = path.read_bytes()
        revised = revise_record(self.project, a['id'], '# Synthetic revised objective\n', DECISION, hashlib.sha256(original).hexdigest())
        self.assertEqual(path.read_text(), '# Synthetic revised objective\n')
        archive = self.project / '.research-framework/record-operations/A001'
        self.assertIn(original, [p.read_bytes() for p in archive.glob('*.md')])
        with self.assertRaises(ValidationError): revise_record(self.project, a['id'], 'other', DECISION, hashlib.sha256(original).hexdigest())

    def test_program_revision_creates_no_ast(self):
        path = self.project / 'coordination/plans/RESEARCH_MAP.md'; source = path.read_bytes()
        adopted = source.decode().replace('UNADOPTED SCAFFOLD', 'RESEARCHER-ADOPTED SYNTHETIC DEMONSTRATION')
        result = adopt_map(self.project, adopted, DECISION, hashlib.sha256(source).hexdigest())
        self.assertEqual(self.registry()['records'], [])
        self.assertEqual((self.project / result['revision_record'] / 'before.md').read_bytes(), source)

    def test_many_to_many_links_and_stale_registry(self):
        a = self.add('A'); w = self.add('W')
        revision = self.registry()['revision']
        set_links(self.project, a['id'], [w['id']], DECISION, revision)
        with self.assertRaises(ValidationError): set_links(self.project, a['id'], [], DECISION, revision)

    def test_existing_registration_does_not_rewrite_legacy_record(self):
        path = self.project / 'coordination/plans/A017.md'; path.write_text('# Existing synthetic Aim\n')
        before = path.read_bytes()
        register_existing(self.project, 'A', 'A017', 'coordination/plans/A017.md', 'Existing', DECISION)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.add('A')['id'], 'A001')
