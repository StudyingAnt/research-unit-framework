# Research Program Framework

This repository is the authoritative Git-managed development source for Framework v1.1, its future versioned project starters, initialization, migration, safe updates, verification, and releases. The historical Starter v3 implements Framework v0.5.

The framework supports experimental, computational, theoretical, observational, and hybrid life-science research. Researchers control scientific direction and adopted claims; agents assist with authorized execution, reproducibility, and documentation.

## Current implementation boundary

**Phase 1: architecture, file ownership, development instructions, and bilingual specification alignment.** The overall architecture is approved. Runtime code, starter payloads, installation metadata, migration/update tools, automated test suites, packaging, and releases are not implemented in this repository. Their paths in the architecture are planned paths, not available commands or shipped assets.

Phase 1 is approved; the authorized follow-up makes development context portable. It does not authorize Phase 2, a project migration, Git commits, pushes, tags, or publication. Further implementation requires explicit phase authorization.

## Documents

| Document | Role |
|---|---|
| [English v1.1 specification](docs/RESEARCH_PROGRAM_FRAMEWORK_v1.1.md) | Primary scientific and governance requirements |
| [Korean v1.1 specification](docs/RESEARCH_PROGRAM_FRAMEWORK_v1.1_ko.md) | Companion translation |
| [Architecture](docs/ARCHITECTURE.md) | Adopted repository, deployment, scientific-record, and release boundaries |
| [Ownership and updates](docs/OWNERSHIP_AND_UPDATES.md) | File ownership, conflict handling, migration, backup, and rollback contract |
| [Requirements traceability](docs/REQUIREMENTS_TRACEABILITY.md) | Requirement sources, future acceptance evidence, and current implementation status |
| [Development instructions](AGENTS.md) | Agent scope, protected references, and phase gates |

## Checkout-local development context

At session start, agents follow `AGENTS.md` to explicitly discover the optional root `DEVELOPMENT_CONTEXT.local.md`. This Git-excluded file holds the actual checkout path, protected reference locations, execution context, and external policy-manual location. A new clone supplies its own verified location facts when needed; it does not inherit another workstation's paths. Missing context does not authorize dependent reference or HPC operations. Generic policies remain in the shared documents, and local context cannot expand permissions.

## Reporting standard

One Tactic produces one scientifically complete report, with corresponding English and Korean Markdown, HTML, and PDF outputs. The report explains rationale, actual methods, material specifications, controls, calculations, uncertainty, figure or table construction, findings, interpretation, and provenance. It must support manuscript preparation without requiring readers to open source code.

Reports have **no page-count target, minimum, or maximum**. Page counts are informational. Scientific completeness, readability, bilingual equivalence, and verified evidence determine acceptance. Figure defaults remain publication-oriented and configurable as specified.

## Reference safety

The original v0.5 starter and active research project are strictly read-only references. No project installation or restructuring follows from adopting this architecture. Scientific records, data, code repositories, local research instructions, and existing reports remain project-owned. Research-specific content must not enter the generic framework or its test fixtures.

Future starters will come from one maintained source tree and versioned release artifacts. Scientific projects will not need this development checkout, a mandatory root Git repository, or mandatory packaging of analysis scripts.
