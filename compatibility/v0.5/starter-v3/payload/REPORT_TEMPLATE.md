# Research Unit Report Contract

The smallest reporting unit is one **Tactic**, identified by `A###-S##-T##`. Use the same `<UNIT_ID>_<slug>` folder name under both `reports/` and `analyses/`.

## Deliverables

For every completed unit, create all six files:

- `reports/<UNIT_FOLDER>/en/report.md`, `report.html`, `report.pdf`
- `reports/<UNIT_FOLDER>/ko/report.md`, `report.html`, `report.pdf`

Markdown is the editable source in each language; HTML and PDF are derived products. Refer to the same verified quantitative findings and figures in both languages. Prefer Noto Serif for English output and Noto Serif KR / Noto Serif CJK KR for Korean output.

## Content structure

The English and Korean sources use corresponding sections:

1. **Motivation:** Why this unit is scientifically useful, including source report IDs and unresolved observations.
2. **Aim & tactic question:** The overarching Aim in one sentence, plus the narrower question this tactic can answer in one sentence.
3. **Strategy & tactic:** The approach and concrete procedure. Avoid duplicating implementation details.
4. **Specifications / evaluation:** Inputs, comparisons, numerical settings, metrics, sensitivity checks, expected output and decision criteria. Preserve the user-approved plan before executing.
5. **Execution & verification:** Which code/configuration was run, where, how the result was checked, and deviations from plan.
6. **Main figure:** One central figure, optionally accompanied by closely related alternative views and clear captions.
7. **Results:** Quantitative findings as observations only. Cite the backing result files. Include negative or null findings.
8. **Analysis / interpretation:** What the findings support and what remains only a hypothesis.
9. **Limitations & next questions:** Known limitations and brief follow-up ideas, without automatically initiating additional analysis.
10. **Artifact references:** Host-aware absolute paths and relative repository paths, configuration, outputs, figures, logs, Git commits, and run commands.

## Metadata

Each language's Markdown report starts with:

- `**Status:**` `PLANNING | APPROVED | EXECUTING | WAITING | BLOCKED | FAILED | COMPLETED`
- `**Scientific outcome:**` `NOT_EVALUATED | SUPPORTED | NOT_SUPPORTED | INCONCLUSIVE`
- `**Aim ID:**` `A###`
- `**Strategy ID:**` `S##`
- `**Tactic ID:**` `T##`
- `**Related units:**` other finished report IDs or `None`

Do not use `COMPLETED` to mean a hypothesis is supported. Do not fill result sections with expectations before execution.

## Reproducibility and references

- The **source of publication code** remains in `repos/<repository>/<task>/` and may support several units.
- The **outputs** remain in `analyses/<UNIT_FOLDER>/results/`, `figures/`, and `logs/` (or explicitly documented external HPC paths).
- Record source repository URL when known, exact Git SHA, local or remote hostname, executable entry point, effective parameters, run command, input/output absolute paths, and validation evidence.
- For HPC results, record the **unit-specific HPC -> WSL path mapping**, Slurm job/run identifier, and the transfer record at `analyses/<UNIT_FOLDER>/logs/hpc_transfer_manifest.md`. The local copy must be placed under the **same report unit ID**, separated into `results/`, `figures/`, and `logs/` (or documented unit-scoped staging before organization). See `docs/hpc.md`.
- For portable references, record repository-relative paths alongside host-aware absolute paths.
- Mark unresolved or unavailable fields honestly; never invent them.
- The PDF/HTML report may include one compact artifact table rather than listing every intermediate file. Link a full manifest or directory for large output sets.

## Visual standards

- Prefer one main figure per tactic. Additional panels should answer the same tactic question.
- Export every manuscript figure as 600 dpi PNG, vector PDF, and SVG from the same source code and data.
- Apply `docs/figure_style.md` with all figure typography in Arial, 5-7 pt at final figure size, solid black for text except when text color encodes a necessary data category.
- Figure text style is distinct from report-body Noto Serif typography.
- Aim for a 1-2 page PDF per language. Measure actual pages and shorten prose or adjust layout without shrinking a manuscript figure below its required final-size text specification.

## Chat-driven operation

The agent performs the lifecycle using local WSL tools after the user approves the scientific plan. The user does not manually create report folders or invoke report-building scripts. A first analysis uses the first available Aim/Strategy/Tactic ID; new analyses reuse existing Aims/Strategies when appropriate; pending analyses resume the original unit ID. See `AGENTS.md` for discovery and classification rules. HPC-only `git pull`, Slurm commands, and local `rsync` retrieval remain human-operated.

## Preparation and finalization

1. During planning, the agent creates the report source with `Status: PLANNING` once a unit is scoped and fills sections 1-4; keep 5-10 explicitly pending. Do not create speculative empty units from casual exploratory discussion.
2. After explicit user approval, set `Status: APPROVED` and implement in the designated source repository.
3. During execution or pending HPC results, set the accurate `EXECUTING` or `WAITING` status.
4. After verifying actual results, write Results separately from Interpretation and complete the artifact references.
5. Set `Status: COMPLETED` and an evidence-supported scientific outcome in **both** language sources.
6. The agent runs `python tools/build_reports.py <UNIT_FOLDER>` to generate HTML/PDF, and inspects both PDFs and links (or honestly reports a tooling blocker).
7. End the unit. Follow-up analyses require a separately scoped tactic and, normally, a new session.
