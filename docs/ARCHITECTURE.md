# Framework v1.1 Architecture

**Decision date:** 2026-11-14  
**Status:** Implemented v1.1 framework; acceptance and release procedure documented
**Scientific authority:** [Primary specification](RESEARCH_PROGRAM_FRAMEWORK_v1.1.md), with [Korean companion](RESEARCH_PROGRAM_FRAMEWORK_v1.1_ko.md)

This document records the approved architecture. The implementation follows these boundaries; acceptance evidence and practical limits are recorded separately. [Ownership and updates](OWNERSHIP_AND_UPDATES.md) is the normative mutation contract; [requirements traceability](REQUIREMENTS_TRACEABILITY.md) identifies later acceptance evidence.

## 1. Boundaries and sources of authority

Separate three contexts:

| Context | Authority | Boundary |
|---|---|---|
| Framework development repository | Specifications, framework source, starter source, schemas, tests, release definitions | Contains generic material only; root agent instructions govern framework development |
| Versioned release | Immutable source revision, starter payload, bundled runtime, file manifest, checksums | Records exactly what can be installed; no dependency on a mutable development checkout |
| Installed scientific project | Approved scientific records, local instructions/configuration, independent repositories, installed framework receipt | Retains its identity, layout, data, primary systems, Git histories, and scientific ownership |

Resolve the development checkout root from the active workspace. Record its workstation-specific root, protected reference locations, and external policy-manual paths only in the root `DEVELOPMENT_CONTEXT.local.md`, excluded by `.gitignore`. Agents explicitly discover and read it through the root development instructions; it is not assumed to load automatically. Missing local context does not authorize guessing paths or performing dependent operations. Reference trees designated by the researcher or local context remain strictly read-only. Phase 1 created no snapshot; Phase 2 preserves only the reviewed generic legacy baseline in this development repository and installs nothing into the references.

The primary English specification controls scientific and governance semantics. Its Korean companion must remain aligned. Explicit researcher instructions control adopted changes and authorized execution. Architecture approval alone does not authorize later phases, project migration, or publication.

## 2. Development repository structure

The target source tree is:

```text
research-unit-framework/
├── AGENTS.md                         # Development instructions
├── README.md
├── VERSION                           # Future implementation release version
├── CHANGELOG.md
├── pyproject.toml                    # Framework tooling only
├── docs/                             # Specifications and engineering contracts
├── src/research_program_framework/   # Single framework runtime source
├── schemas/                          # Release, installation, operation, and record validation
├── starter/                          # Single maintained starter source
├── compatibility/v0.5/starter-v3/     # Future observed legacy baseline and provenance
├── tests/                            # Synthetic project fixtures and acceptance tests
├── requirements/                     # Development/reporting dependencies
└── .github/workflows/                # Future verification and artifact builds
```

Phase 2 added the reviewed historical baseline, validators, schemas, and tests. Phase 3 adds update planning/merging, descriptor-anchored storage, journaled application, recovery, rollback, and synthetic integration tests. Phases 4–9 add the starter/runtime, initialization, conservative migration, scientific records, bilingual reporting, handoffs, schemas, archive acceptance and release automation. The local context is checkout-only developer information, not framework installation metadata or release payload. Shared documents and release artifacts contain generic policies without workstation-specific paths or local research project names. Keep generated artifacts separate from editable source.

Maintain one editable starter source. A tagged source revision and its verified release archives define a versioned starter; do not maintain independently edited copies for every release. Compatibility snapshots are immutable migration ancestors with recorded provenance, not alternative current starters. Starter v3 is a distribution name; its framework version is v0.5.

## 3. Runtime and delivery

Use a Python framework CLI with a runtime built from the single source package. Release builds will bundle that runtime as a Python zip application, `runtime.pyz`, and ship the starter payload, schemas, release manifest, and checksums. Generated runtime archives are build products, not another editable source copy. Select and record supported interpreter/dependency versions through later validation; Core administration is tested on Python 3.9 and 3.11 on Linux/WSL; optional rendering has a separately observed environment.

