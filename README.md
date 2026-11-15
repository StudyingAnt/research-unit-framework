# Research Program Framework v1.1

Researcher-directed life-science program records, detailed bilingual scientific
reporting, and guarded framework administration. Scientific authority is the
[English specification](docs/RESEARCH_PROGRAM_FRAMEWORK_v1.1.md), with its
[Korean companion](docs/RESEARCH_PROGRAM_FRAMEWORK_v1.1_ko.md).

The implementation supports Narrative, flexible Workstreams, Aim/Strategy/Tactic
and material Specifications, optional Runs, a Research Map and stable ID registry,
manuscript evidence integration, durable handoffs and human-operated HPC workflows.
Experimental, computational, theoretical, observational and hybrid work share the
same governance. Scientific repositories remain independent; no project-root Git
repository or installable analysis package is required.

## Use a release

Core administration requires Python 3.9+ on Linux/WSL. Download and verify a
trusted release archive, then extract it into its own directory. Never overlay
it onto an existing research project. The standalone newproj zip application
also embeds the starter and works without this development checkout.

```bash
python3 /absolute/release/newproj.pyz new /absolute/new/project
python3 /absolute/project/.research-framework/runtime.pyz inspect /absolute/project
python3 /absolute/project/.research-framework/runtime.pyz --help
```

The new destination must be absent. Initialization creates no scientific IDs,
adopted direction, environments, independent repositories or remote jobs.

## Plan before existing-project changes

```bash
python3 /absolute/release/newproj.pyz update-plan /absolute/project --release /absolute/release
python3 /absolute/release/newproj.pyz update /absolute/project --release /absolute/release --plan-digest REVIEWED_DIGEST
```

Read-only plans create no files, locks or backups. Application rejects stale
plans and unresolved conflicts, retains exact upstream ancestors and local edits,
verifies backups before replacement, journals writes and finalizes metadata last.
Guarded recovery/rollback protects later work. Unknown files and scientific records
are preserved. See [ownership](docs/OWNERSHIP_AND_UPDATES.md) and
[the update engine](docs/UPDATE_ENGINE.md) for guarantees and platform limits.

Metadata-free Starter v3 / Framework v0.5 projects use the distinct
[migration procedure](docs/MIGRATION.md), with inspected legacy ancestry,
explicit conflict resolutions and external verified recovery storage. Existing
reports, analyses, layouts, research instructions and Git histories are preserved.
Framework administration never regenerates scientific reports.

## Scientific work and reporting

[Scientific record commands](docs/SCIENTIFIC_RECORDS.md) record explicit researcher
approval references and preserve stable IDs/revisions. Program planning needs no
AST unit; interrupted work resumes its existing identity. An agent cannot adopt
a scientific direction or manuscript claim from a successful execution.

[Reporting](docs/REPORTING.md) produces corresponding EN/KO editable Markdown,
HTML and PDF with eleven sections, manuscript-level methodological guidance,
static math, publication-quality figure checks and preserved revisions. There
are no arbitrary page-count limits. Optional rendering dependencies and actual
font files are configured separately; scientific/bilingual review and visual
inspection remain explicit requirements. Unsupported math/assets/fonts fail
honestly. Table-only and completed NOT_EVALUATED evidence are supported.

[Execution and handoff tools](docs/EXECUTION_AND_HANDOFFS.md) distinguish intended,
reconstructed, verified and unknown provenance. Humans retain remote access,
submission, monitoring, transfers and physical/regulated operations. Command
preparation does not execute remote work or provision environments.

## Develop and validate

Read [AGENTS.md](AGENTS.md) and any ignored checkout-local context explicitly.
The original legacy reference is read-only. The active target remains read-only
during development and can change only under the final validated migration
conditions. Public sources, fixtures and releases contain generic content only.

```bash
PYTHONPATH=src python3 -B -m unittest discover -s tests -q
PYTHONPATH=src python3 -B -m research_program_framework audit-public
PYTHONPATH=src python3 -B -m research_program_framework build-release dist/rc
```

See [architecture](docs/ARCHITECTURE.md), [requirements traceability](docs/REQUIREMENTS_TRACEABILITY.md),
[acceptance evidence](docs/ACCEPTANCE.md), [release workflow](docs/RELEASE.md),
and [installation](docs/INSTALLATION.md). Core tests use synthetic temporary
projects. Actual rendering acceptance uses a separately selected environment;
optional dependency absence is reported as a skip rather than a false pass.

No license grant is supplied or inferred. Third-party fonts, scientific packages
and research content are not bundled. The legacy snapshot is inert historical
migration evidence, not current operating policy.
