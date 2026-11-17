# Research Program Framework 2.0.2

HPC planning-policy hotfix: justify resource and scheduling choices instead of
inheriting defaults from reference repositories, wrappers or example configs.

- Require a source and reason for CPU, memory, time, partition and concurrency
  choices. Separate scientific reproducibility from operational scheduling and
  explain cases where allocations or platforms affect the result.
- Independent arrays default to no explicit `%N` concurrency cap (equivalent to
  the task count). A lower cap needs an identified constraint or an explicit
  validation reason recorded in the AST plan. This is not a promise of concurrent
  starts or permission to ignore site/storage/tool constraints.
- Verify scheduling-limit facts once per applicable project scope, with date,
  source, returned evidence and coverage gaps in PROJECT_INSTRUCTIONS.md. Reuse
  them across ASTs until potentially stale. Read-only Slurm query examples cover
  associations, QOS and array configuration; missing fields are not proof of no
  limits. MaxArraySize is separate from concurrent-running-task limits.
- New AST draft plans include one execution/resource checklist item. No Slurm
  launcher, remote connection, submission service or semantic validator is added.

Downstream managed updates are AGENTS.md, docs/hpc.md and tools/new_unit.py.
The PROJECT_INSTRUCTIONS.md seed gains a site-fact prompt for new projects only;
existing project instructions remain project-owned and are never overwritten.
Record actual facts locally only after verified human-returned evidence. Existing
AST plans/reports, identities, analyses, code and environments are not rewritten.
See [the project update note](UPDATE_2.0.2.md).

The 2.x update format and managed allowlist are unchanged. Use the existing
preview/merge/backup mechanism. Human-operated HPC, login/compute environment
separation and detailed bilingual reporting remain intact. No actual cluster
policy or execution has been verified by the framework's synthetic tests.