The installed runtime resides at `.research-framework/runtime.pyz`. Thin project helpers retain familiar unit-creation and report-building entry points, delegate to that runtime, and resolve the actual project root explicitly. They must work independently of the development checkout and must not depend on private workstation paths.

The CLI responsibilities are initialization, inspection/diagnostics, migration and upgrade planning, explicit plan application, guarded rollback, record validation, scoped unit/optional Run creation, and report rendering. It is not an autonomous scientific planner, an HPC submission service, or an environment provisioning step. Diagnostics report observed failures before suggesting configuration changes.

Keep installation/update dependencies separate from optional reporting dependencies. Reuse working rendering environments when appropriate. Do not install or update dependencies as an incidental side effect of ordinary unit execution or framework upgrade. Framework packaging does not require analysis repositories to be installable packages.

## 4. Installed project structure and policy entry points

Preserve the specification's source, outputs, reports, data, resources, environments, notes, documentation, and coordination boundaries. New projects add a private installation area while keeping familiar entry points:

```text
project_root/
├── AGENTS.md                         # Initial bridge plus project-owned instructions
├── CLAUDE.md                         # Optional bridge to shared instructions
├── REPORT_TEMPLATE.md                # Local presentation contract and shared-contract reference
├── PROJECT_INSTRUCTIONS.md           # Project-specific research instructions
├── framework-project.json            # Project-specific settings and path mappings
├── .research-framework/
│   ├── runtime.pyz                   # Framework-managed release payload
│   ├── policy/                       # Framework-managed shared operating/report contracts
│   ├── docs/                         # Framework-managed generic defaults
│   ├── installation.json             # Generated installation state
│   ├── baselines/                    # Exact upstream ancestors
│   ├── transactions/                 # Operation journals
│   └── backups/                      # Framework-change recovery only
├── templates/                        # Explicitly managed reusable templates; local additions allowed
├── tools/                            # Explicitly managed thin helpers and report stylesheet
├── repos/                            # Independent scientific repositories, if applicable
├── reports/                          # Project-owned paired scientific reports
├── analyses/                         # Project-owned evidence and execution records
└── coordination/
    ├── plans/RESEARCH_MAP.md          # Researcher-owned program
    ├── plans/ID_REGISTRY.json         # Project-owned stable registration history
    ├── plans/A###.md                 # Approved Aim/Strategy records
    ├── plans/workstreams/            # Optional expanded Workstream records
    └── manuscripts/                  # Publication-specific claims and evidence
```

Paths are new-project defaults, not restructuring instructions. Existing documentation, launchers, templates, or primary-system locations may be mapped in project configuration. Never assume a project root is a Git repository or that all relevant software lies under it.

For new projects, root bridges explicitly direct agents to read the shared policy and local research instructions. A link alone is not assumed to be automatically loaded by every agent. Common policies must also be understandable by human collaborators. Root bridges become project-specific files after initialization; updates cannot replace them as ordinary managed payload. Existing root instructions require reviewed reconciliation during migration, preserving their scientific and local rules.

Do not install this repository's development `AGENTS.md` into a scientific project. Do not create a proprietary-memory dependency or assume a tool-specific instruction loader works without a compatibility check.

## 5. Scientific records and governance

Implement the full v1.1 model with lightweight, readable records:

| Record | Required behavior |
|---|---|
| Research Narrative and Research Map | Distinguish questions, hypotheses, observations, inferences, alternatives, and synthesis; preserve researcher-selected priorities and dated adopted revisions |
| Workstream | Flexible sustained scientific purpose; no compulsory assay, dataset, software, or modality taxonomy |
| Aim/Strategy/Tactic | Preserve AST hierarchy and stable `A###-S##-T##` identity, with one coherent report per Tactic |
| Specifications | Material protocols, measurements, controls, parameters, QC, evaluation, and provenance; no fabricated irrelevant fields |
| Optional Run | A concrete execution, acquisition, batch, or experiment instance within a Tactic; preserve source and execution identity |
| Manuscript | Independent publication argument linking claims to unit evidence, limitations, conflicting evidence, and researcher decisions |

