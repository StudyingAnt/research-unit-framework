# Research Unit Project Starter

A lightweight, file-centered workflow for Codex, Claude Code, and Antigravity sharing the same WSL project. Research units are labeled `A###-S##-T##`: Aim / Strategy / Tactic.

## Use the desktop chat, not the terminal

This starter is designed to be **agent-operated from a normal desktop-app chat**. You do **not** need to run `new_unit.py`, `build_reports.py`, create directories, pick IDs, update status files, or manually export reports. The agent does those local WSL tasks when it has the necessary tools and permissions.

1. Place the starter files in your existing project root, preserving all pre-existing `repos/` and other data. Review conflicts when merging files with the same names.
2. Open the **top-level project directory** in Codex Desktop, Claude Code Desktop, or Antigravity with WSL as the actual execution environment. A nested Git repository can have a different instruction-discovery boundary, so do not assume the root rules load when opening only that nested folder.
3. Start a normal conversation about the scientific work. The agent should inspect the registered Aim/Strategy/Tactic history, classify the request, and discuss the plan rather than ask you to run setup commands.
4. Approve the plan in chat. The agent then creates/manages the unit, implements code in the correct repository, runs local work, and prepares HPC handoffs only when needed.
5. On completion, the agent checks outputs and creates the six report artifacts in `reports/` and a concise summary in chat. Start the next independent research unit in a new chat when desired.

### Case A: first Aim, no previous units

A starter project may contain only templates, empty directories and existing code. If there is no actual registered Aim or research-unit report, the agent should treat it as a **first unit**, discuss the scientific question and propose `A001-S01-T01` (if free). It should create `coordination/plans/A001.md`, the approved unit report and output folders **itself**, after the Aim, Strategy, Tactic, and specifications are agreed. No command is required from you.

Example message (Korean or English is fine):

> I want to investigate whether the initial barcode distribution could arise from technical bias. Let's define the first Aim, Strategy, Tactic and analysis plan together.

### Case B: prior aims and reports exist

The agent should read **only relevant** approved plans and completed reports, then decide whether the question belongs to an existing Aim/Strategy or requires a new one. It should propose the correct unused ID, summarize relevant findings, and discuss the new plan. Existing unit reports, not previous chat history, supply the context.

Example message:

> Read A001-S01-T01 and A001-S01-T02. I want a new analysis of a possible alternative explanation. Let's plan it before implementing anything.

### Case C: resume a unit awaiting HPC results

If the existing unit is `WAITING` or `BLOCKED`, the agent **continues that same unit ID**. It reads the saved approved plan and execution handoff, asks for only the missing HPC evidence, verifies retrieved outputs, and finishes the report. It must not create a fresh tactic just because the desktop chat is new.

Example message:

> Resume A001-S01-T02. I have the Slurm job status and downloaded results. Please validate them and complete the report.

### Exact human/agent boundary

| Responsibility | Who handles it |
|---|---|
| Identify existing A/S/T, discuss and record the new plan | Agent with user approval |
| Create local folders, files, scripts and bilingual outputs | Agent in WSL |
| Modify publication code and local config in `repos/` | Agent after plan approval |
| Execute and inspect local analysis | Agent if tools permit |
| Local Git commit/push | Agent only with separate authorization |
| On HPC: `git pull --ff-only`, `sbatch`, `squeue`/`sacct`, log inspection | User (human-operated HPC) |
| On local WSL: `rsync` retrieval from HPC | User (human-operated transfer) |
| Verify retrieved results, export figures, finish MD/HTML/PDF | Agent |

For HPC, the agent provides short, precise copy-paste commands and waits for actual outputs. **For rsync specifically, the agent must select the destination using the existing `A###-S##-T##_<slug>` ID and map result data, figures, and logs to the matching `analyses/<UNIT_FOLDER>/results/`, `figures/`, and `logs/`.** The user runs the supplied command in the local WSL terminal but never has to sort downloaded files or guess their destinations. The agent creates local folders, records a unit-scoped transfer manifest, and verifies downloaded outputs. It does not pretend to have remote access or automatically change server files. It must persist a resumable status record when a job is pending. See `docs/hpc.md`.

