# Framework v1.1 Requirements Traceability

**Date:** 2026-11-14  
**Checkpoint:** Phase 1 documentation only

Sources are the [primary English specification](RESEARCH_PROGRAM_FRAMEWORK_v1.1.md), [Korean companion](RESEARCH_PROGRAM_FRAMEWORK_v1.1_ko.md), the researcher's architecture/migration request and detailed reporting requirements, and the explicit Phase 1 authorization. The [architecture](ARCHITECTURE.md) and [ownership policy](OWNERSHIP_AND_UPDATES.md) record adopted engineering decisions. [Development instructions](../AGENTS.md) enforce the current work boundary.

All requirements below are **specified**, not implemented or runtime-tested in this repository. Validation of documentation does not establish that starter, updater, migration, reporting, or release software works. The v0.5 reference and active project's prior capabilities are evidence for design choices, not an installed v1.1 implementation here.

## 1. Scientific and governance requirements

| ID | Requirement and source | Adopted design / later acceptance evidence |
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

| ID | Requirement and source | Adopted design / later acceptance evidence |
|---|---|---|
| R16 | Methodological depth suitable for manuscript preparation and collaborator/advisor review (approved reporting request; 9–10.3) | Eleven corresponding sections; reader can understand rationale, actual procedures, units, measurements, filters, preprocessing, calculations, controls, uncertainty, exact specifications, evidence construction, results, interpretation, and limits without opening code |
| R17 | No arbitrary report length restriction (approved reporting request; 10) | No target, minimum, maximum, typical-length recommendation, truncation, page-count build gate, typography shrinking, or matching-language-page requirement; page counts informational only |
| R18 | EN/KO Markdown, HTML, PDF and scientific equivalence (10, 10.5) | Six paired outputs; metadata, equations, settings, units, figures/tables, values, claims, and source correspondence; manual semantic review supplements automated comparison |
| R19 | Publication-quality evidence exports (9, 10.1, 10.3) | 600 dpi at intended size, vector PDF/SVG where feasible, Arial 5–7 pt and black non-data text defaults, verified report fonts; journal/legibility/image-integrity exceptions; primary tables supported |
| R20 | Honest actual/historical provenance and reporting scope (10.4, 11) | Planned/default/reconstructed/effective/unknown distinguished; available vs producing revision, relevant dirty-source hashes; reporting-only work does not authorize reruns or provenance investigation |
| R21 | Results versus Interpretation; status versus outcome (9–10.2) | Negative/inconclusive completion accepted; `NOT_EVALUATED` with explanation when no verdict applies; no invented hypothesis or unperformed-work completion |
| R22 | Reliable rendering and revision preservation (10.4–10.5) | Explicit unsupported-math/asset/font failures, disclosed previews, visual HTML/PDF inspection, preserved prior reports/plans, no update-triggered regeneration |

## 3. Engineering requirements added by the architecture/migration request

| ID | Requirement and source | Adopted design / later acceptance evidence |
|---|---|---|
| R23 | Authoritative Git-managed source and versioned starters | One editable source, versioned verified release archives, distinct specification/release/schema versions; no distribution-version confusion |
| R24 | Ownership A/B/C/D and project preservation | Explicit file allowlists, D-to-B/C transition, unknown files preserved, root research instructions/configuration protected; generated installation state distinct from scientific records |
| R25 | Safe new-project initialization | Selected verified release, destination checks, self-contained runtime, empty unadopted planning scaffolds, no fabricated IDs/direction or automatic repository/environment setup |
| R26 | Tracked updates, dry-run, conflict detection, safe merging | Exact upstream and installed hashes, retained ancestors, byte/type-aware three-way decisions; zero-write dry-run, stale-plan detection, unresolved-conflict refusal |
| R27 | Backup, interrupted-operation recovery, guarded rollback | Verified affected-set backups, journals, final state recorded last, post-state guards protecting later edits, no recursive project reset |
| R28 | v0.5 migration without installation metadata | Provenance-recorded observed baseline, conservative unknown-base handling, reviewed ownership adoption, no reorganization or scientific/report regeneration |
| R29 | Automated verification and release management | Synthetic fixtures and failure tests; archive-based initialization/migration/upgrade checks; manual acceptance boundaries; license/reuse and dependency support verified before related release claims |
| R30 | Incremental authorization and read-only references | Phase 1 documentation is approved; its authorized portability follow-up adds local context and an ignore rule only. No Phase 2 files or legacy copies, reference-tree mutations, commit, push, tag, or publication; stop for review |

## 4. Phase 1 change boundary and validation

The approved Phase 1 documentation comprises:

- Updated `RESEARCH_PROGRAM_FRAMEWORK_v1.1.md` and `RESEARCH_PROGRAM_FRAMEWORK_v1.1_ko.md` in this directory.
- New `ARCHITECTURE.md`, `OWNERSHIP_AND_UPDATES.md`, and this traceability document in this directory.
- New repository-root `AGENTS.md` and `README.md`.

The authorized portability follow-up updates development-context references in these shared documents and adds a root `.gitignore` plus `DEVELOPMENT_CONTEXT.local.md`. The latter is checkout-only and Git-excluded. It supplies location facts, not installation metadata or new implementation authorization. Both scientific specifications remain unchanged by this follow-up.

Validation must check:

1. Both specifications preserve all sixteen main sections and align their eleven reporting sections, new reporting subsections, output formats, status/outcome values, governance, and modality coverage.
2. The old length recommendation is removed and no replacement page target or gate is introduced. Informational page counts and scientific readability remain explicit.
3. Relative documentation links resolve, fenced blocks are balanced, and cross-document ownership/phase rules are consistent.
4. The workspace contains the seven approved Markdown documents plus the authorized ignore rule and local context; no future runtime, manifest, baseline, schema, starter, test suite, CI, packaging, or release artifact is created.
5. Protected reference-tree entry metadata remains unchanged across the phase, and no write-capable reference helper or remote/Git mutation was invoked. Reading reference metadata for preservation checks does not validate their scientific contents.
6. Scan both tracked files and nonignored untracked files eligible for commit, so an unborn repository cannot pass portability validation vacuously. No workstation-specific path or local research project name may remain in that candidate set. Verify the local context is ignored, untracked, and explicitly discoverable from the root agent instructions.

Use ephemeral documentation checks rather than adding a future implementation test suite in this phase. Report actual validation results and remaining limits to the researcher, then stop. Runtime acceptance evidence is deferred until its implementation phase is explicitly authorized.
