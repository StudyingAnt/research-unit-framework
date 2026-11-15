# Framework v1.1 Requirements Traceability

**Date:** 2026-11-14  
**Checkpoint:** Framework v1.1 implementation and acceptance

Sources are the [primary English specification](RESEARCH_PROGRAM_FRAMEWORK_v1.1.md), [Korean companion](RESEARCH_PROGRAM_FRAMEWORK_v1.1_ko.md), the researcher's architecture/migration request and detailed reporting requirements, and the autonomous authorization for Phases 3 through 10. The [architecture](ARCHITECTURE.md) and [ownership policy](OWNERSHIP_AND_UPDATES.md) record adopted engineering decisions. [Development instructions](../AGENTS.md) enforce the current work boundary.

All requirements below are specified and implemented with the evidence and limits below. Phase 2 delivered the reviewed baseline and validators; Phases 3–9 add guarded updates/recovery, standalone starters, initialization, conservative v0.5 migration, researcher-adopted scientific records, detailed bilingual reporting, handoffs and release acceptance. The active reference is not considered migrated merely because this repository is implemented. Final deployment/release status is recorded separately.

## 1. Scientific and governance requirements

| ID | Requirement and source | Implemented design / acceptance evidence |
|---|---|---|
| R01 | Researcher controls direction, priorities, consequential choices, adopted claims, and publication (specification sections 1, 7, 13) | Explicit decision rights and dated adopted changes; agent cannot adopt a proposal from successful execution |
| R02 | Narrative separates question, hypothesis, observation, inference, alternative, synthesis (2.1, 6) | Research Map and revision records preserve epistemic categories and researcher approval |
| R03 | Flexible Workstreams and many-to-many Aim associations (2.2, 3) | Synthetic cross-linked Workstreams/Aims; no mandatory modality or assay taxonomy |
| R04 | Aim/Strategy/Tactic and material Specifications (2.3–2.4, 9) | Approved scoped plans, applicable parameters/protocols/controls; no fabricated irrelevant fields |
| R05 | Optional execution Runs independent of report revisions (2.4, 4, 10.4) | Multiple or no Runs within a Tactic; distinct report revision and execution identity |
| R06 | Stable AST IDs and scientifically appropriate boundaries (4) | Collision and registration checks, no ID reuse or renumbering, no automatic identifier-width expansion |
| R07 | Research Map and program planning records (6) | Researcher-owned Narrative, priorities, gaps, dependencies, and dated approved changes; no auto-generated scientific backlog |
| R08 | Manuscript-level evidence integration independent of AST (2.5, 6.3) | Claims link evidence and limitations, including contradictions; evidence can support multiple manuscripts without ID changes |
| R09 | Program discussion, review, and synthesis without forced AST; same-ID resume (8) | Planning-only and review scenarios create no unit; interrupted/deferred handoff resumes the existing one |
| R10 | Experimental, computational, theoretical, observational, hybrid work (1–2, 9, 14–16) | Synthetic modality coverage, including code-free experimental evidence and hybrid source linkage |
| R11 | Protected primary systems and qualified human activities (5.1, 7.1, 9, 11) | Authorized protocol/sample/acquisition/ELN/LIMS references, no restricted data copied into generic/public artifacts |
| R12 | Independent scientific repositories and existing layouts (5, 11, 15) | No mandatory root Git, submodules, code relocation, or packaging of analysis scripts; portable documented inputs |
| R13 | Human-operated HPC and resumable evidence handoffs (7–9, user instructions and HPC policy) | Separate pull/submit/monitor/retrieve steps, verified paths, same-unit destination mapping, actual returned evidence; no login Conda requirement, job-internal Conda setup retained |
| R14 | Cross-agent and human continuity (8, 12, 16) | Durable shared records plus explicit root-policy loading; actual compatibility pilots, no proprietary-memory authority |
| R15 | No automatic scientific scope expansion (7, 9, 13) | Completion does not initiate another unit, strategic revision, or manuscript; new action needs authorized scope |

## 2. Reporting requirements

