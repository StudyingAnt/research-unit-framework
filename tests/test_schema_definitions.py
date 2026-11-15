"""Generated structural schemas supplement the semantic Python validators."""

import json
from pathlib import Path
import unittest

from research_program_framework.schema_definitions import definitions


class SchemaDefinitionTests(unittest.TestCase):
    def test_generated_documents_match_source(self):
        root = Path(__file__).resolve().parents[1]
        for name, schema in definitions().items():
            self.assertEqual(json.loads((root / 'schemas' / (name + '.schema.json')).read_text()), schema)

    def test_schemas_validate_synthetic_records_when_jsonschema_available(self):
        try: import jsonschema
        except ImportError: self.skipTest('Independent optional JSON Schema validator unavailable')
        from test_execution import provenance, run_record
        from test_records import DECISION
        for name, value in [('approval', DECISION), ('provenance', provenance()), ('run', run_record()),
                            ('id-registry', {'schema_version': 1, 'revision': 0, 'records': []})]:
            jsonschema.Draft202012Validator.check_schema(definitions()[name])
            jsonschema.validate(value, definitions()[name])
