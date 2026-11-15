# Research Project Operating Instructions

Read `PROJECT_INSTRUCTIONS.md`, `REPORT_TEMPLATE.md`, and the relevant parts of
`coordination/plans/RESEARCH_MAP.md` before scientific work. Read actual files;
do not assume that an assistant automatically follows Markdown links.

## Researcher authority

The researcher decides scientific direction, priorities, consequential
Specifications, adopted interpretations and manuscript arguments. Actively
challenge weak arguments, missing controls, confounding and unsupported claims;
offer alternatives. Brainstorming is not approval. Record a formal decision only
after explicit researcher acceptance, with its date, rationale and uncertainties.
Do not infer approval from a successful analysis, render or conversation ending.
During scientific discussion and planning in both Coordination and AST sessions, 
use the globally installed K-Dense `scientific-critical-thinking` skill when available. 
Read its `SKILL.md` and apply its guidance to evaluating hypotheses, study designs, assumptions, confounding, and evidence quality. If unavailable, continue without it.

## Coordination

When the researcher starts **Coordination**, follow
`coordination/COORDINATION.md`. Read the Research Map and relevant Aim plans;
discover existing AST reports when needed. Discuss competing hypotheses,
Narratives, flexible Workstreams, priorities, dependencies and evidence gaps.
Synthesize verified observations separately from inference and proposed claims.
Planning, review and manuscript discussion do not require an AST.

Coordination and AST sessions communicate through persistent project files,
not direct access to other chats. No mandatory message, summary document or
automatic chat handoff is required. Consult reports when they matter; do not
duplicate every report in another authoritative document.

## AST work

Read the relevant plans and reports; agree the Aim, Strategy, bounded Tactic
question and material Specifications before consequential execution. Use
`A###-S##-T##` as stable identity. Resume unfinished work under its existing ID.
A report may be revised repeatedly without a new AST. Create a new Tactic only
for a substantively distinct evidence-producing task; repeat executions may be
optional `R###` Runs within the same Tactic. Report revisions use `REV###`.
Never recycle registered or retired IDs or use manuscript mappings to renumber.

Use `tools/new_unit.py` for scoped ID/folder/draft administration after approval.
It does not approve unfilled Methods or execute science. Preserve approved plans
and prior report revisions. At completion, present findings and stop; a useful
result does not authorize further experiments, analyses or strategic changes.

## Files and evidence

- `coordination/plans/`: researcher-approved Narrative, Workstreams, Aims,
  priorities and dated decisions. Workstreams and Aims can be many-to-many.
- `coordination/manuscripts/`: publication-specific claims, supporting and
  contradicting evidence, limitations and researcher decisions. One AST can
  inform multiple manuscripts or none.
- `reports/`: each Tactic's detailed EN/KO scientific record and revisions.
- `analyses/`: derived tables, figures, logs, effective settings and optional Runs.
- `repos/`: independent analysis or reusable-package repositories. Keep their
  established entry points; do not force analysis scripts into packages.
- `data/`, `resources/`, `envs/`, `notes/`: project inputs, references,
  environments and clearly unadopted ideas, respectively.

Support experimental, computational, theoretical, observational and hybrid work.
Qualified humans perform physical/regulated activities. Reference authorized
ELN/LIMS/acquisition or controlled records instead of copying restricted data.
Existing historical research need not be imported or formalized. Consult or
formalize individual material only when useful and specifically authorized.

## Reporting and HPC

Follow `REPORT_TEMPLATE.md` and `docs/figure_style.md`. Preserve all eleven
scientific sections and scientifically equivalent EN/KO Markdown, HTML and PDF.
Methods explain the science without source-code inspection. There is no report
page-count target, minimum or maximum. A table can be primary evidence. Keep
operational status separate from scientific outcome; completed negative/null or
NOT_EVALUATED work is legitimate when explained. Never invent a verdict.

Read `docs/hpc.md` and verified project settings before remote-work instructions.
The human runs remote pull, submission, monitoring and transfer commands. Keep
login-node submission separate from compute-job environment initialization.
Never assume site modules, paths, access, job IDs or successful execution.

Framework updates affect reusable policies/templates/tools, never scientific
records. Preserve project-specific settings and local edits. A template change
does not authorize rebuilding historical reports or rerunning analyses.
