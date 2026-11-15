# Phase 2 Manifest and Path Validation

**Status:** Phase 2 validation primitives retained; Phase 3 update/recovery operations are documented separately  
**Contracts:** [Architecture](ARCHITECTURE.md), [ownership policy](OWNERSHIP_AND_UPDATES.md), [requirements traceability](REQUIREMENTS_TRACEABILITY.md)

## 1. Definitions and authority

The single source package is `src/research_program_framework/`. It uses the Python standard library. `manifests.py` defines immutable parsed records, strict JSON loaders, semantic release validation, legacy inventory validation, and structural schema generation. `paths.py` performs portable-name checks and descriptor-relative, read-only file/inventory verification. No payload code is executed.

The generated structural definitions are [release manifest schema](../schemas/release-manifest.schema.json) and [legacy baseline schema](../schemas/legacy-baseline.schema.json). Regenerate them from `manifest_schema()` when their format changes. JSON Schema alone does not enforce path aliases, ownership locations, sorted inventory, actual file identity, or content review; the Python semantic and filesystem validators are required as well.

All objects reject unknown/missing fields. JSON loading rejects duplicate object keys at any depth, non-finite numbers, malformed UTF-8, invalid JSON, and excessive document size. Schema version is the integer `1`, not a boolean or numeric string. Manifests are UTF-8 JSON in regular single-link files with supported modes.

| Field | Framework release | Observed legacy baseline |
|---|---|---|
| `schema_version` | `1` | `1` |
| `kind` | `framework_release` | `legacy_baseline` |
| `framework_version` | Canonical three-part version with optional prerelease/build identifiers | `0.5` |
| `specification_version` | Separate two-part specification version | Not claimed for a historical design |
| `source_revision` | Lowercase full 40- or 64-digit hexadecimal Git object ID | Null: no historical producing revision established |
| `distribution` | Not a field | `Starter v3` |
| `observed_on` | Not a field | Valid calendar date in ISO form |
| `content_review` | No automated safety attestation | `reviewed_generic`, recording the prior human/agent content review |
| `files` | Sorted, nonempty list of release file records | Sorted, nonempty list of observed fingerprints |

Each fingerprint has a canonical relative `path`, nonnegative integer byte `size`, lowercase `sha256`, and `mode` (`0644` or `0755`). Release files additionally specify ownership `A` or `D`. D seeds must name their subsequent `project_owner` (`B` or `C`); A files cannot claim project ownership. B scientific records and C local settings are never shipped as managed replacements. Root instructions/configuration are seeds; generated installation state and actual scientific record locations are rejected. This is format/role validation, not update or migration application.

Hashes establish integrity relative to the selected manifest, not publisher authenticity or permission to install. A syntactically valid source ID is not proof that the commit exists or that a release is compatible with a project. Review labels cannot automatically establish that arbitrary future content is safe to publish. These checks do not choose a scientific outcome or inspect scientific validity.

## 2. Names and read-only filesystem checks

Payload paths use portable ASCII letters, digits, underscore, hyphen, dot, and POSIX separators. Reject absolute, drive/UNC, backslash, colon, control/non-ASCII, empty/dot/parent components, trailing dots/spaces, device names, Git/control directories, and the private development-context filename. Detect case aliases in every component, duplicate files, and file/directory prefix conflicts. This restriction applies to framework payload filenames; it does not rename or restrict researchers' input paths or Korean report contents.

Filesystem inspection on Linux/WSL opens every root and parent component with directory descriptors and no-follow flags. Reject symlinked roots/ancestors, symlink files, hard-linked files, FIFOs, sockets, other special files, and unsupported permission modes. Compare the named entry with the opened descriptor, hash bounded bytes, and check identity/size/mode/timestamps before and after reading. Verify the exact file and parent-directory inventory, including a second metadata inventory after hashing. Unexpected entries stop inspection instead of causing traversal of unrelated trees. Reads do not create caches, locks, backups, or metadata and do not extract or run archived helpers.

Format/resource bounds are explicit: at most 10,000 files per manifest, 2 MiB of manifest JSON, 256 characters for version identifiers, 4,096 characters per relative path, 255 per component, and 128 components. Byte sizes are integers up to `2**53 - 1`; booleans and floats are invalid. Filesystem verification defaults to at most 64 MiB per file and 256 MiB total, with explicit caller-supplied limits available. These are payload validation bounds, not scientific-report length restrictions.

Verification is an observed, read-only check, not a globally atomic snapshot of an actively hostile filesystem. It detects tested link replacements, in-read modifications, and changes to an earlier file during later hashes. Phase 3 reuses these primitives and revalidates at mutation boundaries; [the engine contract](UPDATE_ENGINE.md) defines those operations. No-atime file/directory reads now suppress access-time changes and fail closed when unsupported or denied. Archive extraction, trusted signature verification, environment setup, initialization, and v0.5 migration remain unimplemented.

## 3. API and validation workflow

For a future bundle with a manifest outside its payload directory, the read-only sequence is:

```python
from pathlib import Path
from research_program_framework.manifests import load_release_manifest, verify_release

manifest = load_release_manifest(Path("bundle/release-manifest.json"))
verified_files = verify_release(Path("bundle/payload"), manifest)
```

These are illustrative paths, not a shipped bundle or CLI command. `validate_release_manifest()` accepts an already decoded object. `verify_release()` rechecks even a manually constructed record before examining payload files. `load_legacy_baseline()` validates observed provenance separately; `validate_payload()` can check its fingerprints without assigning install/update ownership.

The preserved baseline is documented [here](../compatibility/v0.5/starter-v3/README.md). It has 22 byte/mode-verified files. Its full inventory manifest digest is pinned in an integrity test. Historical page restrictions and old helper behavior are retained as inert evidence, not adopted as current policy. No active-project content or workstation-specific source paths are included.

## 4. Automated verification

From the development repository root:

```sh
PYTHONPATH=src python3 -B -m unittest discover -s tests -v
```

The source import path is for development tests only; it creates no installation and imposes no import-path convention on scientific projects. `-B` avoids bytecode cache creation, including in the legacy snapshot. All mutation fixtures use temporary synthetic directories. The preserved baseline is read only for integrity checks; local development context and protected reference projects are not test dependencies.

The core suite needs only the standard library. When `jsonschema` is already available, an optional test independently checks both structural schemas and valid/invalid examples using its Draft 2020-12 validator; otherwise that cross-check is explicitly skipped. Do not install dependencies automatically.

At the Phase 2 checkpoint the suite had 40 tests: 39 passed and 1 actual AF_UNIX socket test was skipped because the execution sandbox rejects `bind`. A separate socket-metadata rejection test passed; actual FIFO, symlink/hardlink, case/prefix collision, permission, hash/inventory, malformed JSON, resource-limit, and observed-race cases ran. These tests remain in the current combined suite described in [the engine contract](UPDATE_ENGINE.md). The environment remains Python 3.9.18 without configuration changes; this is not a release-wide compatibility matrix.

Remaining release questions include license/reuse terms, publisher trust and compatibility policy, and later archive/initialization/migration behavior. Phase 3 implements guarded registered-installation recovery, not a release or metadata-free migration.