## Structure

- `AGENTS.md`: common behavioral rules and research-unit lifecycle.
- `CLAUDE.md`: imports the same instructions for Claude Code.
- `REPORT_TEMPLATE.md`: compact report contract.
- `templates/`: source templates for the two languages.
- `repos/`: independent source Git repositories and publication-ready scripts/configurations; this starter does **not** initialize a Git repository here.
- `analyses/`: actual output files, figures, and logs for each tactic.
- `reports/`: six outputs per completed tactic (EN/KO x MD/HTML/PDF).
- `coordination/plans/`: mapping between aims, strategies, and tactic reports; manuscript, revision, and presentation assets are organized under `coordination/`.
- `docs/figure_style.md`, `docs/hpc.md`: optional specialized references when needed.
- `data/`, `resources/`, `envs/`, `notes/`: existing project-level material.

## Internal tools (for agents and debugging)

The commands below explain what the agent may run **inside WSL**. They are **not routine instructions for the user**. In an ordinary research session, the desktop agent should invoke them itself.

To scaffold an approved unit, the agent can run:

```bash
python3 tools/new_unit.py A001-S01-T01 barcode_distribution
```

This creates `reports/A001-S01-T01_barcode_distribution/en/report.md` and `ko/report.md`, plus empty output directories under `analyses/A001-S01-T01_barcode_distribution/`. It does **not** modify code repositories or execute analysis, and will refuse to overwrite an existing unit.

The agent fills the Markdown reports during planning. It must not replace pending result placeholders with hypothetical observations.

## Build both language reports

The **agent** checks these prerequisites and performs report generation when authorized and technically able. It requests user intervention only for unavailable system-level access, credentials or package-install permissions. Prerequisites in the WSL environment: Python 3, Pandoc, WeasyPrint, Fontconfig, and the preferred Noto Serif fonts. Install the Python renderer in an isolated Python environment, if needed. For Debian/Ubuntu, package names and availability may vary:

```bash
sudo apt-get install pandoc fontconfig
python3 -m pip install weasyprint
```

Install Noto Serif and a Korean Noto Serif family through your authorized font sources. The Korean output accepts `Noto Serif KR` or `Noto Serif CJK KR`. Check the installed font family names with `fc-list : family | grep -i 'Noto Serif'`. Never redistribute proprietary fonts through project files.

When both language reports have `Status: COMPLETED`, all pending tokens are resolved, and `figure_01.{png,pdf,svg}` exists, the **agent** runs:

```bash
python3 tools/build_reports.py A001-S01-T01_barcode_distribution
```

Or render all completed units:

```bash
python3 tools/build_reports.py --all
```

To preview an unfinished report or use an environment without the requested fonts **temporarily**:

```bash
python3 tools/build_reports.py A001-S01-T01_barcode_distribution --allow-draft --allow-font-substitution
```

A preview is not a validated final scientific report. The build tool checks structural completeness and file presence, but it cannot prove statistical correctness, inspect every linked figure, or guarantee the target page count without human/agent review. Inspect the generated PDFs and HTML in their output folders.

## Nested repositories and report history

The starter intentionally does not create a `.git/` at the project root. `repos/` can contain multiple independently versioned repositories. If reports and coordination documents need version history, decide separately whether the project root itself should be a management Git repository, a synced folder, or another backed-up workspace. Do not accidentally commit nested Git histories as ordinary files.

## Manuscript figure rules

See `docs/figure_style.md`. Every manuscript figure must have `png` (600 dpi), `pdf` (vector), and `svg` (vector) variants. Figure labels use Arial, 5-7 pt at final size, black except for genuine data-color encoding. Font availability must be verified in the figure-generation environment. PDF/HTML report text uses Noto Serif families, not Arial.

## Portable code

Paths under `analyses/`, `data/`, or `resources/` may be private/HPC-specific. Keep scripts in the publication repository portable through documented input arguments or config files. Final reports should contain both verifiable host-aware absolute paths for internal reproducibility and portable relative references where feasible. Check public releases for embedded personal paths and private data.
