# Human-Operated External Computation

Read the project's verified HPC manual before creating or changing workflows.
Resolve the owning analysis repository, working directory, launcher, existing
environment, target cluster and outputs from verified project information.
Humans perform remote pull, submission, monitoring, cancellation and transfers.
Slurm submission/status commands require no login Conda activation; load a Slurm
module only if its absence has actually been established.

Jobs retain all required verified module loads, Conda initialization and activation
of the existing absolute environment prefix before invoking scientific programs.
Keep all SBATCH directives above executable shell statements and launchers thin.
Preserve existing nested-repository invocation contracts. Do not install packages,
create environments or embed scientific algorithms in ordinary launchers.
Keep expected outputs outside source checkouts as configured by the project.

Supply separate pull/submit, status and result-retrieval commands only after paths
and settings are verified. Preserve optional Run identity when mapping remote
outputs to local destinations. Check actual accounting, exit codes, logs and output
quality. Disappearance from a queue is not success. Never manufacture a job ID or
claim an unobserved transfer. Avoid destructive transfer or cleanup flags.
