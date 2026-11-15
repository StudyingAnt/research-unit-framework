# Phase 3 Safe Update Engine

**Status:** Implemented update/recovery engine for registered installations; adjacent lifecycle modules are documented separately
**Contracts:** [Architecture](ARCHITECTURE.md), [ownership policy](OWNERSHIP_AND_UPDATES.md), [manifest/path validation](MANIFESTS_AND_PATHS.md), [traceability](REQUIREMENTS_TRACEABILITY.md)

## 1. Scope and prerequisites

The engine manages explicitly registered class A files only. Project-owned scientific records, class C instructions/configuration, and class D seeds are preserved. New D seeds are not created by an upgrade; existing or deleted seeds are not replaced. Ownership transitions require separate adoption and become conflicts. Unknown destination files remain unowned even when their bytes match the incoming file.

An existing `.research-framework/installation.json` and exact upstream objects under `.research-framework/baselines/` are required. No function bootstraps these, guesses a legacy version, creates a scientific project, or reorganizes repositories. Synthetic test fixtures construct registered installations directly; that fixture code is not a public initializer.

The installation receipt uses schema version `1`, kind `framework_installation`, a project identifier, nonnegative generation, the Phase 2 release manifest, an `installed` fingerprint/absence map for every current A file, and the last operation identifier or null. A persistent `project_owned` map retains B/C ownership of seeds even after their upstream removal and local deletion; older receipts without that field infer the current seeds and preserve them on the next actual update. Release changes cannot promote those paths to A. Upstream objects are keyed by SHA-256 and retain exact upstream bytes independently of locally merged installed results. Unknown/corrupt state or missing ancestors stops normal updating.

## 2. API and read-only review

The public engine entry points are:

| Function | Behavior |
|---|---|
| `updates.plan_update(project, payload, release, resolutions=None)` | Validate the Phase 2 manifest and exact payload, inspect the registered installation, compare B/L/N, and return an immutable in-memory plan |
| `UpdatePlan.describe()` | Return a reviewable description with actions, reasons, fingerprints, local/planned and upstream diffs, conflicts, and a plan digest |
| `transactions.apply_update(plan)` | Recompute under the project lock, reject stale/forged/conflicted plans, prepare verified recovery material, and apply |
| `transactions.plan_rollback(project, operation_id)` | Read-only preflight of a completed or interrupted operation and all recovery targets/backups |
| `transactions.plan_recovery(project, operation_id)` | Read-only preflight for an unfinished operation; committed operations require explicit rollback |
| `transactions.apply_rollback(plan)` | Revalidate the reviewed rollback/recovery plan under lock and restore safely |

Plans stay in memory; printing a description does not save a plan file. There is no implicit write, repair, cache, lock file, backup, or journal in dry-run. Reads use Linux `O_NOATIME`, including descriptor-based directory reads, so successful dry-run does not change access times. If no-atime access is unsupported or permission is denied, stop rather than silently fall back to a read that changes metadata. Owned Linux/WSL project and payload trees are the tested context.

Planning binds the actual root identity, raw receipt, incoming release and payload snapshots, managed-file content/mode/identity, relevant parent identities, and explicit resolutions. Apply recomputes that plan before creating operation storage. It also checks paths again at write boundaries. Changes to a target, receipt, payload, root, or parent invalidate the plan. Unrelated scientific records are not read to establish a global project snapshot.

## 3. Three-way decisions

Use exact old upstream B, current local L, and incoming N. Preserve byte encodings and newline conventions.

- Unmodified L follows changed N; unchanged N preserves modified L; L equal to N is already current.
- Disjoint UTF-8 line edits merge in memory. Identical edits coalesce. Overlapping edits, competing insertions, ambiguous insert/delete boundaries, and edits on both sides of binary content become conflicts.
- No merge subprocess or temporary file is used. No conflict markers are written. Existing unresolved marker lines block acceptance.
- Compare content and permission modes separately so a local executable-bit change can survive an unrelated upstream content change.
- Preserve local deletion when N is unchanged. A changed N versus local deletion is a conflict.
- An upstream removal proposes explicit retirement of an unmodified managed file. Modified local content conflicts and is preserved.
- Any unresolved conflict blocks the entire update before operation storage or target writes.

Explicit `resolutions` are path-to-bytes decisions, or `None` to retain the local state. They produce a new reviewable plan. They may resolve already managed A files only; they cannot adopt unknown files, override a seed, or change ownership. The application code never chooses a resolution for the researcher. Diffs and resolutions can contain local material and must remain in the authorized project's context.

Automatic merging is bounded to inputs of at most 1 MiB and 10,000 newline characters when both sides changed; otherwise explicit resolution is required. Phase 2 manifest/file bounds remain in effect. These limits concern update processing and do not impose scientific-report length limits.

## 4. Backup, staging, and commit order

Apply uses an exclusive advisory lock on the existing installation directory, without creating a persistent lock file. It rejects cross-filesystem paths, nested Git checkouts, path aliases, unsafe links, special files, and invalid modes through the reused Phase 2 validators and the descriptor-anchored storage layer. Git metadata paths are never update targets. Root and locked installation-directory identities are rechecked before mutation; stage and destination identities are rechecked before publication.

