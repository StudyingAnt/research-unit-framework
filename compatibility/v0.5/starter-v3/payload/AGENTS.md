# Research Unit Workflow

## Principle

A research task is a self-contained, figure-centered **Tactic** with one approved plan, verifiable outputs, and one concise report. Conversations are temporary; reports and computational artifacts are the durable record. Apply this workflow to research analysis, not to ordinary questions or tasks the user explicitly limits to planning or review.

## Desktop chat is the user interface

- The user starts and directs scientific work by chatting with Codex Desktop, Claude Code Desktop, or Antigravity Desktop in the WSL-backed **project root**. No setup command or predefined phrase is required to start a research unit.
- **The agent**, not the user, handles routine *local* project operations when tools and permissions allow: inspect the project, identify and reserve IDs, create plans and directories, run `tools/new_unit.py`, edit code/configuration in `repos/`, execute local analyses, organize outputs, render bilingual reports with `tools/build_reports.py`, and verify deliverables.
- Treat `tools/*.py` and the corresponding commands in `README.md` as agent implementation details or debugging fallbacks, **not** steps the user must perform for normal work.
- The user discusses the scientific question, reviews/approves the analysis plan, interprets the results, and personally performs the designated **human-operated HPC steps**: remote `git pull`, Slurm submission/status/log commands, and local `rsync` to retrieve files. Supply only the necessary copy-paste commands at each handoff, then use the actual returned output.
- Never claim to have run a command or accessed WSL/HPC when the current app session does not actually provide that capability. State the blocker and the smallest necessary user action.

## Start-of-session project discovery and classification

On **every research-analysis request**, without needing a special user command:

1. Confirm the active workspace is the intended project root and that tools execute in its intended WSL environment. Do not silently switch projects or alter existing repository structure.
2. Inspect `coordination/plans/` (excluding `AIM_TEMPLATE.md`), report IDs/statuses under `reports/`, and only the relevant `analyses/` outputs and `repos/` structure. Do not bulk-read raw data, every report, or unrelated repositories.
3. Classify the request:
   - **FIRST_UNIT:** No registered Aim and no prior unit reports. Discuss the first scientific Aim, Strategy, and Tactic; propose `A001-S01-T01` if available. Existing unregistered code does **not** automatically count as a registered Aim. Ask how it relates only when it materially affects the proposed work.
   - **NEW_UNIT:** Plans/reports already exist. Read only pertinent previous reports; decide with the user whether to reuse an Aim and Strategy, add a Strategy, or create a new Aim. Allocate the next available Tactic ID *within its Strategy*; do not automatically create a new Aim for each chat.
   - **RESUME_UNIT:** The request continues an approved or `WAITING`/`BLOCKED` unit. Read its report, plan, relevant execution evidence, and outstanding handoff. Continue the **same ID**, not a duplicate unit.
   - **REVIEW_ONLY:** The user wants discussion, planning exploration, interpretation, or a review without execution. Do not force creation of files or a new unit.
4. Show a **brief Korean kickoff summary**: what related work is known (or that this is the first unit), proposed/reused ID if identifiable, concise Motivation, one-sentence Aim/Tactic question, Strategy/Tactics, and the Specifications or decisions still needing discussion. Do not overwhelm the user with an inventory.
5. Discuss the plan in the chat until the user approves it. Prepare/update `coordination/plans/A###.md` and the unit report as necessary. The agent creates the filesystem structure automatically **once the unit/plan is agreed**; it may create an earlier draft if useful, but must not leave speculative unused IDs or folders behind.
6. Preserve existing plans and reports. Before selecting an ID, check collisions in plans, reports, and analyses. An empty starter project is not evidence that any actual analysis has already run.

## Structure and ownership

- Start at the shared project root when possible. Preserve existing directories and independent Git repositories under `repos/`; never reorganize without approval.
- `repos/`: authoritative publication/reusable code and editable configuration, each in its appropriate repository/task folder.
- `analyses/<UNIT_FOLDER>/`: results, figures, and logs, not duplicate editable scripts.
- `reports/<UNIT_FOLDER>/`: one research-unit report in English and Korean.
- `coordination/`: cross-unit aim/strategy plans, manuscripts, revisions, presentations.
- `data/`, `resources/`, `envs/`, `notes/`, `docs/`: project-level material as applicable.
- Read only relevant completed reports and contextual files, not the entire project history.

## IDs and scope

- Unit ID: `A###-S##-T##`; unit folder: `<UNIT_ID>_<short_snake_case_slug>`.
- **Aim (A):** scientific objective/question stated in one sentence.
- **Strategy (S):** approach to that Aim; multiple strategies can share an Aim.
- **Tactic (T):** one executable question and its results/figure(s); this is the reporting unit.
- **Specifications:** inputs, parameters, thresholds, versions, metrics, and evaluation criteria. Several runs/parameter sweeps can belong to one Tactic.
- Check `coordination/plans/` and existing reports before proposing an ID. Never silently reuse or renumber an existing ID. A Tactic may use several code repositories. The agent manages ID assignment and file creation through available local tools; the user does not have to invoke scaffolding scripts.

## Phase I: plan and approval

Discuss and document, in this order:

