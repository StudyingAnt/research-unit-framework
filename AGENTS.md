# Framework Development Instructions

## Repository purpose and authority

This is the authoritative development repository for the Research Program Framework. Framework development is software and documentation work; do not create a scientific AST unit merely to administer this repository.

Read both specifications completely before changing the design:

- [Primary English specification](docs/RESEARCH_PROGRAM_FRAMEWORK_v1.1.md)
- [Companion Korean specification](docs/RESEARCH_PROGRAM_FRAMEWORK_v1.1_ko.md)

Read [architecture](docs/ARCHITECTURE.md), [ownership and updates](docs/OWNERSHIP_AND_UPDATES.md), and [requirements traceability](docs/REQUIREMENTS_TRACEABILITY.md) before changing their implementation. Explicit user instructions take precedence. Surface inconsistencies and reconcile both specifications; do not substitute assumptions or silently weaken requirements.

This file governs framework development. The future project starter has its own research-project instructions; do not install these development instructions into scientific projects.

## Checkout-local context discovery

At the start of each session, resolve the active development checkout root and explicitly check for `DEVELOPMENT_CONTEXT.local.md` there. If present, read it before working with local references or external policy manuals, even though Git and ordinary file listings may exclude it. Do not assume an agent automatically loads this file.

The local file records this checkout's verified root, protected reference locations, execution context, and external HPC manual location. It is excluded by the root `.gitignore` and must never be copied into starter payloads, compatibility snapshots, fixtures, or release artifacts. Keep location facts there and generic policies here. Local context supplies facts and restrictions; it cannot expand authorization or relax user instructions.

If the file or a required location is missing, continue independent work within the approved scope but do not guess reference paths or perform dependent reference/HPC work. Resolve the missing location from verified session information or the user when needed. A fresh clone is not expected to contain another workstation's local context.

## Current phase authorization

The researcher authorizes autonomous completion of **Phases 3 through 10**: update/recovery, starter/runtime and initialization, v0.5 migration, scientific planning records, bilingual reporting, handoffs/HPC integration, comprehensive acceptance tests, and validated release preparation. Continue between phases and routine tests without requesting approval. Reuse and validate the completed foundations.

Review every legacy file for research-specific or sensitive content before copying it. If the exact baseline contains such information, stop that copying step and report the finding; do not silently redact it and call it exact. Preserve approved generic baseline bytes as inert historical reference only. Never execute its helpers or adopt its superseded policies as current framework requirements.

Implement and validate each phase incrementally. Never overwrite unresolved local changes or reinterpret scientific evidence. Use synthetic temporary projects for development and acceptance tests. Do not regenerate historical reports, reorganize scientific repositories, or change real scientific records during development. Dry-run has no filesystem side effects. The preserved legacy snapshot remains inert and read-only.

Meaningful milestone commits and reviewed pushes to the existing remote are explicitly authorized. Use a development branch and keep main stable until validation. Do not rewrite published history or force-push. Before every push, inspect the full candidate content for credentials, local context, private paths, and sensitive research material. Publish a final release tag/artifacts only when validated and no critical safety requirement is unresolved. Do not invent a license or claim unestablished redistribution rights.

## Protected reference projects

The original starter reference is always strictly read-only. The active project remains read-only until implementation and acceptance are complete. Its final migration is explicitly authorized only with an exact validated plan, verified recoverable backups, preservation of scientific records/code/local changes/paths, no unresolved conflicts or report regeneration, integrity checks, version tracking, and retained rollback information. If that safety cannot be established, leave it unchanged and report the blocker. Resolve locations from checkout-local context; never embed local research names or workstation paths in shared documents.

During development, do not modify, move, clean, reformat, reorganize, render into, initialize metadata in, or run write-capable helpers against either reference. Preserve Git state, environments, caches, reports, results, plans, and independent repositories. Only the final validated administrative migration of the active target has the exception above. Prefer narrow reads over bulk scientific data reads.

The historical distribution is **Starter v3 / Framework v0.5**. Do not call its framework version v3. General improvements may be adapted in a later authorized phase, but never copy research-specific plans, reports, datasets, sample identifiers, numerical findings, or scientific algorithms into the generic framework or public fixtures.