For a fresh operation identifier, retain:

```text
.research-framework/
├── installation.json
├── baselines/<upstream_sha256>
├── backups/<operation_id>/<index>.bin
└── transactions/<operation_id>/
    ├── journal.json
    ├── after/<index>.bin
    ├── stage/<index>.bin
    └── restore/<index>.bin
```

Recovery objects live under private manager-owned directories. Backup bytes preserve local edits; the journal records original modes, absence, parent identities, and created-directory intents/identities. Verify the complete before/after backup set before starting target mutation, and recheck applicable backups at write boundaries. Failed backups cannot authorize a target change. Exact new upstream bytes are retained separately from merged outputs. No backup or journal is automatically pruned.

Journal transitions are `PREPARING` → `APPLYING` → `COMMITTED`. The checksummed, bounded journal is replaced atomically and synced; file staging and target directory changes are synced too. Each target has durable write intent followed by completion/identity evidence. Installation receipt/generation is written last, after payload files, and final results are rechecked before the committed journal state. A no-change release is a true no-op.

Multiple files are not changed as one global atomic filesystem operation. The journal identifies incomplete work. Normal exceptions attempt guarded recovery; an interruption leaves durable evidence for explicit recovery. An exception's operation identifier lets the caller inspect the actual journal rather than infer success or failure from the exception alone. A durable `COMMITTED` operation is not automatically reversed as unfinished work.

## 5. Guarded recovery and rollback

Preflight every affected target and every required backup before restoring any target. Reject later content, permission, identity, parent, root, or receipt changes, corrupt backups/journals, unregistered paths, or stale recovery plans. Even rewriting identical bytes is treated as a later local edit unless a completed child rollback proves the current inode/token. Do not offer a blanket force overwrite.

Recovering untouched `PREPARING` work marks it `ABORTED` without requiring incomplete backups. Otherwise enter `ROLLING_BACK`, restore affected payload files in reverse order, and restore the original receipt last. Record restoration intent and result per file so an interrupted rollback can resume. Known journaled write/restore gaps may match either verified before or after state; unknown states require manual inspection.

Rollback removes an operation-added file only while it still matches its recorded result. Remove a recorded operation-created directory only while its identity matches and it is empty. New user files in that directory remain. Never recursively replace a project directory. Already rolled-back/aborted operations are no-ops. Backups and the full audit lineage remain available.

Roll back the current head first. After a later update is rolled back, an older rollback is allowed only when the completed child's journal proves the present file token and restored receipt lineage. Matching content alone is insufficient. Pending operations block new updates until recovered or explicitly investigated.

## 6. Validation and limits

Run from the development repository root:

```sh
PYTHONPATH=src python3 -B -m unittest discover -s tests -v
```

The combined suite currently contains 103 tests: 102 pass and one actual Unix socket creation test is skipped by the sandbox's `bind` restriction. Socket metadata rejection is separately covered. New tests exercise disjoint/conflicting/binary edits, local deletions and retirements, mode preservation, exact upstream retention, immutable and retired seeds, ownership changes, stale/forged plans, lock contention, no-atime dry-runs, verified backup failures/corruption, stage/link/parent/state-directory replacement, interruptions before/after writes and commit, interrupted rollback, rollback after later local edits, multi-operation lineage, unsupported filesystem metadata, and preservation of scientific records and Git contents. Fixtures are temporary synthetic projects; reference projects are never mutation fixtures.

The tested environment remains the existing Python 3.9.18 on Linux/WSL. No dependencies or environments are installed or rebuilt. The implementation requires no-atime support, descriptor-relative operations, advisory locking, directory fsync, and a single filesystem for project targets and operation storage. Supported project/payload entries use the current process UID/GID and ordinary file modes; ACLs, extended attributes, and non-default filesystem ownership are rejected rather than silently lost on replacement. Unsupported capabilities fail closed. Broader filesystem-metadata preservation requires later implementation and acceptance evidence.

Advisory locks serialize cooperating engine instances. The engine checks identities/content before and after writes; it cannot provide a globally atomic snapshot or serialize a noncooperating process in the final check-to-rename window. Run mutations while external editors/jobs are quiescent. Checksums are integrity checks, not authentication against an attacker who can rewrite all manager state. Missing/corrupt audit metadata, unknown intermediate states, or unverified external edits require manual inspection; they are not permission for destructive cleanup.

This module operates only on registered installations. Separate implemented modules
provide [initialization](INSTALLATION.md), [metadata-free migration](MIGRATION.md),
[reporting](REPORTING.md), and the CLI/release workflow. Archive extraction and a
publisher signature/discovery trust policy are not automatic update operations;
operators select and verify a trusted release. The earlier 103-test result is a
historical Phase 3 checkpoint. [Complete acceptance](ACCEPTANCE.md) records the
subsequent autonomous implementation and actual platform/deployment limits.
