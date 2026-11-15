import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import unittest

from research_program_framework.manifests import (load_release_manifest, load_legacy_baseline,
    manifest_schema, validate_release_manifest, validate_legacy_baseline, verify_release)
from research_program_framework.paths import ValidationError, validate_payload
from support import PayloadCase, record, release, legacy


class ManifestTests(PayloadCase):
    def test_release_round_trip(self):
        item = self.write()
        value = release([record(ownership='A')])
        manifest = validate_release_manifest(value)
        self.assertEqual(verify_release(self.payload, manifest), (item,))
        path = self.root / 'manifest.json'
        path.write_text(json.dumps(value))
        path.chmod(0o644)
        self.assertEqual(load_release_manifest(path), manifest)

    def test_version_syntax(self):
        for version in ['0.0.0', '1.1.0', '1.1.0-rc.1', '1.1.0+build.9', '1.1.0-0.alpha-1']:
            value = release(); value['framework_version'] = version
            with self.subTest(version=version):
                validate_release_manifest(value)
        for version in ['v1.1.0', '01.1.0', '1.1', '1.1.0-01', '1.1.0-rc..1',
                        '1.1.0+', '1.1.0\n', '1.1.0+' + 'a' * 300]:
            value = release(); value['framework_version'] = version
            with self.subTest(version=version), self.assertRaises(ValidationError):
                validate_release_manifest(value)

    def test_top_level_types_versions_and_unknown_fields(self):
        mutations = [('schema_version', True), ('schema_version', 2), ('schema_version', '1'),
                     ('kind', 'legacy_baseline'), ('framework_version', None),
                     ('specification_version', '1.1.0'), ('source_revision', None),
                     ('source_revision', 'unverified'), ('unknown', 'ignored?')]
        for key, value in mutations:
            data = release(); data[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValidationError):
                validate_release_manifest(data)
        for data in [None, [], 'manifest', {}, {key: value for key, value in release().items() if key != 'files'}]:
            with self.subTest(data=data), self.assertRaises(ValidationError):
                validate_release_manifest(data)
        value = release(); value['source_revision'] = '2' * 64
        validate_release_manifest(value)

    def test_file_types_and_fields(self):
        for key, value in [('path', '../escape'), ('path', None), ('sha256', 'bad'),
                           ('sha256', 'A' * 64), ('size', -1), ('size', True), ('size', 1.5),
                           ('size', 2 ** 53), ('mode', 644), ('mode', '0777'),
                           ('ownership', 'B'), ('ownership', 'C'), ('extra', 1),
                           ('project_owner', 'B')]:
            data = release(); data['files'][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValidationError):
                validate_release_manifest(data)

    def test_file_list_bounds_order_and_collisions(self):
        variants = [None, {}, [], [None], [record(ownership='A')] * 10001,
                    [record('z', ownership='A'), record('a', ownership='A')],
                    [record('a', ownership='A'), record('a', ownership='A')],
                    [record('A/one', ownership='A'), record('a/two', ownership='A')],
                    [record('a', ownership='A'), record('a/b', ownership='A')]]
        for index, files in enumerate(variants):
            value = release(); value['files'] = files
            with self.subTest(index=index), self.assertRaises(ValidationError):
                validate_release_manifest(value)

    def test_project_owned_and_generated_state_rejected(self):
        for path in ['reports/A001-S01-T01/en/report.md', 'analyses/result.csv',
                     'repos/code.py', 'coordination/plans/A001.md',
                     '.research-framework/installation.json', '.research-framework/backups/old',
                     '.research-framework/transactions/op', '.research-framework/baselines/base',
                     '.research-framework/other', '.RESEARCH-FRAMEWORK/policy/AGENTS.md']:
            with self.subTest(path=path), self.assertRaises(ValidationError):
                validate_release_manifest(release([record(path, ownership='A')]))

    def test_root_bridges_and_local_settings_are_seeds(self):
        for path in ['AGENTS.md', 'CLAUDE.md', 'README.md', 'REPORT_TEMPLATE.md',
                     'framework-project.json', 'docs/hpc.md', 'PROJECT_INSTRUCTIONS.md', '.gitattributes']:
            with self.subTest(path=path):
                with self.assertRaises(ValidationError):
                    validate_release_manifest(release([record(path, ownership='A')]))
                validate_release_manifest(release([record(path, ownership='D', project_owner='C')]))

    def test_initialization_owner_rules(self):
        for extra in [{}, {'project_owner': 'A'}, {'project_owner': None}]:
            with self.subTest(extra=extra), self.assertRaises(ValidationError):
                validate_release_manifest(release([record(ownership='D', **extra)]))
        for path in ['data/.gitkeep', 'coordination/plans/RESEARCH_MAP.md',
                     'coordination/plans/ID_REGISTRY.json', 'coordination/manuscripts/.gitkeep']:
            with self.subTest(path=path):
                validate_release_manifest(release([record(path, ownership='D', project_owner='B')]))
                with self.assertRaises(ValidationError):
                    validate_release_manifest(release([record(path, ownership='D', project_owner='C')]))

    def test_common_policy_and_aim_template_allowed(self):
        for path in ['.research-framework/runtime.pyz', '.research-framework/policy/AGENTS.md',
                     '.research-framework/docs/compute.md', 'coordination/plans/AIM_TEMPLATE.md']:
            with self.subTest(path=path):
                validate_release_manifest(release([record(path, ownership='A')]))

    def test_forged_dataclass_revalidated(self):
        manifest = validate_release_manifest(release())
        forged = replace(manifest, files=(replace(manifest.files[0], path='../outside'),))
        with self.assertRaises(ValidationError):
            verify_release(self.payload, forged)

    def test_duplicate_keys_nonfinite_and_invalid_json(self):
        for raw in [b'{"kind":"framework_release","kind":"legacy_baseline"}',
                    b'{"files":[{"size":1,"size":2}]}', b'{"size":NaN}',
                    b'{"size":Infinity}', b'{"size":-Infinity}', b'\xff', b'[]',
                    b'{', b'\xef\xbb\xbf{}', b'[' * 2000 + b']' * 2000]:
            path = self.root / 'manifest.json'
            path.write_bytes(raw); path.chmod(0o644)
            with self.subTest(raw=raw[:50]), self.assertRaises(ValidationError):
                load_release_manifest(path)

    def test_manifest_size_limit(self):
        path = self.root / 'manifest.json'
        path.write_bytes(b' ' * (2 * 1024 * 1024 + 1)); path.chmod(0o644)
        with self.assertRaises(ValidationError):
            load_release_manifest(path)

    def test_manifest_link_rejected(self):
        target = self.root / 'actual.json'
        target.write_text(json.dumps(release()))
        (self.root / 'alias.json').symlink_to(target)
        with self.assertRaises(ValidationError):
            load_release_manifest(self.root / 'alias.json')

    def test_legacy_identity_and_observation(self):
        expected = validate_legacy_baseline(legacy())
        self.assertIsNone(expected.source_revision)
        for key, value in [('framework_version', '3'), ('distribution', 'v0.5'),
                           ('source_revision', '1' * 40), ('content_review', 'not_reviewed'),
                           ('observed_on', '2026-02-30'), ('observed_on', '20261114'),
                           ('schema_version', True), ('kind', 'framework_release')]:
            data = legacy(); data[key] = value
            with self.subTest(key=key), self.assertRaises(ValidationError):
                validate_legacy_baseline(data)
        data = legacy(); data['files'][0]['ownership'] = 'A'
        with self.assertRaises(ValidationError):
            validate_legacy_baseline(data)


