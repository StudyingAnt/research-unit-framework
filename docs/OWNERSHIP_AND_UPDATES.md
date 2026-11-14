# File Ownership and Safe Updates

**Decision date:** 2026-11-14  
**Status:** Adopted policy; Phase 2 adds read-only validation, with mutation tooling deferred  
**Related contracts:** [Architecture](ARCHITECTURE.md), [primary specification](RESEARCH_PROGRAM_FRAMEWORK_v1.1.md), [requirements traceability](REQUIREMENTS_TRACEABILITY.md)

This policy governs future initialization, framework upgrades, migration, and recovery. It does not authorize any operation against a project. An operation must stay within the user's named project and approved scope. Reference projects designated by the user or checkout-local development context remain strictly read-only; their locations belong only in that Git-excluded context.

## 1. Ownership classes

Classify explicit files and their roles, not entire trees by filename resemblance. A release manifest identifies eligible payload files; the installation receipt records the adopted classification. Neither document grants ownership of scientific records or unrelated local files.

| Class | Meaning | Creation and update rule |
|---|---|---|
| A: Framework-managed | Generic runtime, shared policy/defaults, schemas, reusable templates, and thin helpers explicitly registered as managed | Install a verified payload; later compare upstream base, local content, and new upstream content. Preserve modifications and reject unresolved conflicts |
| B: Project-owned scientific records | Research direction, plans, decisions, reports, primary/derived evidence, execution and provenance records, manuscript work, scientific source | Never replace, remove, reformat, re-render, or revise through a framework upgrade. Authorized research helpers may administer records only within a separately agreed scientific scope |
| C: Project-specific configuration | Local research instructions, project paths/settings, environment/HPC runbooks, journal choices, reporting overrides, repository configuration | Preserve user values, unknown keys, local semantics, and existing locations. Propose schema/configuration changes explicitly; apply only a reviewed, authorized configuration change |
| D: Initialization-only | Empty scientific scaffolds, root bridges, initial project README, directory markers, and default local configuration seeds | Create only when absent during authorized initialization. Never overwrite or recreate during upgrade. After creation, active ownership becomes B or C according to purpose |

An unknown or unregistered existing file is **unowned and preserved**, including one located under a normally managed directory. Do not infer A from a common filename, an old starter resemblance, or the presence of installation metadata. Scientific records and local configuration cannot be promoted to A merely to make an upgrade succeed.

## 2. New-project defaults and legacy treatment

The following are planned installed-project paths, not files created by Phase 1:

| Path or role | New-project ownership | Existing-project treatment |
|---|---|---|
| `.research-framework/runtime.pyz`, named shared policy and generic documentation files | A | Add only after collision checks and an approved installation/migration plan |
| Named official report templates, report stylesheet, and thin helper files | A | Establish the baseline and local differences first; do not overwrite locally improved tools/templates |
| `coordination/plans/AIM_TEMPLATE.md` and other explicitly named reusable templates | A only for the reusable template itself | Never extend this exception to actual Aim plans or other scientific records |
| Root `AGENTS.md`, optional `CLAUDE.md`, `REPORT_TEMPLATE.md` | D seeds, then C | Preserve existing project instructions and presentation requirements; reconcile conflicts through reviewed changes |
| `PROJECT_INSTRUCTIONS.md`, `framework-project.json`, project figure/compute/HPC runbooks and local overrides | D seeds where supplied, then C | Preserve values, paths, local rules, unknown fields, and legitimate conventions |
| Root project `README.md` and optional ignore-file seeds | D, then B or C according to content | Preserve existing documentation and version-control policy |
| `coordination/plans/RESEARCH_MAP.md`, initially empty `ID_REGISTRY.json` | D empty scaffolds, then B | Do not invent scientific direction or register speculative IDs. Add absent scaffolds only when the migration scope explicitly includes them |
| Actual Aim/Workstream plans, manuscript records, approvals, and strategic decisions | B | Preserve identity and content |
| Existing and new report Markdown, HTML, PDF, revisions, and report validation records | B | No automatic regeneration, translation, status changes, or contract conversion |
| Analysis results, figures, logs, Run manifests, effective configurations, transfer records | B | Preserve bytes, provenance, and existing layout; no housekeeping during updates |
| Scientific code/checkouts and repository-local configuration under `repos/` or elsewhere | B or C; independent repository authority | No checkout edits, moves, nested traversal for update writes, cleanup, commit, pull, or branch/history changes |
| Data, protocols/resources, environments, controlled primary records, informal notes | Project/institution-owned B or C as applicable | No installation, copying, relocation, environment rebuild, or disclosure through an update |
| Unregistered local templates, custom scripts, hidden files, symlinks, or other additions | Unowned | Preserve and surface any destination collision |

