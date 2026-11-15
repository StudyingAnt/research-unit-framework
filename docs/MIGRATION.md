# Metadata-Free v0.5 Adoption

Migration uses the reviewed observed Starter v3 / Framework v0.5 ancestor.
Its historical installed revision remains unknown. It is never executed.
The operator must inspect a complete dry-run before applying it. An existing
`.research-framework` directory is refused; recover or inspect it first.

```bash
python3 newproj.pyz migrate-plan /absolute/project --release /absolute/release
```

Project-owned records and unknown files are not migration targets. Existing
configuration and research instructions remain intact. Scientific seed files,
including the Research Map and ID registry, are not introduced by migration.
Recognized legacy managed paths use the observed ancestor in a three-way
comparison. Local edits are merged only when unambiguous; conflicts refuse the
whole operation. `--keep-local RELATIVE_PATH` is an explicit reviewed resolution
for a recognized legacy managed file, never for an unknown destination collision.
Retained old helpers may still implement obsolete behavior; use the canonical
installed runtime for v1.1 operations and review their compatibility separately.

`--bridge-policy-reviewed` prepends the exact policy-loader text shown in the plan
to existing AGENTS/CLAUDE/report entry points, preserving their original bytes.
It makes current generic reporting rules take precedence over obsolete generic
ones while retaining project-specific science. Review this administrative change
against the actual instructions before selecting it. Migration does not adopt or
rewrite scientific claims, plans, source code, existing reports or repositories.

Application requires the exact plan digest and an existing, private recovery
directory outside the project:

```bash
python3 newproj.pyz migrate /absolute/project --release /absolute/release --plan-digest REVIEWED_DIGEST --backup-root /absolute/private/recovery
```

Use the same reviewed bridge/keep-local options in both commands. Before the first
target modification, all touched originals, original absence/modes and after-images
are verified in that external directory. The durable journal survives incomplete
installation or removal of installation metadata. Installation state is finalized
last. Exact new upstream bases are distinct from installed locally merged content.
This is an affected-set administrative backup, not a scientific-data backup.

An interruption leaves external journal/backup evidence. Recovery is guarded undo,
not speculative completion. Inspect `migration-OPERATION/journal.json`, then:

```bash
python3 newproj.pyz migration-rollback-plan /absolute/private/recovery/migration-OPERATION
python3 newproj.pyz migration-rollback /absolute/private/recovery/migration-OPERATION --plan-digest REVIEWED_DIGEST
```

The entire touched set is checked before restoration. Later modifications block
undo of affected files. Untouched files, including retained local helpers, remain
outside the undo scope. Preserve the external journal, blobs and adoption record.
No automatic cleanup, force overwrite, report regeneration, root Git initialization
or scientific reorganization occurs. The same trusted-state, cooperating-writer,
Linux filesystem and ordinary ownership/metadata limitations as the update engine
apply. Stop editors and jobs that could modify administrative targets during apply.
