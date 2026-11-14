"""Strict version-one release definitions and observed legacy inventories.

Validation is read-only and offline. Digests verify integrity, not publisher
authenticity, scientific appropriateness, or authorization to install a file.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import re
from typing import Optional

from .paths import (FileFingerprint, ValidationError, read_payload_file,
                    validate_path_set, validate_payload)


SCHEMA_VERSION = 1
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_FILES = 10000
MAX_SIZE = 2 ** 53 - 1
SHA256_PATTERN = r"[0-9a-f]{64}"
REVISION_PATTERN = r"(?:[0-9a-f]{40}|[0-9a-f]{64})"
_NUMBER = r"(?:0|[1-9][0-9]*)"
_PRE = r"(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
VERSION_PATTERN = rf"{_NUMBER}\.{_NUMBER}\.{_NUMBER}(?:-{_PRE}(?:\.{_PRE})*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"


@dataclass(frozen=True)
class ReleaseFile(FileFingerprint):
    ownership: str
    project_owner: Optional[str] = None


@dataclass(frozen=True)
class ReleaseManifest:
    schema_version: int
    kind: str
    framework_version: str
    specification_version: str
    source_revision: str
    files: tuple[ReleaseFile, ...]


@dataclass(frozen=True)
class LegacyBaseline:
    schema_version: int
    kind: str
    framework_version: str
    distribution: str
    observed_on: str
    source_revision: None
    content_review: str
    files: tuple[FileFingerprint, ...]


def _object(value, required: set[str], optional: set[str] = frozenset()) -> dict:
    if type(value) is not dict or set(value) - required - optional or required - set(value):
        raise ValidationError("Manifest object has missing, unknown, or invalid fields")
    return value


def _string(value, pattern: str) -> str:
    if type(value) is not str or len(value) > 256 or not re.fullmatch(pattern, value, flags=re.ASCII):
        raise ValidationError("Manifest string has an unsupported value or syntax")
    return value


def _header(value, fields: set[str], kind: str) -> dict:
    data = _object(value, fields)
    if type(data['schema_version']) is not int or data['schema_version'] != SCHEMA_VERSION:
        raise ValidationError("Unsupported manifest schema version")
    if data['kind'] != kind:
        raise ValidationError("Manifest kind does not match the requested validator")
    return data


def _file(value, release: bool) -> FileFingerprint:
    required = {'path', 'size', 'sha256', 'mode'}
    if release:
        required.add('ownership')
    data = _object(value, required, {'project_owner'} if release else set())
    if type(data['size']) is not int or not 0 <= data['size'] <= MAX_SIZE:
        raise ValidationError("Manifest file size must be a bounded nonnegative integer")
    _string(data['sha256'], SHA256_PATTERN)
    _string(data['mode'], r"(?:0644|0755)")
    if not release:
        return FileFingerprint(**data)
    ownership = data['ownership']
    if ownership not in ('A', 'D'):
        raise ValidationError("Release payload can contain only managed files or initialization seeds")
    if ownership == 'A' and 'project_owner' in data:
        raise ValidationError("Managed payload must not claim project ownership")
    if ownership == 'D' and data.get('project_owner') not in ('B', 'C'):
        raise ValidationError("Initialization seed must name its subsequent project owner")
    return ReleaseFile(**data)


def _files(value, release: bool) -> tuple[FileFingerprint, ...]:
    if type(value) is not list or not 1 <= len(value) <= MAX_FILES:
        raise ValidationError("Manifest requires a bounded nonempty file list")
    files = tuple(_file(item, release) for item in value)
    paths = validate_path_set(item.path for item in files)
    if paths != tuple(sorted(paths)):
        raise ValidationError("Manifest file list must be sorted by canonical path")
    if release:
        for item in files:
            _release_role(item)
    return files


def _release_role(item: ReleaseFile) -> None:
    """Protect scientific records and generated state; this is not an updater."""
    parts = item.path.split('/')
    seeds = {
        'AGENTS.md', 'CLAUDE.md', 'REPORT_TEMPLATE.md', 'README.md',
        'PROJECT_INSTRUCTIONS.md', 'framework-project.json', '.gitignore',
        'docs/figure_style.md', 'docs/compute.md', 'docs/hpc.md',
    }
    scientific_roots = {'analyses', 'reports', 'data', 'resources', 'envs', 'notes', 'repos', 'coordination'}
    scientific_seeds = {'coordination/plans/RESEARCH_MAP.md', 'coordination/plans/ID_REGISTRY.json'}
    template = 'coordination/plans/AIM_TEMPLATE.md'
    path = item.path
    # Case aliases cannot bypass role restrictions even on a case-sensitive host.
    folded = path.casefold()
    if parts[0].casefold() == '.research-framework':
        if item.ownership != 'A' or not (
            path == '.research-framework/runtime.pyz'
            or path.startswith('.research-framework/policy/')
            or path.startswith('.research-framework/docs/')
        ):
            raise ValidationError("Release cannot supply generated installation state or unknown private paths")
    if folded in {seed.casefold() for seed in seeds} and item.ownership != 'D':
        raise ValidationError("Root instructions and project settings must be initialization-only seeds")
    if parts[0].casefold() in scientific_roots:
        if path == template and item.ownership == 'A':
            return
        marker = len(parts) == 2 and parts[-1] == '.gitkeep'
        coordination_marker = (path in {'coordination/manuscripts/.gitkeep',
                                       'coordination/presentations/.gitkeep',
                                       'coordination/revisions/.gitkeep'})
        if item.ownership != 'D' or not (path in scientific_seeds or marker or coordination_marker):
            raise ValidationError("Release payload must not contain project-owned scientific records")
        if item.project_owner != 'B':
            raise ValidationError("Scientific scaffold must become project-owned")


def validate_release_manifest(value) -> ReleaseManifest:
    """Parse a strict release definition without inspecting or mutating a project."""
    data = _header(value, {'schema_version', 'kind', 'framework_version',
                          'specification_version', 'source_revision', 'files'}, 'framework_release')
    _string(data['framework_version'], VERSION_PATTERN)
    _string(data['specification_version'], rf"{_NUMBER}\.{_NUMBER}")
    _string(data['source_revision'], REVISION_PATTERN)
    return ReleaseManifest(**{**data, 'files': _files(data['files'], release=True)})


def validate_legacy_baseline(value) -> LegacyBaseline:
    """Validate an observed inventory, without claiming a historical release SHA."""
    data = _header(value, {'schema_version', 'kind', 'framework_version', 'distribution',
                          'observed_on', 'source_revision', 'content_review', 'files'}, 'legacy_baseline')
    if (data['framework_version'] != '0.5' or data['distribution'] != 'Starter v3'
            or data['source_revision'] is not None
            or data['content_review'] != 'reviewed_generic'):
        raise ValidationError("Unsupported legacy identity or unreviewed content")
    _string(data['observed_on'], r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
    try:
        date.fromisoformat(data['observed_on'])
    except ValueError as exc:
        raise ValidationError("Legacy observation date is invalid") from exc
    return LegacyBaseline(**{**data, 'files': _files(data['files'], release=False)})


def _unique_object(pairs) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("Duplicate JSON object key")
        result[key] = value
    return result


def _constant(value):
    raise ValidationError("Non-finite JSON numbers are not accepted")


def _load(path: Path):
    path = Path(path)
    raw = read_payload_file(path.parent, path.name, MAX_MANIFEST_BYTES)
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object, parse_constant=_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValidationError("Invalid manifest JSON") from exc


def load_release_manifest(path: Path) -> ReleaseManifest:
    return validate_release_manifest(_load(path))


def load_legacy_baseline(path: Path) -> LegacyBaseline:
    return validate_legacy_baseline(_load(path))


def verify_release(root: Path, manifest: ReleaseManifest) -> tuple[FileFingerprint, ...]:
    """Check manifest structure again, then verify a separate payload directory."""
    if not isinstance(manifest, ReleaseManifest):
        raise ValidationError("A validated release manifest is required")
    # Frozen instances still can be constructed by callers without a parser.
    from dataclasses import asdict
    data = asdict(manifest)
    data['files'] = [dict(item) for item in data['files']]
    for item in data['files']:
        if item['project_owner'] is None:
            del item['project_owner']
    validated = validate_release_manifest(data)
    return validate_payload(root, validated.files)


def manifest_schema(legacy: bool = False) -> dict:
    """Generate the structural JSON Schema; semantic path/role checks remain required."""
    file_properties = {
        'path': {'type': 'string', 'minLength': 1, 'maxLength': 4096,
                 'pattern': r'^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$'},
        'sha256': {'type': 'string', 'pattern': f'^{SHA256_PATTERN}$'},
        'size': {'type': 'integer', 'minimum': 0, 'maximum': MAX_SIZE},
        'mode': {'enum': ['0644', '0755']},
    }
    file_schema = {'type': 'object', 'additionalProperties': False,
                   'required': list(file_properties), 'properties': file_properties}
    properties = {'schema_version': {'type': 'integer', 'const': SCHEMA_VERSION},
                  'kind': {'const': 'legacy_baseline' if legacy else 'framework_release'}}
    if legacy:
        properties.update({
            'framework_version': {'const': '0.5'}, 'distribution': {'const': 'Starter v3'},
            'observed_on': {'type': 'string', 'pattern': r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$'},
            'source_revision': {'type': 'null'}, 'content_review': {'const': 'reviewed_generic'},
        })
    else:
        properties.update({
            'framework_version': {'type': 'string', 'maxLength': 256, 'pattern': f'^{VERSION_PATTERN}$'},
            'specification_version': {'type': 'string', 'maxLength': 256, 'pattern': rf'^{_NUMBER}\.{_NUMBER}$'},
            'source_revision': {'type': 'string', 'pattern': f'^{REVISION_PATTERN}$'},
        })
        file_schema['required'].append('ownership')
        file_properties.update({'ownership': {'enum': ['A', 'D']},
                                'project_owner': {'enum': ['B', 'C']}})
        file_schema['oneOf'] = [
            {'properties': {'ownership': {'const': 'A'}}, 'not': {'required': ['project_owner']}},
            {'properties': {'ownership': {'const': 'D'}}, 'required': ['project_owner']},
        ]
    properties['files'] = {'type': 'array', 'minItems': 1, 'maxItems': MAX_FILES, 'items': file_schema}
    return {'$schema': 'https://json-schema.org/draft/2020-12/schema',
            'title': 'Observed v0.5 baseline' if legacy else 'Framework release manifest',
            'description': 'Structural definition only; framework semantic and filesystem validation is also required.',
            'type': 'object', 'additionalProperties': False, 'required': list(properties),
            'properties': properties}