The common policy lives separately from project-owned root bridges. Project-specific presentation can adapt the shared contract but must retain approved scientific depth, bilingual outputs, and absence of page-count requirements. Existing deviations are surfaced during migration; they are not silently normalized.

Ownership transitions are recorded. A D creation receipt remains historical evidence, but it is not continuing permission to rewrite the resulting B/C file. Empty-directory markers are never a reason to remove a populated directory. Local deletion of a D seed is not repaired automatically.

## 3. Generated installation state

Generated state inside `.research-framework/` belongs to the installation manager and is separate from upstream release payload. A release cannot replace this state as if it were a template. The state is not an authority for scientific claims.

| State | Required information and protection |
|---|---|
| Installation receipt | Framework release, specification and metadata schema versions; release source/digest; project identity; operation history; file ownership and installation results |
| File records | Exact path, ownership role, file kind and relevant permissions, old/new upstream identity, installed content hash, preserved local differences, pending decisions |
| Upstream baselines | Exact verified upstream bytes keyed by content hash and release provenance, retained for future three-way comparison |
| Operation plan | Operation type, target root, source release, preconditions, intended changes, diffs, classifications, conflicts, configuration decisions, protected paths |
| Journal | Operation identity, approved plan digest, affected paths, staged/backup references, per-file progress, recovery state, final installation-state transition |
| Backup | Original bytes or symlink identity where relevant, permissions, existence/absence, parent-directory creation records, and verified hashes for the affected set |

Keep the upstream baseline distinct from the locally merged installed result. Otherwise the next upgrade could misidentify local changes as official upstream content. Preserve local deletions as explicit state, not as missing metadata to repair.

Preserve backups and journals across release updates; never auto-prune them. They may contain project-specific content and must remain in the appropriate project storage, outside public framework sources and release artifacts. This is framework-change recovery, not backup of a project's scientific data. Unknown files inside the installation area remain unowned.

If state is missing, corrupt, inconsistent, or from an unsupported schema, stop ordinary upgrade and offer an inspected recovery/migration plan. Do not synthesize a successful installation receipt from the current local files.

## 4. Upgrade decision rules

Let B be the verified previous upstream file, L the observed local state, and N the new upstream file. Absence and file kind are states, not empty file contents. Compare bytes before interpreting text; never silently normalize line endings or encoding to claim an exact match.

| Condition for a registered A file | Planned outcome |
|---|---|
| L = B and N exists with changed content | Update to N, with backup and preconditions |
| L changed and N = B | Keep L and record preserved local modification |
| L = N | Already at the desired content; retain correct baseline/state history |
| B, L, N differ as mergeable text | Produce a three-way merge candidate and diff |
| Text merge is conflict-free | Apply only as a disclosed action in the authorized plan; preserve local changes and retain N as the new upstream ancestor |
| Text merge conflicts | Leave target untouched; require a reviewed resolution and a revalidated plan |
| Binary content changed on both sides, file kind changed, or merge base is unknown | Require manual resolution; no automatic replacement |
| N introduces a path and L is absent | Add only if the path, parent types, and ownership checks pass |
| N introduces a path occupied by an unregistered file | Unmanaged collision; preserve L even if similarly named |
| L was deleted locally and N is unchanged from B | Preserve the local deletion |
| L was deleted locally and N changed | Surface a delete/change conflict; do not recreate automatically |
| N removes the file and L = B | Propose explicit retirement of this registered file, with backup; do not silently delete |
| N removes the file and L changed | Delete/change conflict; preserve L |
| B/L/N are unchanged | No payload write required |

A conflict-free text merge proves textual compatibility only. A C instruction/configuration change requires semantic review even if a merge engine reports no conflicts. B and D records are not merge targets for an ordinary framework upgrade. Template changes apply to future units, not existing scientific records.

Do not provide a blanket overwrite path that silently discards modifications. Any user-authorized replacement must name the affected files and consequences in a concrete plan, preserve the original state, and remain within the requested scope.

## 5. Read-only planning and dry-run

1. Resolve the intended project and operation, applicable local instructions, installation state or legacy status, and verified release identity. Do not auto-detect a different target and mutate it.
2. Inspect the candidate file allowlist and relevant configuration without bulk-reading scientific data or traversing independent repositories for update writes.
3. Validate release contents and planned paths before extraction or staging. Reject absolute/archive-escaping paths, parent traversal, unsafe links, duplicate or conflicting destinations, and unsupported file types.
4. Classify every candidate as update, add, keep, merge, conflict, explicit retirement, or reviewed configuration change, and show the reason and diff.
5. Emit the plan and unresolved decisions. Do not create project files, directories, caches, locks, backups, metadata, temporary merge files, or repair state during dry-run. In-memory work is permitted. Saving a plan is a separate explicit output request, not an implicit side effect of dry-run.

