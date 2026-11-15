"""Provenance boundaries, optional Runs, handoffs and human-only HPC preparation."""

import hashlib
from pathlib import Path
import tempfile
import unittest

from research_program_framework.execution import (validate_provenance, validate_run,
    record_run, handoff, validate_launcher, hpc_commands)
from research_program_framework.initialization import create_project
from research_program_framework.release import build
from research_program_framework.records import adopt_record
from research_program_framework.paths import ValidationError
from test_records import DECISION, TACTIC


def provenance():
    return {'category': 'computation', 'verification': 'reconstructed', 'reference': 'synthetic:source-record',
            'description': 'Available source inspected; producing history unknown.', 'producing_revision': None,
            'available_revision': '1'*40, 'dirty_source_hashes': {}}


def run_record():
    return {'schema_version': 1, 'unit_id': 'A001-S01-T01', 'run_id': 'R001', 'status': 'PLANNING',
            'performer': 'Synthetic Operator', 'started_at': None, 'completed_at': None, 'command': None,
            'external_id': None, 'provenance': [provenance()], 'outputs': [],
            'validation': {'expected': [], 'received': [], 'checks': [], 'missing': []}}


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.project = self.root / 'project'
        release = build(Path(__file__).resolve().parents[1], self.root / 'release')
        create_project(self.project, self.root / 'release/payload', release)
        a = adopt_record(self.project, 'A', 'Synthetic Aim', 'Explicit scope.', DECISION)
        s = adopt_record(self.project, 'S', 'Synthetic Strategy', 'Explicit strategy.', DECISION, parent=a['id'])
        self.t = adopt_record(self.project, 'T', 'Synthetic Tactic', TACTIC, DECISION, parent=s['id'])

    def test_available_head_is_not_producing_revision(self):
        value = provenance(); validate_provenance(value)
        value['producing_revision'] = value['available_revision']
        with self.assertRaises(ValidationError): validate_provenance(value)

    def test_optional_run_and_later_resume_keep_identity(self):
        value = run_record(); result = record_run(self.project, value, DECISION)
        value['status'] = 'WAITING'; value['external_id'] = 'synthetic-acquisition-17'
        updated = record_run(self.project, value, expected_sha256=result['sha256'])
        self.assertEqual(updated['path'], result['path'])
        (self.project / result['path']).unlink()
        with self.assertRaises(ValidationError): record_run(self.project, value, DECISION)

    def test_false_completion_and_unvalidated_required_output_rejected(self):
        value = run_record(); value['status'] = 'COMPLETED'
        with self.assertRaises(ValidationError): validate_run(value)
        value.update(started_at='2026-11-14T12:00:00Z', completed_at='2026-11-14T12:01:00Z')
        value['validation']['missing'] = ['required evidence']
        with self.assertRaises(ValidationError): validate_run(value)

    def test_waiting_handoff_durable_and_same_id(self):
        value = {'schema_version': 1, 'unit_id': self.t['id'], 'resume_id': self.t['id'], 'status': 'WAITING',
            'approved_scope_reference': DECISION['reference'], 'known_execution_ids': ['synthetic-run-1'],
            'evidence_received': [], 'evidence_missing': ['operator output'], 'expected_outputs': ['synthetic table'],
            'next_human_step': 'Return the actual acquisition log for inspection.', 'updated_at': '2026-11-14T12:00:00Z'}
        result = handoff(self.project, value)
        self.assertEqual(result['resume_id'], self.t['id'])
        with self.assertRaises(ValidationError): handoff(self.project, value)
        value['resume_id'] = 'A001-S01-T02'
        with self.assertRaises(ValidationError): handoff(self.project, value)

    def test_launcher_order_and_job_internal_conda_setup(self):
        valid = '#!/bin/bash\n#SBATCH --mem=1G\nset -euo pipefail\nmodule load verified-module\neval "$(conda shell.bash hook)"\nconda activate /verified/existing/environment\npython analysis.py\n'
        self.assertTrue(validate_launcher(valid)['validated'])
        for invalid in (valid.replace('#SBATCH --mem=1G\n', '')+'#SBATCH --mem=1G\n', valid.replace('conda activate /verified/existing/environment','conda activate named-env'), valid.replace('module load verified-module\n',''), valid+'pip install package\n'):
            with self.assertRaises(ValidationError): validate_launcher(invalid)

    def test_hpc_commands_separate_operations_and_never_activate_login_conda(self):
        path = self.project / 'repos/analysis/stage/job.slurm'; path.parent.mkdir(parents=True)
        path.write_text('#!/bin/bash\n#SBATCH --mem=1G\nset -euo pipefail\npython stage.py\n')
        config = {'verified': True, 'evidence_reference': 'Synthetic verified command-preparation fixture',
            'remote_host': 'operator@synthetic.invalid', 'remote_repository': '/synthetic/repos/analysis',
            'working_directory': '/synthetic/repos/analysis/stage', 'launcher': 'job.slurm',
            'local_launcher': 'repos/analysis/stage/job.slurm', 'remote_outputs': '/synthetic/results',
            'local_destination': str(self.project / 'analyses'), 'slurm_available': True, 'slurm_module': None, 'job_id': None}
        result = hpc_commands(self.project, config)
        self.assertNotIn('accounting', result)
        self.assertNotIn('conda', result['submit']); self.assertNotIn('module', result['submit'])
        self.assertIn('stage', result['submit']); self.assertNotIn('--delete', result['retrieve'])
        self.assertTrue(result['human_operated'])