| ID | Requirement and source | Implemented design / acceptance evidence |
|---|---|---|
| R16 | Methodological depth suitable for manuscript preparation and collaborator/advisor review (approved reporting request; 9–10.3) | Eleven corresponding sections; reader can understand rationale, actual procedures, units, measurements, filters, preprocessing, calculations, controls, uncertainty, exact specifications, evidence construction, results, interpretation, and limits without opening code |
| R17 | No arbitrary report length restriction (approved reporting request; 10) | No target, minimum, maximum, typical-length recommendation, truncation, page-count build gate, typography shrinking, or matching-language-page requirement; page counts informational only |
| R18 | EN/KO Markdown, HTML, PDF and scientific equivalence (10, 10.5) | Six paired outputs; metadata, equations, settings, units, figures/tables, values, claims, and source correspondence; manual semantic review supplements automated comparison |
| R19 | Publication-quality evidence exports (9, 10.1, 10.3) | 600 dpi at intended size, vector PDF/SVG where feasible, Arial 5–7 pt and black non-data text defaults, verified report fonts; journal/legibility/image-integrity exceptions; primary tables supported |
| R20 | Honest actual/historical provenance and reporting scope (10.4, 11) | Planned/default/reconstructed/effective/unknown distinguished; available vs producing revision, relevant dirty-source hashes; reporting-only work does not authorize reruns or provenance investigation |
| R21 | Results versus Interpretation; status versus outcome (9–10.2) | Negative/inconclusive completion accepted; `NOT_EVALUATED` with explanation when no verdict applies; no invented hypothesis or unperformed-work completion |
| R22 | Reliable rendering and revision preservation (10.4–10.5) | Explicit unsupported-math/asset/font failures, disclosed previews, visual HTML/PDF inspection, preserved prior reports/plans, no update-triggered regeneration |

## 3. Engineering requirements added by the architecture/migration request

| ID | Requirement and source | Implemented design / acceptance evidence |
|---|---|---|
| R23 | Authoritative Git-managed source and versioned starters | One editable source, versioned verified release archives, distinct specification/release/schema versions; no distribution-version confusion |
| R24 | Ownership A/B/C/D and project preservation | Explicit file allowlists, D-to-B/C transition, unknown files preserved, root research instructions/configuration protected; generated installation state distinct from scientific records |
| R25 | Safe new-project initialization | Selected verified release, destination checks, self-contained runtime, empty unadopted planning scaffolds, no fabricated IDs/direction or automatic repository/environment setup |
| R26 | Tracked updates, dry-run, conflict detection, safe merging | Exact upstream and installed hashes, retained ancestors, byte/type-aware three-way decisions; zero-write dry-run, stale-plan detection, unresolved-conflict refusal |
| R27 | Backup, interrupted-operation recovery, guarded rollback | Verified affected-set backups, journals, final state recorded last, post-state guards protecting later edits, no recursive project reset |
| R28 | v0.5 migration without installation metadata | Provenance-recorded observed baseline, conservative unknown-base handling, reviewed ownership adoption, no reorganization or scientific/report regeneration |
| R29 | Automated verification and release management | Synthetic fixtures and failure tests; archive-based initialization/migration/upgrade checks; manual acceptance boundaries; license/reuse and dependency support verified before related release claims |
| R30 | Incremental authorization and read-only references | Autonomous Phases 3–10 authorization; original reference remains read-only, active target changes only in the final validated migration. Logical commits and privacy-reviewed pushes are authorized; no forced history changes or premature final release |

## 4. Phase 1 change boundary and validation

The approved Phase 1 documentation comprises:

- Updated `RESEARCH_PROGRAM_FRAMEWORK_v1.1.md` and `RESEARCH_PROGRAM_FRAMEWORK_v1.1_ko.md` in this directory.
- New `ARCHITECTURE.md`, `OWNERSHIP_AND_UPDATES.md`, and this traceability document in this directory.
- New repository-root `AGENTS.md` and `README.md`.