Workstreams and Aims have many-to-many associations; evidence can support multiple manuscripts or none. Changing a manuscript mapping does not change AST identity. A report revision is distinct from an execution Run, even if historical naming used similar identifiers.

Scientific prose remains in readable Markdown and authorized primary systems. Schemas validate structured identifiers, relationships, provenance, and execution records without requiring a second authoritative copy of the scientific narrative or a database. Generated indexes are reconstructible views; they cannot adopt scientific claims. The ID registry preserves registered and retired identities, not speculative proposals from notes.

Allocate IDs only within an agreed scope, checking approved plans, reports, analyses, and registration history. Reserve/create records transactionally, never recycle registered IDs, and stop for an explicit format decision if identifier capacity is exhausted. A new project has an empty registry and unadopted Research Map scaffold, with no fabricated Aim, Workstream, Tactic, Run, or manuscript.

Program discussion, review, literature assessment, and synthesis may occur without a new AST unit. Resume interrupted work under its existing Tactic. Preserve approved plans and record scientifically material deviations and renewed approval. Researchers adopt direction, interpretation, and manuscript claims; tooling must not infer adoption from successful execution.

## 6. Evidence, reporting, and reproducibility

Specification section 10 defines the eleven-section scientific reporting contract, corresponding EN/KO Markdown/HTML/PDF outputs, and no page-count requirement. Methods must support manuscript preparation and collaborator review without source-code inspection. Preserve Results/Interpretation separation, material definitions and calculations, controls, uncertainty, figures or appropriate primary evidence tables, limitations, and provenance.

Preserve publication-quality defaults while respecting journal needs, legibility, actual fonts, and measurement-image integrity. A table-only Tactic must not require a fabricated figure. Raster imagery embedded in a vector container must not be claimed as newly vectorized evidence. Unsupported mathematics or missing assets must fail explicitly, not disappear from an apparently successful report.

Track intended versus effective settings, reconstructed methods versus verified procedures, available versus producing revisions, and dirty source hashes when needed. Completed descriptive or technical work may use `NOT_EVALUATED` with a reason when no scientific verdict was evaluated. Do not label required but unperformed work complete.

Experimental, observational, and hybrid records cite authorized protocol, sample, acquisition, ELN/LIMS, or controlled-archive identifiers. Neither the framework repository nor its release artifacts receive restricted data or real research content. Tests use synthetic evidence. Reports link scientific source in independently usable repositories rather than duplicate editable scripts under analyses.

Report rendering is a separate operation from framework update. A requested revision preserves earlier report versions and approved plans, stages both languages, and replaces outputs only after validation. Old reports remain valid historical records; adopting a new contract does not rewrite them or silently revoke their prior status.

## 7. Human-operated execution and handoffs

Physical and regulated activities remain with authorized people and institutions. External computation and transfers follow human-operated workflows. Agents prepare verified, scoped commands and inspect actual returned evidence; they do not invent access, paths, job IDs, successful transfers, or producing revisions.

Keep login-node submission and monitoring separate from compute-job initialization. Use Slurm as already available; require a login-node module only after verifying it is unavailable. Do not activate Conda merely to submit or monitor. Conda jobs retain required module loading, initialization, and activation of an existing absolute environment prefix inside the job. Environment creation and dependency changes are separate operations.

Preserve the owning analysis repository's entry point, launcher location, and submission working directory. Keep launchers thin and scientific code independently versioned. The per-unit mapping of remote results, figures, and logs to verified local destinations must retain optional Run identity and transfer evidence. `WAITING` handoffs preserve the approved scope, known execution/protocol IDs, evidence received or missing, expected outputs, and the next human-operated step.

Before changing HPC workflows or instructions in a development checkout, follow the verified manual designated in its local development context. If that reference is missing, locate and verify the actual manual and report the broken reference rather than inventing a replacement. Generic releases carry project-neutral rules and configuration references, without a workstation-specific manual path, site modules, account, or environment prefix. A local test cannot establish cluster-policy compliance.

## 8. Installation, upgrade, and migration contracts

Initialization creates a selected release only after checking the destination and planned ownership. It does not initialize scientific Git repositories, clone software, install environments, or decide research direction. Existing nonempty destinations use inspected migration/merge plans rather than directory overlays.

