# Human-Operated HPC

Read the project's verified HPC manual/runbook and existing analysis repository
before preparing commands. Resolve the actual project, owning analysis repository,
optional installed packages, cluster, paths, environment and submission working
directory. Record site-specific facts in PROJECT_INSTRUCTIONS.md. Generic examples
are not verified cluster settings. Missing facts are questions, not defaults.

The human operates remote access, code synchronization, submission, monitoring
and result retrieval. Do not assume SSH or initiate transfers/submissions.
Provide separate, resolved commands for each step after inspecting the project.
Do not claim execution, transfer or success without returned evidence.

Keep login-node submission/monitoring separate from compute-job initialization.
If Slurm is already available, no extra module load or Conda activation is needed
merely to submit or monitor. Conda-based jobs must still load verified required
modules, initialize Conda and activate the existing absolute environment prefix
inside the job. Keep environment provisioning separate from ordinary science.

Keep Slurm launchers thin, with all #SBATCH directives before executable lines.
Scientific algorithms, processing, plotting and input enumeration belong in the
owning analysis repository. A repository may use numbered stages, a nested
workflow or an existing submission wrapper; preserve its actual working-directory
contract. Do not force a scripts/ layout or make analysis scripts installable
packages. Reusable packages, when relevant, are independently installed and
versioned dependencies, not code copied into a launcher.

Select resources from the actual workload and verified cluster policy. Prepare
log directories before submission. Preserve exact inputs, effective settings,
analysis and dependency revisions (including dirty-source hashes), interpreter,
job/Run identity, logs and expected outputs. An absent queue entry is not success;
check accounting, exit codes, outputs and scientific QC separately.

Resume WAITING/BLOCKED work under the same AST. Keep received/missing evidence
and the next human step in its existing plan, report or optional Run record.
No mandatory handoff summary is required. Never invent job IDs, provenance,
account access, source revisions or historical success; never use destructive
sync/deletion or rebuild a working environment without explicit scope.
