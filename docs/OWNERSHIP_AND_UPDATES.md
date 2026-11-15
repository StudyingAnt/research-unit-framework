# Ownership and Project Updates

Only projects created from baseline 2 are supported. Previous releases and real
historical projects are not converted. Work from the current framework checkout
or extracted release; the project does not depend on that checkout for research.

| Files | Ownership and rule |
|---|---|
| Explicit template-manifest.json managed entries | Generic AGENTS/report/Coordination policies, reusable templates, style defaults and helper scripts; compare against the previous upstream snapshot |
| Reports/revisions, analyses, plans/ID registry, manuscripts, data, repos, resources, environments, notes | Project-owned scientific records; never framework update targets |
| PROJECT_INSTRUCTIONS.md, framework-project.json, README.md, docs/compute.md and ignore rules | Initialization-only seeds that become project-owned settings; never overwrite or recreate on update |
| Unlisted local additions | Unowned; preserve even within a managed-looking folder |
| .framework/ | Small generated version/snapshot state and affected-file backups; no scientific authority |

The updater hard-restricts managed paths to named generic policy files and
reusable templates/tools. A manifest cannot claim an actual plan, report, dataset
or scientific repository. Newly managed paths colliding with local unregistered
files are conflicts, even if their bytes happen to match. Local deletions are
preserved when upstream is unchanged; a concurrent upstream change is a conflict.

## Preview and apply

```bash
python3 tools/update_project.py /absolute/new-baseline-project
python3 tools/update_project.py /absolute/new-baseline-project --apply
```

Preview performs no writes, locks, temporary merges or cache creation. It shows
all actions/diffs and a plan_digest. Optionally require that exact reviewed digest
with `--apply --expect DIGEST`. Apply always recomputes and rejects a stale plan.
No update invokes reporting, scientific execution, Git or dependency installation.

For base B, local L and new N: L=B updates to N; N=B keeps local work; L=N is
already current. Disjoint UTF-8 line edits merge in memory. Ambiguous overlaps,
binary changes on both sides, delete/change combinations and unmanaged collisions
block the entire application. Changed file modes are compared too. A removed
upstream file is deleted only if locally pristine; changes require review.
A managed entry reclassified as a seed stays in place and becomes project-owned.
No blanket overwrite option exists.

For a tracked-file conflict, compare `.framework/base/HASH` (HASH is in the
project manifest), the project file, and `template/PATH` in the new source. Prepare
an explicit merged file outside the project, then use the same option in preview
and apply:

```bash
python3 tools/update_project.py /absolute/project --resolve templates/report.en.md=/absolute/merged.en.md
python3 tools/update_project.py /absolute/project --resolve templates/report.en.md=/absolute/merged.en.md --apply
```

This changes only a known managed file. It cannot adopt an unmanaged collision or
change scientific paths. Resolve that collision manually after preserving it.
The new snapshot always stores official N, separately from the merged local result.

## Backups and interruption

Before the first managed-file change, verify affected originals, their modes and
absence, and previous manifest under `.framework/backups/TIMESTAMP-ID/`.
`changes.json` includes exact before/after hashes and the reviewed plan. `before/`
contains originals; `previous-manifest.json` and retained immutable snapshot
objects preserve the old version information. Keep this directory private: it
may contain local instructions. Backups are never automatically pruned.

An update is not globally atomic. An interruption can leave some new files with
the old manifest. Inspect a new preview and retained backup before retrying;
immutable baseline objects keep that old manifest meaningful. If a late writer
changed a file, the script stops rather than clobbering it. No automatic cleanup,
forced rollback or speculative scientific recovery occurs.

For manual restoration, inspect changes.json, compare current files with its
recorded after-state, and preserve any later work first. Restore only affected
files from before/ with their modes; remove operation-added files only after
checking they still equal the operation's output. Restore previous-manifest.json
only with its corresponding file set. Do not reset the entire project or touch
scientific records. This is an administrative affected-file backup, not a
scientific-data backup. See architecture for concurrency/platform limits.
