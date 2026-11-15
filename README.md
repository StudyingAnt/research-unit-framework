# Research Program Framework

A lightweight template for researcher-directed life-science projects. Browse
[`template/`](template/) to see the project you will get: Markdown operating
instructions, Coordination plans, stable Aim/Strategy/Tactic (AST) work, detailed
English/Korean reports and a few practical Python scripts.

**2.0 is a new baseline.** It retains the scientific design of v1.1, with no
backward-compatibility or automatic conversion for earlier installations.
Existing research can stay where it is; historical material can be consulted
individually when useful. Earlier releases remain in Git history.

## Create a project

Python 3.9+ on Linux/WSL is sufficient for project creation and updates. Clone or
extract a release, then put its root on your PATH once:

```bash
export PATH="/absolute/path/to/research-unit-framework:$PATH"
newproj --configure ~/projects
newproj my_research
```

Add the export to your shell configuration if you want it to persist. The
configured parent defaults to `~/projects`; `RPF_PROJECTS_DIR` or `--projects-dir`
can override it. An exact destination is also supported:

```bash
newproj my_research --destination /absolute/path/to/my_research
```

Without changing PATH, use `python3 tools/newproj.py my_research` from this
checkout. Creation refuses existing destinations and creates no Git repository,
scientific environment, adopted research direction or invented AST records.

## Start Coordination

Open the new project in your assistant and say:

> Start Coordination. Read the Research Map and relevant plans, examine the
> current hypotheses and alternatives, and help me choose the next priorities.

The assistant follows `AGENTS.md` and `coordination/COORDINATION.md`. Coordination
can develop Narratives, flexible Workstreams, Aims, dependencies and manuscript
evidence. It challenges weak arguments; only decisions you explicitly approve
enter formal scientific records. Brainstorming does not automatically create an
AST or adopt a hypothesis.

## Start or resume an AST session

Ask the assistant to read relevant plans and develop an Aim, Strategy, bounded
Tactic question and detailed Specifications with you. After approval, it handles
ID/folder administration with `tools/new_unit.py`. You do not need to memorize
the helper commands. Interrupted work resumes the same `A###-S##-T##` identity.
Repeat reporting revisions keep that AST; a substantively different
evidence-producing task warrants a new one. Execution Runs (`R###`) are optional.

Sessions communicate through plans, reports and figures. There is no required
cross-chat message, handoff summary or automatic chat transfer. Scientific code
can live in independent repositories under `repos/`; physical research and remote
HPC remain human-operated. No historical research import is required.

## Produce reports

The assistant fills the eleven-section EN/KO templates with actual scientific
rationale, definitions, procedures, filters, calculations, controls, uncertainty,
exact settings, figures/tables, findings, limitations and provenance. Methods must
support manuscript preparation without opening code. **There are no page limits.**

Markdown is editable; HTML and PDF are generated with a separately configured
reporting environment (Pandoc plus `requirements/reporting.txt` and actual report
fonts). The normal helper is `python tools/build_reports.py AST_ID --revision
REV001` inside the project. Each revision preserves all six language/format
outputs. Repeated revisions never overwrite earlier archives. Structural checks
supplement explicit scientific, bilingual and HTML/PDF visual review.

See [reporting setup and checks](docs/REPORTING.md) for the small configuration
and figure declarations. Project settings and scientific reports belong to you.

## Update a project

After pulling/extracting the newer framework, preview changes with its tool:

```bash
python3 tools/update_project.py /absolute/path/to/my_research
python3 tools/update_project.py /absolute/path/to/my_research --apply
```

The first command is read-only. Updates compare the previous template, local
file and current template. Unchanged managed files update; local modifications
are preserved or merged when disjoint. Conflicts block the entire application.
Verified affected-file backups are kept under the project's `.framework/backups/`.
Reports, plans, data, independent repositories and project settings are never
update targets. See [ownership, conflict resolution and backup use](docs/OWNERSHIP_AND_UPDATES.md).

The visible structure is deliberately small:

```text
template/       The single project template, including its tools and instructions
tools/          Project creation, updates and release packaging
newproj         Convenient creation command
docs/          Scientific design and short operating/engineering references
tests/         Synthetic project and reporting tests
```

Read [architecture](docs/ARCHITECTURE.md) for internals and [release notes](docs/RELEASE_NOTES.md)
for the baseline change. No runtime archive, migration service or proprietary chat
state is needed to browse or operate a project.