A plan must be reviewable and bound to the actual root, release digest, and observed file states. Text suggesting a later command is not evidence that it has been executed.

## 6. Apply, failure, and interruption

An authorized apply operation must:

1. Validate the selected plan, release digest, required resolutions, target identity, expected ownership, and supported metadata schema.
2. Acquire a project-scoped mutation lock and recheck the planned content, file kinds, parents, and permissions. Abort stale plans rather than overwrite intervening changes. Never follow a symlink or hard-link alias to mutate an external or protected file.
3. Build and verify backups of the exact affected set before the first target change. Record absent files and newly created directories. Insufficient space or backup failure stops the write phase.
4. Stage validated content on the appropriate filesystem, record journal progress, and replace files atomically where supported. Reject unresolved conflict markers and unauthorized paths.
5. Recheck preconditions at the write boundary, record per-file outcomes, and validate the resulting affected set. Cooperating tool locks do not prevent all external writers; fail conservatively when changes are detected.
6. Finalize installation state only after all required changes and checks succeed. Never mark a partially applied or conflicted migration as an active v1.1 installation.
7. Preserve diagnostics and recovery information after failure. Restore safely where possible, or leave an explicit incomplete state and a guarded recovery plan. Retain evidence instead of cleaning it away.

Multiple file replacements are not one globally atomic filesystem operation. The journal and verified before/after state must support crash recovery. User files created during an interrupted operation are preserved. No update step invokes scientific execution, report rebuilding, package installation, remote access, or Git mutation.

## 7. Backup and guarded rollback

Rollback plans name a completed or interrupted operation and inspect its journal and verified backups. Restore only files that operation changed, including their prior existence and relevant permissions. For an added file, removal is allowed only if it still matches the recorded operation result. Remove an operation-created directory only if it is still empty.

Before restoring, compare each current file with the operation's recorded post-state or known journaled intermediate state. Later edits, later upgrades, new files, missing/corrupt backups, or uncertain state require reviewed conflict resolution. Do not overwrite later work or roll back scientific records that were never part of the operation. Restore the corresponding installation-state lineage while retaining the audit trail.

A rollback dry-run obeys the same no-write rule as upgrade planning. Backups remain available after rollback. Automatic cleanup, recursive directory replacement, and project-wide reset are outside this recovery contract.

## 8. Migration without v0.5 metadata

Migration is a separate operation; it cannot pretend an ordinary upgrade base exists.

1. Inventory relevant legacy framework files and local improvements, configuration/instructions, registered IDs, report/evidence locations, and independent repositories without modifying them.
2. Compare against an observed, provenance-recorded Starter v3 / Framework v0.5 baseline. Exact hashes support comparison, not proof of a historical installation date or official release commit.
3. Classify exact matches, local changes, missing files, unknown ancestors, and destination collisions. Keep proposed research ideas distinct from registered, approved IDs.
4. Prepare ownership adoption and root-instruction reconciliation explicitly. Preserve improved reporting. Use a known ancestor for text merging only when its applicability is established; otherwise require manual resolution.
5. Propose optional empty Research Map/registry scaffolds separately. Existing project content is not permission to draft or adopt a Narrative, Workstream, manuscript, or scientific priority.
6. Resolve conflicts and secure approval for the concrete migration plan. Apply with the same path checks, revalidation, backup, staging, journal, and rollback contract as upgrades.
7. Verify existing scientific records and repositories are preserved. Record legacy provenance limits, the selected release, retained local modifications, and ownership decisions before activating installation metadata.

Do not move or rename existing units, repositories, output directories, primary records, or runbooks. Do not renumber AST IDs, reinterpret a report revision as a Run, regenerate old reports, convert old findings into new claims, copy restricted records, or rebuild environments. Old reports retain their historical contract and status until a separately authorized report revision.

## 9. Acceptance boundary

Later automated acceptance must exercise every merge decision, unmanaged collisions, local deletions, unknown bases, failed backups, interrupted writes, concurrent edits, path/link attacks, state corruption, repeat invocation, and guarded rollback using synthetic projects. Preservation checks cover scientific records, local instructions/configuration, independent Git contents/history, untracked files, and unrelated paths.

Phase 1 adopted this policy and checked its consistency with the architecture and bilingual specifications. Phase 2 preserves the reviewed generic baseline and implements read-only manifest/path/file validation with component tests. It creates no installation metadata and implements none of the initialization, upgrade, migration, merge application, backup, or rollback operations governed here.