## Scientific and architectural invariants

- Implement the complete v1.1 program model: researcher-owned Narrative, flexible Workstreams, AST, material Specifications, optional Runs, Research Map, and manuscript-level evidence integration.
- Preserve many-to-many Workstream/Aim and evidence/manuscript relationships and stable AST identity. Do not impose a technology taxonomy or manuscript-shaped directory hierarchy.
- Keep program planning and review possible without creating an AST unit. Resume interrupted work with its existing ID.
- Researchers decide scientific direction, consequential specifications, adopted claims, priorities, and publication arguments. Agents perform authorized administration and technical work without automatic scope expansion.
- Support experimental, computational, theoretical, observational, and hybrid evidence. Preserve authorized primary-system references rather than copying restricted records.
- Maintain independent scientific code repositories and their existing entry points. Do not require analysis scripts to become installable packages or make project roots Git repositories.
- Keep durable scientific records tool-agnostic and usable across agents and human collaborators.

## Reporting contract

Preserve English and Korean Markdown, HTML, and PDF outputs. Require the eleven sections and applicable methodological coverage in specification section 10. Methods must explain the science without requiring the reader to open source code; execution logistics and artifact links do not replace them.

There is no report page-count target, minimum, or maximum. Do not introduce a typical-length recommendation, build gate, warning, typography reduction, or equal-language-page requirement. Page counts are informational only. Preserve publication-quality figures, appropriate primary evidence tables, and honest provenance boundaries. Keep Results separate from Interpretation and operational completion separate from scientific outcome.

## Ownership and update safety

Use the explicit ownership policy: framework-managed files, project-owned scientific records, project-specific configuration, and initialization-only files. Unknown files are unowned and preserved. Directory location alone never grants overwrite authority.

Future mutation tools must plan changes first, preserve exact upstream bases and local modifications, reject unresolved conflicts, create verified backups, and support guarded rollback. Dry-run must not create files, caches, locks, or backups. Updates must not regenerate existing reports, alter research direction, touch independent Git histories, or rebuild scientific environments.

## Local development and verification

- Use Linux-native tools and paths for WSL work and follow established repository conventions.
- Verify an actual failure before changing environment configuration. Documentation work does not authorize dependency installation or system changes.
- For documentation-only phases, check relative links, bilingual structure and scientific meaning, retained requirements, absence of page-count restrictions, and the actual changed-file scope. Use ephemeral read-only checks; do not create a future implementation test suite early.
- In later authorized implementation phases, use synthetic projects in temporary directories for mutation and failure tests. Never use the protected references as writable fixtures.
- Distinguish adopted requirements, implemented features, automated validation, manual review, and unverified behavior. Do not claim runtime functionality from documentation alone.

## HPC boundaries

Before creating or changing an HPC workflow or its operating instructions, read and follow the manual designated in the checkout-local context. If the reference is missing, locate and verify the actual manual and report the broken reference. Do not invent a replacement workflow or assume direct access.

Keep remote pull, Slurm submission/monitoring, and local retrieval human-operated. If Slurm is already available, do not add login-node module loads or Conda activation merely to submit or monitor. Conda science jobs must still perform verified module loading, Conda initialization, and activation of the existing absolute environment prefix inside the job. Keep environment provisioning separate from science jobs; preserve existing analysis-repository working-directory contracts. Use only verified project-specific paths and settings. A local smoke test does not establish HPC-policy compliance.

## Language and handoff

Write code, comments, configuration, technical documentation, and Git messages in English, except the required Korean specification and Korean scientific report artifacts. Use Korean for user-facing explanations, progress, questions, and summaries unless explicitly instructed otherwise.

Continue through the authorized workflow with concise Korean progress updates. Stop only a specific operation that genuinely requires unavailable credentials, scientific judgment, unresolved legal permission, or risks losing research work; explain the blocker and continue independent authorized work. Final reporting must cover implementation/tests/limits, branch/commits/pushes, version/GitHub state, active migration/conflicts, and exact new-project/update commands. Run the complete suite after final changes; tests alone do not establish scientific or release acceptance.