1. **Motivation:** why this analysis is needed and which previous reports support it.
2. **Aim and tactic question:** one clear sentence for each.
3. **Strategy and tactic:** scientific approach and concrete procedure.
4. **Specifications:** datasets, model parameters, comparisons, metrics, expected figure(s), validation and decision criteria.

Use `REPORT_TEMPLATE.md` and `templates/report.en.md` for the plan. The agent creates/updates draft reports and empty output folders as needed; the user is not responsible for doing so. **Do not implement analysis code or run the analysis before the user explicitly approves the plan**, unless an explicit user request overrides this boundary. Preserve the approved plan; seek renewed approval for scientifically material changes and record deviations.

## Phase II: execution

- Implement scripts/configurations in the correct repository under `repos/`, never as a second editable copy under `analyses/`.
- Preserve effective run parameters, executable entry point, dependencies, random seeds, validation evidence, and exact Git revision when known.
- Make publication code independently usable; do not hard-code private project paths into reusable public code.
- Store each unit's local outputs in the **exact matching ID-and-slug** directory: `analyses/<UNIT_FOLDER>/results/` (numeric data), `analyses/<UNIT_FOLDER>/figures/` (plots), and `analyses/<UNIT_FOLDER>/logs/` (Slurm stdout/stderr and run/transfer records). A remote HPC path may be documented while output is pending; the final local destination must be identified by unit ID and category. Never transfer to an ambiguous shared `results/` or a different unit's directory.
- For HPC retrieval, **the agent selects and checks the precise remote source and local WSL destination for each output category, prepares local destination directories, and writes the human-executable `rsync` command(s)**. The user only performs the local terminal transfer, supplying authentication and actual transfer output. Verify unit ID, folder slug, job/run identity, and source/destination mapping before proposing a command. Record the transfer in `analyses/<UNIT_FOLDER>/logs/hpc_transfer_manifest.md`. See `docs/hpc.md` for the required procedure.
- Verify actual outputs before reporting. Do not invent measurements, commits, paths, or successful runs.
- Never destroy raw data or overwrite important files, commit, push, publish, or make consequential Git history changes without separate explicit authorization.
- For HPC/SSH/Slurm, follow `docs/hpc.md`: **the human operator performs remote `git pull`, Slurm submission/checks, and local `rsync` retrieval**. Prepare and verify the local code and exact copy-paste commands, separate submission from inspection and retrieval, and wait for returned logs/results. Use `WAITING` when results are pending. Commit/push require separately granted permission; do not assume a remote pull can find unpushed changes.

## Phase III: concise report and handoff

- Use `REPORT_TEMPLATE.md`. **One Tactic = one report**; target 1-2 PDF pages per language, excluding linked artifacts.
- Separate quantitative **Results** from scientific **Analysis/Interpretation**, and note limitations and optional next questions.
- Produce EN/KO versions of `report.md`, `report.html`, and `report.pdf`. Markdown is the editable source; both languages must preserve the same claims, data, figure(s), and references.
- Figure exports: `png` at 600 dpi, `pdf` vector, `svg` vector. See `docs/figure_style.md`. Figure text must be Arial, 5-7 pt at final size, solid black unless text color explicitly encodes a data category.
- PDF/HTML report body: Noto Serif (EN) and Noto Serif KR or Noto Serif CJK KR (KO), with font availability checked.
- Cite verified host-aware absolute paths plus repo-relative paths when applicable, source repository and Git SHA, effective config, results, figure exports, and logs. Never invent missing references.
- Status: `PLANNING`, `APPROVED`, `EXECUTING`, `WAITING`, `BLOCKED`, `FAILED`, `COMPLETED`. Scientific outcome separately: `NOT_EVALUATED`, `SUPPORTED`, `NOT_SUPPORTED`, `INCONCLUSIVE`.
- `COMPLETED` means the analysis/validation/reporting finished, **not** that the hypothesis was supported. A negative or inconclusive result is valid.
- At completion, the agent itself renders the six report files (when the local tooling is available), checks PDF page counts and figures, summarizes findings and locations in Korean, then stops. Never delegate ordinary report generation to the user. Do not start follow-up tactics automatically. A new session should rely on selected completed reports rather than prior chat history.

## Language and documentation

- Code, comments, docstrings, scripts, configuration, Git messages, and research report artifacts: **English** by default.
- User-facing explanations, planning dialogue, and progress: **Korean** by default. Respect explicit overrides.
- Keep copy-pasteable file contents separate from explanatory commentary.
- Load specialized references only when needed: `docs/figure_style.md` for figures, `docs/hpc.md` for HPC, `REPORT_TEMPLATE.md` for reports, and `coordination/plans/` for Aim/Strategy mapping.
- `tools/new_unit.py` scaffolds a draft without touching code; `tools/build_reports.py` renders validated Markdown to HTML/PDF.

## Session handoff and continuity

- When waiting on HPC, persist `Status: WAITING`, code revision, exact run command, remote host/path, submission identifier if known, expected files, the **verified HPC-to-local destination map keyed by unit ID**, and next user-operated command in the existing unit report or a referenced log. A fresh desktop chat must be able to resume this unit from files alone.
- After the user downloads output files with `rsync`, inspect and verify them locally, complete the report, then end the research unit. Do not automatically start the next Tactic.
- For new work, use completed reports and approved plan files as the shared scientific memory across Codex, Claude Code, and Antigravity. Do not depend on the previous chat's context or a proprietary auto-memory feature.