Upgrade uses a verified release manifest, the exact previous upstream ancestor, the local file, and the new upstream file. Dry-run produces a read-only plan. Explicit application rechecks its preconditions, preserves local edits, rejects unresolved conflicts, backs up affected files, journals staged writes, and commits installation state last. Guarded rollback protects later edits. Phase 3 implements these operations for existing registered installations; the [engine contract](UPDATE_ENGINE.md) records the exact API, tested bounds, and recovery guarantees. [Initialization](INSTALLATION.md) and [metadata-free adoption](MIGRATION.md) are separate implemented operations, not updater side effects.

Metadata-free v0.5 adoption uses a separately reviewed migration plan. Preserve existing layout, AST IDs, reports, results, research instructions, configuration, repositories, and untracked files. Record observed legacy baseline provenance without inventing historical installation metadata. Unknown ancestors require conservative manual resolution. Keep local reporting improvements; do not automatically regenerate reports or write a scientific Research Map.

The exact ownership, merge outcomes, generated state, and recovery rules are defined in [ownership and updates](OWNERSHIP_AND_UPDATES.md).

## 9. Verification and release boundaries

Use temporary synthetic projects for automated tests of ownership, path handling, dry-run, conflicts, migration, rollback, interruption, and preservation of independent repositories and scientific records. Pilot experimental, computational, theoretical, observational, and hybrid evidence, including deferred handoff, negative/inconclusive completion, appropriate tables, optional Runs, and many-to-many manuscript evidence.

Automated checks establish structural and operational properties; manual scientific and bilingual review remains necessary. Actual cross-agent loading and human-operated HPC behavior require appropriate acceptance evidence, not claims inferred from unit tests.

Separate specification version `1.1`, implementation release versions such as `1.1.0-rc.1` and `1.1.0`, and schema versions. No implementation release or compatibility promise is issued by Phase 1. Verify archives through initialization, upgrade, and migration tests using the artifact itself. License/reuse terms, supported version matrices, and complete mathematical backend coverage must be resolved before claiming the corresponding release capabilities. Do not redistribute proprietary fonts or personal environment artifacts.

## 10. Phase checkpoints

| Phase | Work boundary | Current state |
|---|---|---|
| 1 | Architecture, ownership policy, development instructions, specification reconciliation, requirements traceability | Approved, including the portability follow-up; committed/pushed by the researcher |
| 2 | Observed legacy baseline, manifests, secure path/file validation, and component tests | Complete and committed by the researcher |
| 3 | Read-only plans, merging/conflicts, backups, journaling, recovery, guarded rollback, and safety tests | Authorized and implemented; see engine validation evidence |
| 4 | Versioned starter, self-contained runtime, new-project creation | Implemented; independent archive acceptance passes |
| 5 | Metadata-free v0.5 migration and installed version/ownership tracking | Implemented; synthetic preservation, interruption and guarded undo pass |
| 6 | Narrative/Workstreams/AST/Specifications/Map/IDs/manuscript evidence | Implemented; explicit approvals, many-to-many relationships and same-ID recovery tested |
| 7 | Detailed bilingual MD/HTML/PDF, equations and figures | Implemented; real rendering and corrected physical-size visual inspection pass |
| 8 | Optional Runs, handoffs, provenance and human-operated HPC | Implemented; synthetic consistency and command-boundary checks pass |
| 9 | Comprehensive acceptance and release candidate | Implemented; clean RC archive, complete local suite and Python 3.9/3.11 remote CI verified |
| 10 | Final version, release, Git publication and authorized active-target assessment | Software acceptance verified; observe publication and target deployment results separately |

The researcher explicitly authorizes autonomous completion of Phases 3–10, logical commits and reviewed pushes, and final active-target migration only under the stated backup/conflict/preservation conditions. The original reference remains read-only. [Acceptance](ACCEPTANCE.md), [traceability](REQUIREMENTS_TRACEABILITY.md) and [release procedure](RELEASE.md) distinguish implemented behavior, verification and remaining limits.
