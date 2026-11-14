# HPC Environment Reference

This file holds **verified environment facts**, not guessed server paths. Fill fields only after checking the actual environment. Global behavioral rules remain in `AGENTS.md`.

## Cluster and access

- Host and login endpoint: `TBD`
- Project root on HPC: `TBD`
- Scheduler and allowed partitions: `TBD`
- Available modules and environments: `TBD`
- Source code mirror/clone paths: `TBD`
- Results destination: `TBD`
- Data/resource paths: `TBD`

## Human-operated procedure (desktop chat handoff)

The agent handles local project preparation and report management. The user performs the following remote/transfer boundary, **not** ordinary scaffolding or report building:

1. **Before HPC sync:** agent updates the correct local repository, checks the script and arguments, records the code revision, and checks whether the code is actually available from the intended remote. An AI-assisted commit/push requires separate authorization. Never suggest pulling a revision that has not been pushed.
2. **HPC Git update:** user connects to the real host and executes a short, copy-pasteable `cd <verified-repo> && git pull --ff-only` command after authentication.
3. **Slurm submission:** agent supplies a separate `sbatch --parsable <verified-script>` command. User executes it and returns the job ID/output.
4. **Queue/status/log inspection:** agent provides concise commands, e.g. `squeue -j <jobid>` and `sacct -j <jobid> --format=JobID,State,ExitCode,Elapsed,MaxRSS` and exact log inspection commands as necessary. User executes and returns actual output.
5. **Local retrieval:** agent determines the **current unit's exact `A###-S##-T##_<slug>` folder**, verifies the HPC output path(s) from the actual Slurm script/configuration, and maps each remote result class into the correct local WSL `analyses/<UNIT_FOLDER>/results/`, `figures/`, or `logs/`. The agent prepares local destination directories. Then it provides one or more exact `rsync -avh --progress` commands **to run from the user's WSL/local terminal**. The user completes interactive authentication and returns the actual transfer output. The user does **not** choose IDs, invent local paths, or manually sort files after transfer.
6. **Local validation and reporting:** agent checks downloaded results, figures and logs via accessible local tools. It creates the standard EN/KO MD, HTML and PDF report set and finalizes the unit only when evidence supports completion.

If HPC execution is pending, record `WAITING` and sufficient details in the existing unit: hostname, job ID, script/commit, planned output paths, and next command. The user may start a **new desktop chat** to resume the same unit. Do not duplicate it.

Do not combine submit, status check, and retrieval into an unattended chain. Do not fabricate path names, job IDs, Git SHAs, success, or output locations. Avoid destructive rsync flags unless explicitly authorized. Prefer manual, inspectable commands with source and target paths confirmed.

## Unit-scoped HPC retrieval contract (required)

Before issuing **any** rsync command, the agent must:

1. Resolve the active **unit ID and full folder name** from the approved plan and existing report. Reuse it when resuming an HPC job; do not invent a fresh ID.
2. Identify the relevant HPC host and **actual output source paths** from verified Slurm scripts, run configurations, submission logs, or user-supplied terminal output. Do not assume that results are stored beside the Git repository.
3. Resolve the actual local **WSL** project root and construct destinations below `analyses/<UNIT_FOLDER>/`. Do not use a Windows path, the repository's source-code tree, `reports/`, or a project-wide generic `results/` as the transfer destination.
4. Map the **contents**, not just a similarly named parent folder:
   - Numeric data, model output, tables, intermediate result files -> `analyses/<UNIT_FOLDER>/results/`
   - HPC-generated figures (when present) -> `analyses/<UNIT_FOLDER>/figures/`
   - Slurm stdout/stderr, execution logs, saved run metadata -> `analyses/<UNIT_FOLDER>/logs/`
5. If the HPC output combines several categories in a single directory, map verified subdirectories separately; if that is not possible, copy into a clearly labeled **unit-specific staging directory** under `analyses/<UNIT_FOLDER>/results/hpc_staging/<RUN_ID>/`, then have the agent inspect and organize the local files. Never dump mixed files into an unrelated unit or shared output folder.
6. If the Tactic has multiple runs, preserve each run's identity by using a run-specific subfolder (`R001`, `R002`, etc.) or another verified distinct name. Never overwrite previous runs by accident. Check existing local destinations before transfer. If a collision is possible, stop and plan a non-destructive destination with the user; do not use `--delete`, `--remove-source-files`, or destructive overwrite options.
7. For source **directory contents**, use a trailing slash on the rsync source (e.g., `.../results/`) and a corresponding destination ending in `/`. Otherwise rsync may create an unintended extra directory level. Quote paths containing spaces.
8. Show the **unit ID, HPC source, and exact local destination** alongside each command. The agent may create the destination locally; the human runs only the transfer command. Do not ask the human to choose or organize the downloaded files.
9. On receipt of transfer output, confirm file presence, file types, expected counts/sizes when known, and relevant Slurm completion/error evidence. Keep an audit record at `analyses/<UNIT_FOLDER>/logs/hpc_transfer_manifest.md` containing unit/run ID, host, source -> destination mapping, executed command, job ID, known Git SHA, and validation findings. Record uncertainties rather than guessing. Do not mark the report completed from successful rsync alone.

### Illustrative path mapping (not verified real paths)

The following demonstrates **where** data should land. All angle-bracket fields are placeholders. The agent must replace them with confirmed absolute paths before giving a runnable command.

```text
Unit: A001-S01-T02_pcr_bias
HPC result data:  <verified-hpc-host>:<verified-hpc-run>/results/
WSL destination:  <verified-wsl-project-root>/analyses/A001-S01-T02_pcr_bias/results/

HPC Slurm logs:   <verified-hpc-host>:<verified-hpc-run>/logs/
WSL destination:  <verified-wsl-project-root>/analyses/A001-S01-T02_pcr_bias/logs/
```

```bash
rsync -avh --progress '<verified-user>@<verified-hpc-host>:<verified-hpc-run>/results/' '<verified-wsl-project-root>/analyses/A001-S01-T02_pcr_bias/results/'
rsync -avh --progress '<verified-user>@<verified-hpc-host>:<verified-hpc-run>/logs/' '<verified-wsl-project-root>/analyses/A001-S01-T02_pcr_bias/logs/'
```

If the remote has no figures, do not fabricate a `figures/` remote path. The agent may generate local figures after retrieving and validating numeric results. Source-code edits and effective run configuration stay tied to the correct repository, while retrieved run metadata should also be preserved for reproducibility.
