# Scientific Requirements and Baseline-2 Evidence

Scientific authority: [English v1.1](RESEARCH_PROGRAM_FRAMEWORK_v1.1.md) and
[Korean companion](RESEARCH_PROGRAM_FRAMEWORK_v1.1_ko.md). The researcher-approved
baseline-2 redesign supersedes earlier installation/migration/phase requirements.

| Requirement | Implementation / validation boundary |
|---|---|
| Narrative and epistemic categories; flexible Workstreams and many-to-many Aims | Research Map, Aim/Workstream templates and Coordination policy; no generated scientific direction |
| AST, material Specifications, stable non-recycled IDs and same-ID resume | new_unit.py, small registry, plan/report templates, reserved IDs and occupied-path checks |
| Optional Runs and independent report revisions | run.md, R### within Tactic, immutable REV### archives; no mandatory execution instance |
| Manuscript evidence synthesis, contradictions and limitations | manuscript.md and Coordination workflow; no renumbering by publication |
| Researcher-controlled decisions and critical discussion | AGENTS.md, PROJECT_INSTRUCTIONS.md, Coordination instructions; no automated adoption or approval authentication |
| Experimental/computational/theoretical/observational/hybrid evidence | Scientific templates, primary-system references, code-free table-only acceptance |
| Independent source repositories and primary records | No root Git/package requirement, no bulk import, no source/data update targets |
| Human-operated HPC | Generic hpc.md; preserved job-internal setup and existing repository contracts; actual cluster execution untested |
| Cross-agent continuity | Explicit common policy loading and persistent plans/reports; no required chat message, summary or proprietary memory |
| Detailed Methods and all eleven scientific sections | Paired templates and source validation; semantic/methodological adequacy requires explicit review |
| EN/KO MD/HTML/PDF without page limits | Actual synthetic rendering, metadata/numeric/math correspondence, visual review; page counts informational |
| Publication output and honest provenance | Actual font/glyph checks, physical image widths, 600 dpi PNG checks, vector exports and documented exceptions; manual figure review remains necessary |
| Revisions and no automatic historical conversion | Immutable six-output revisions, preview isolation, no migration/bulk rebuild command |
| Visible single template and simple creation | newproj command, configured projects parent, absent-destination checks, standalone copied helpers |
| Reliable future updates | Explicit managed allowlist, previous official snapshots, B/L/N comparison, conflict blocking, read-only preview, verified original backups |
| Scientific/settings preservation | Seeds and unknown files excluded from updates, forbidden scientific paths, synthetic sentinel/hash checks |
| Lightweight release | Browsable source archive, Python 3.9/3.11 core tests and renderer-enabled local acceptance; old tags/history retained |

The tests exercise synthetic projects only. No real experiment, historical-project
conversion, remote HPC run, institutional access or automated scientific judgment
is claimed. Specific current results and environment limits are in ACCEPTANCE.md.