class BaselineTests(unittest.TestCase):
    def test_preserved_baseline_inventory_and_fixed_identity(self):
        base = Path(__file__).resolve().parents[1] / 'compatibility/v0.5/starter-v3'
        manifest = load_legacy_baseline(base / 'manifest.json')
        self.assertEqual(len(manifest.files), 22)
        self.assertEqual(sum(item.path.endswith('/.gitkeep') for item in manifest.files), 10)
        self.assertEqual(manifest.framework_version, '0.5')
        self.assertEqual(manifest.distribution, 'Starter v3')
        self.assertIsNone(manifest.source_revision)
        self.assertEqual(len(validate_payload(base / 'payload', manifest.files)), 22)
        # Pin the reviewed complete inventory, not a regenerated expectation.
        self.assertEqual(hashlib.sha256((base / 'manifest.json').read_bytes()).hexdigest(),
                         '13b25f3caf1a494ead8d8cd47a74d9b791e0bf5ddaceaf5cf740fcb985d09a19')


class StructuralSchemaTests(unittest.TestCase):
    def test_schemas_and_cross_validator_contract(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest('Optional JSON Schema cross-check requires jsonschema; core tests use stdlib only')
        root = Path(__file__).resolve().parents[1] / 'schemas'
        for historical, name, good in [(False, 'release-manifest.schema.json', release()),
                                       (True, 'legacy-baseline.schema.json', legacy())]:
            disk = json.loads((root / name).read_text())
            for schema in [disk, manifest_schema(historical)]:
                Draft202012Validator.check_schema(schema)
                checker = Draft202012Validator(schema)
                self.assertTrue(checker.is_valid(good))
                for key, value in [('schema_version', True), ('extra', 'unexpected'), ('files', [])]:
                    invalid = copy.deepcopy(good); invalid[key] = value
                    with self.subTest(historical=historical, key=key):
                        self.assertFalse(checker.is_valid(invalid))
                if not historical:
                    self.assertTrue(checker.is_valid(release([record('README.md', ownership='D', project_owner='C')])))
                    self.assertFalse(checker.is_valid(release([record(ownership='A', project_owner='B')])))
