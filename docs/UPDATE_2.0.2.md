# Adopting the 2.0.2 HPC Planning Hotfix

Use the verified v2.0.2 framework source and an authorized existing 2.x project.
Resolve actual source/project roots in that project session; do not overlay the
template tree or change any scientific repository's launchers automatically.

| Downstream file | How to adopt |
|---|---|
| AGENTS.md | Managed update: consult the resource-rationale and concurrency policy while planning execution |
| docs/hpc.md | Managed update: resource sources, independent-array default, throttle reasons and reusable dated site facts |
| tools/new_unit.py | Managed update: future generated AST plans include the execution/resource checklist |
| PROJECT_INSTRUCTIONS.md | Project-owned: record verified scheduling facts locally with date/scope/source/evidence; the changed seed is for new projects only |
| Existing AST plans | Project-owned: add relevant rationale in the active plan before execution when authorized; no bulk rewrite or new AST is required |

Inspect the installed format-2 manifest, local instructions and previous upstream
snapshots. Preview with the new source, review the diffs and only then apply:

```bash
python3 /absolute/SOURCE/tools/update_project.py /absolute/PROJECT
python3 /absolute/SOURCE/tools/update_project.py /absolute/PROJECT --apply --expect REVIEWED_PLAN_DIGEST
```

Preserve local policy/runbook additions. Resolve conflicts explicitly against the
old snapshot, local file and new template; do not blindly overwrite or keep every
local version. Use the same reviewed --resolve PATH=FILE options in preview and
apply. Inspect any mode-only differences from differing extraction conventions.
Keep the verified backup path and [recovery instructions](OWNERSHIP_AND_UPDATES.md).

For site facts, have the human run the read-only queries described in the updated
HPC guidance on the verified cluster, then record returned evidence in the
existing PROJECT_INSTRUCTIONS.md. Do not invent limits, infer unlimited scheduling
from blanks, copy this seed over local settings, install dependencies, or add
login-node environment activation just for querying/submitting. Later ASTs reuse
that dated record while its scope and freshness remain applicable.

Verify version 2.0.2, preserved local additions and a same-release preview without
further changes. A new synthetic draft can demonstrate the checklist; do not
create a real AST merely to test an update. Existing plans, reports/revisions,
scientific data, independent repositories, environments and approved methods
remain unchanged. The framework update neither runs these Slurm queries nor
submits/reruns jobs. Apply the planning rule to future execution decisions.
