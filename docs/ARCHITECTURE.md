# Template-First Architecture

The scientific design remains [v1.1](RESEARCH_PROGRAM_FRAMEWORK_v1.1.md), with a
[Korean companion](RESEARCH_PROGRAM_FRAMEWORK_v1.1_ko.md). Implementation 2.0 is a
new baseline. Earlier metadata/installation formats are unsupported and no
migration, legacy adoption or historical conversion command exists.

## One visible template

`template/` is the only editable project template and policy source. Its Python
scripts are ordinary inspectable source, not wrappers around a bundled runtime.
Root `tools/newproj.py` copies it. `newproj` is a convenience command; a small
optional user config remembers the projects parent. No Python package install is
required. A complete release is the same browsable tree as the checkout.

The root AGENTS.md governs framework development; template/AGENTS.md governs
research. PROJECT_INSTRUCTIONS.md contains project-specific settings and authority.
CLAUDE.md points explicitly to the same durable policies. There is no second
hidden policy tree, schema directory, registry service or installed runtime ZIP.

## Ordinary research records

Research Map, Aim and manuscript plans are readable Markdown. Coordination uses
these files and selected AST reports directly, with explicit researcher approval
for adopted decisions. Workstream/Aim and manuscript/evidence relationships can
be many-to-many. No mandatory session handoff document exists. A small ID registry
remembers allocated/reserved/retired Tactics; ID creation checks existing outputs
as well. Optional Runs and report revisions have different identities.

`new_unit.py` reserves an ID before writing draft files; an interrupted creation
never frees it for reuse. Inspect and complete that reserved unit manually. An
allocation approval is not approval of unfilled scientific Specifications.

## Minimal administration

`template-manifest.json` lists the version and eligible managed files.
`.framework/manifest.json` in a new project records that version and exact prior
upstream hashes/modes. Immutable `.framework/base/HASH` files retain ancestors.
`tools/_framework.py` contains copying and update planning/application;
`tools/_merge.py` supplies conservative in-memory line merging. The project
`tools/project_common.py` contains small path/read/write/lock helpers used by
these scripts. There is no package manager or generic transaction engine.

A preview compares B/L/N in memory. Apply rechecks it under a cooperating-writer
lock, verifies changed-original backups, writes individually staged files, adds
immutable upstream snapshots and replaces the small manifest last. Snapshot
objects keep the prior manifest usable across an interrupted update. Retry after
inspecting a fresh preview; backups support manual restoration when needed.
There is no automatic rollback, resumable journal protocol or historical adoption.

## Reporting

`build_reports.py` checks paired Markdown and small report metadata, transforms
Pandoc's parsed math/images, verifies actual fonts and local figure exports,
renders HTML/PDF, and archives one complete immutable revision before publishing
latest convenience copies. `current.json` is written after those copies. Failed
publication leaves the complete revision available for inspected copy restoration.
No report is rebuilt by a framework update. Report sources and archives remain
project-owned. Optional dependencies are separate from core administration.

## Boundaries

Standard-library administration is tested on Linux/WSL with Python 3.9 and 3.11.
Path/link and stale-content checks protect ordinary single-user projects and
cooperating scripts. They do not provide a security boundary against a malicious
concurrent process, network filesystem semantics, arbitrary hardware/power-loss
failures, or full ACL/xattr backup. Backups preserve affected bytes/modes/existence,
not all scientific data. Stop competing editors/writers during updates.

Existing protected projects remain read-only during framework development.
Checkout-local paths and policy manual locations belong only in the ignored
DEVELOPMENT_CONTEXT.local.md, explicitly discovered by root AGENTS.md. No real
research content, fonts, account settings or recovery records enter releases.
