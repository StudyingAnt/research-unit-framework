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

## Resource and scheduling rationale

Values in reference/predecessor repositories, submission wrappers, templates or
example configurations are not verified site policy. Reuse a value only with a
stated reason, such as matching a published procedure for reproducibility; a
reference default or unnoticed plan approval is not itself that reason.

Separate result-affecting choices (tool versions, arguments, reference inputs)
from operational allocations/scheduling choices (CPU, memory, wall time,
partition, array throttle). Do not carry over scheduling values by default just
to reproduce a scientific procedure. If an allocation or platform choice affects
results, such as thread-dependent calculations or architecture, document that
specific reproducibility dependency rather than treating the two lists as
universally independent.

In the AST plan's execution/resource section, give every CPU, memory, time,
partition and array-concurrency choice a source: workload estimate, verified site
policy, or explicit reproducibility reason. Label estimates and their uncertainty;
distinguish per-task requests from aggregate demand. Reference the dated site fact
and record the rationale before submission, not only in an execution log afterward.

## Independent array concurrency

For an array of T independent tasks, default to no operator-imposed concurrency
cap: omit Slurm's `%N` suffix (equivalent to N = T). This does not guarantee that
all tasks start together; site limits, resource availability and scheduler policy
still apply. Independence also does not establish that shared storage or a tool
can support arbitrary concurrent load.

A lower cap needs an identified constraint or an explicit small first slice for
validation. Examples include verified user/account/QOS limits, workload-based
memory or shared-storage I/O pressure, licence/tool limits, and a deliberate
validation stage. Record task count, chosen concurrency (including an explicit
throttle when used), source and reason in the plan. State the validation scope if
running only a first slice; do not silently leave its conservative cap on the
full run. Never inherit a wrapper's throttle merely because it is the default.

## Verify scheduling limits once per project scope

Before the first relevant submission, have the human verify applicable limits on
the actual cluster. Store the result in the project-owned PROJECT_INSTRUCTIONS.md
with date, cluster/account/partition/QOS scope, exact command or authoritative site
source, returned evidence/reference, interpretation and any gaps. Later ASTs reuse
that fact while it applies; do not ask again or poll accounting for every AST.
Reverify when the record may be stale: policy/allocation changes, a different
cluster/account/partition/QOS, or new scheduler evidence contradicting it.

These are read-only command shapes for the human on the verified Slurm system,
not commands the assistant executes remotely. Replace VERIFIED_QOS with the
applicable observed QOS and check field support in the installed Slurm version.
If Slurm is available, no login-node Conda activation or extra module load is
needed merely to perform these queries.

```bash
sacctmgr -nP show assoc where user="$USER" format=Cluster,Account,Partition,DefaultQOS,QOS,MaxJobs,MaxSubmit,GrpTRES
sacctmgr -nP show qos where name=VERIFIED_QOS format=Name,MaxJobsPU,MaxSubmitJobsPU,MaxTRESPU,GrpTRES
scontrol show config | grep -Ei 'ClusterName|MaxArraySize|SchedulerParameters'
```

Association rows are a starting point, not proof of unlimited scheduling. Check
applicable inherited/account, job/partition QOS and partition limits as needed;
do not infer that blank fields, empty results, unavailable commands or denied
access mean no limits. Record partial coverage as unknown and use verified site
documentation or administrator clarification for missing facts. MaxArraySize
bounds the array task index; max_array_tasks may additionally bound task count.
Neither establishes a simultaneous-running-task limit or justifies a throttle.

See Slurm's [array documentation](https://slurm.schedmd.com/job_array.html),
[accounting query fields](https://slurm.schedmd.com/sacctmgr.html),
[limit hierarchy](https://slurm.schedmd.com/resource_limits.html), and
[configuration reference](https://slurm.schedmd.com/slurm.conf.html).

## Resume and evidence

Resume WAITING/BLOCKED work under the same AST. Keep received/missing evidence
and the next human step in its existing plan, report or optional Run record.
No mandatory handoff summary is required. Never invent job IDs, provenance,
account access, source revisions or historical success; never use destructive
sync/deletion or rebuild a working environment without explicit scope.