The authorized portability follow-up updates development-context references in these shared documents and adds a root `.gitignore` plus `DEVELOPMENT_CONTEXT.local.md`. The latter is checkout-only and Git-excluded. It supplies location facts, not installation metadata or new implementation authorization. Both scientific specifications remain unchanged by this follow-up.

The Phase 1 validation checks were:

1. Both specifications preserve all sixteen main sections and align their eleven reporting sections, new reporting subsections, output formats, status/outcome values, governance, and modality coverage.
2. The old length recommendation is removed and no replacement page target or gate is introduced. Informational page counts and scientific readability remain explicit.
3. Relative documentation links resolve, fenced blocks are balanced, and cross-document ownership/phase rules are consistent.
4. The workspace contains the seven approved Markdown documents plus the authorized ignore rule and local context; no future runtime, manifest, baseline, schema, starter, test suite, CI, packaging, or release artifact is created.
5. Protected reference-tree entry metadata remains unchanged across the phase, and no write-capable reference helper or remote/Git mutation was invoked. Reading reference metadata for preservation checks does not validate their scientific contents.
6. Scan both tracked files and nonignored untracked files eligible for commit, so an unborn repository cannot pass portability validation vacuously. No workstation-specific path or local research project name may remain in that candidate set. Verify the local context is ignored, untracked, and explicitly discoverable from the root agent instructions.

These remain historical Phase 1 evidence, not a prohibition on the subsequently authorized Phase 2 components. Scientific specifications and their requirements remain unchanged in Phase 2.

## 5. Phase 2 implementation and evidence

| Requirement subset | Implemented evidence | Limit |
|---|---|---|
| R23, R28: observed legacy source | Exact 22-file baseline, reviewed content, SHA-256/size/mode inventory, pinned manifest digest, integrity test | Unknown historical revision remains null; no migration |
| R24, R26: release definition and ownership | Versioned strict manifest parser, structural schemas, A managed/D seed roles, root/scientific/generated-state protections | No installation receipts, merge plans, or update engine |
| R26: secure path/file inspection | Portable canonical names, alias/prefix checks, descriptor-based no-follow reads, single-link regular files, exact bounded inventory/hash/mode checks, observed-change detection | Linux/WSL read-only verification; no archive extraction or future-write safety claim |
| R29: component tests | Synthetic temporary projects, malformed input and filesystem/race cases, observed baseline integrity, optional independent JSON Schema check | No end-to-end installer/update/migration/rollback, rendering, or release validation |
| R30: authorization and privacy | Root phase instructions updated; local context remains Git-excluded, protected references read-only, no active-project content copied | Stop after Phase 2; no commit/push or Phase 3 |

See [manifest and path validation](MANIFESTS_AND_PATHS.md) for the format and historical Phase 2 result: 40 tests, 39 passing and one sandbox-restricted socket test skipped. Socket-type rejection was separately tested. The phase-specific limits above describe that checkpoint; Phase 3 adds the following capabilities.

## 6. Phase 3 implementation and evidence

| Requirement subset | Implemented evidence | Limit |
|---|---|---|
| R24, R26: ownership and planning | In-memory B/L/N plans, content/mode comparison, disjoint line merging, unresolved-conflict refusal, explicit registered-file resolutions, immutable D seeds, unmanaged-collision and ownership-transition rejection | Existing registered canonical paths only; no configuration rewriting, layout remapping, initialization, or metadata-free adoption |
| R26: dry-run and stale-plan checks | No-atime descriptor reads, exact payload revalidation, immutable plans bound to root/receipt/file/parent/source state, fresh-plan recomputation under lock | Linux/WSL with sufficient no-atime permissions; no global snapshot guarantee |
| R27: backup, journal, and failure recovery | Verified complete backups and after-images, durable per-file intent/results, exact new upstream objects, receipt finalized last, automatic guarded recovery on ordinary failure, explicit interruption recovery | Single filesystem, trusted manager state and cooperating writers; corrupt/unknown states require inspection |
| R27: guarded rollback | Whole affected-set preflight, later edit/mode/identity checks, protected operation-added files/directories, resumable restoration, receipt restored last, proven child-rollback lineage | No force overwrite, recursive reset, backup pruning, or scientific-record recovery |
| R29: tests | 103 combined tests: 102 pass, one sandbox-restricted actual socket test skipped; synthetic conflict, interruption, retired-seed ownership, backup/stage tampering, path/metadata replacement, rollback/local-edit, and no-atime cases | No real deployment or power-loss/hardware durability certification; unsupported ownership/ACL/xattrs fail closed; socket-type rejection separately covered |
| R30: scope and preservation | Phase instructions updated, scientific specifications and observed baseline unchanged, protected references remain read-only | Subsequent phases proceed under the autonomous completion authorization |

