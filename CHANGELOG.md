# Changes

## 2.0.2

Require a reason/source for HPC resource and scheduling values rather than copying
reference defaults. Independent arrays default to no explicit concurrency cap;
any lower cap is justified in the AST plan. Reuse dated project scheduling-limit
facts, with read-only Slurm query examples and explicit limits on interpretation.
New unit plans include an execution/resource checklist. Existing projects update
AGENTS.md, docs/hpc.md and tools/new_unit.py; project-owned site facts and existing
plans require scoped local recording, never an automatic rewrite.
See [release notes](docs/RELEASE_NOTES.md) and
[downstream adoption](docs/UPDATE_2.0.2.md).

## 2.0.1

Clarify default Aim granularity, bounded enabling objectives and flexible
one-or-several Strategy/Tactic composition. Align installed guidance, the Aim
template, EN/KO specifications and philosophy. Existing research records and
identities are preserved; no runtime or metadata-format change is required.
See [release notes](docs/RELEASE_NOTES.md) and the
[project update instructions](docs/UPDATE_2.0.1.md).

## 2.0.0

Template-first clean baseline. See [release notes](docs/RELEASE_NOTES.md) for
retained science, simplified creation/updates, removed infrastructure and limits.
Earlier implementation and release history remains in Git and existing tags.