The [update engine contract](UPDATE_ENGINE.md) documents the exact API, consumed receipt format, tests, and remaining platform/concurrency limits. Later scientific and deployment requirements are authorized and remain pending implementation at this checkpoint.

## 7. Complete implementation evidence

The earlier sections retain historical phase evidence. This table supersedes
their old implementation limits for current capability claims.

| Requirements | Current implementation and observed evidence | Practical boundary |
|---|---|---|
| R01–R04, R07, R15 | `records.py`, scientific starter policy and Research Map/Aim templates; explicit approval references, preserved map/record revisions, epistemic categories and material Specifications | Validators do not authenticate approval or decide methodological adequacy; scientific adoption remains human |
| R03, R08 | Many-to-many W–A links and independent M–T evidence associations; manuscript Claims/Supporting Evidence/Contradictory Evidence/Limitations/Decisions; network tests | A link alone does not establish support or adopt an interpretation |
| R05–R06, R09 | Non-recycled bounded registry, existing-path collision discovery, retire/revise/register-existing, pending reservation and same-ID resume, optional R### separate from REV###; interruption tests | Ambiguous legacy identity conventions/capacity exhaustion need an explicit inspected decision |
| R10–R12 | Archive-only creation of experimental/computational/theoretical/observational/hybrid records; no Run/code/Git requirement; configurable scientific paths and primary-system references | No real experiment, restricted-data access or scientific repository change is performed by administration |
| R13–R14 | Shared explicit agent-policy bridges, durable scoped handoffs, actual/missing execution evidence, launcher validation and separate human-operated pull/submit/monitor/retrieve commands | Actual vendor loader behavior, remote resources/imports and institutional permissions require appropriate human checks |
| R16–R18, R21 | Eleven-section detailed EN/KO templates, actual paired MD/HTML/PDF, no page gate, table-only completion, outcome reason, scalar/metadata/math comparisons; full renderer tests | Scientific/bilingual meaning is explicitly reviewed rather than inferred from structure or scalar agreement |
| R19–R20, R22 | Actual Noto/Arial fonts, 600 dpi PNG and PDF/SVG exports, intended physical width, glyph/asset/math failures, honest provenance categories, verified producing/available distinctions, retained report revisions and guarded publication recovery | MathText subset, external font licensing, manual figure/scientific review; no historical regeneration or speculative rerun |
| R23–R25 | Single editable source, deterministic runtime/release payload, strict A/D manifests and persistent B/C ownership, no-clobber fresh creation, empty unadopted records, archive-only execution | Linux/WSL supported administration; no mandatory scientific packaging/root Git or environment provisioning |
| R26–R28 | Zero-write plans, B/L/N comparison and explicit resolutions, stale/unsafe-path/conflict refusal, verified backups, durable journals, guarded update/migration rollback, external metadata-free adoption recovery | Trusted administrative state/cooperating writers; unsupported ACLs/xattrs/ownership/filesystems fail closed |
| R29–R30 | Complete 155-test renderer-enabled run: 154 pass, one sandbox-restricted socket creation skipped; Python 3.9/3.11 GitHub CI success; archive-only tests; public/history/archive audits; corrected HTML/PDF visual review | Final tag/assets and active-target status must be observed separately; publication grants no invented license |

See [acceptance evidence](ACCEPTANCE.md) for actual environments, visual review,
unperformed real-world activities and release/deployment status. No unsupported
scientific judgment, institutional activity, full TeX engine or universal agent/
cluster certification is silently represented as implemented automation.
