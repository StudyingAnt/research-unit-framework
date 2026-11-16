# Applying the 2.0.1 Aim-Guidance Hotfix

These instructions are for a project session applying an explicitly authorized
update. Framework development does not itself authorize changes to any research
project. No assessed or protected project is updated by preparing this guide.

## Scope

Use a clean checkout of tag `v2.0.1` or its verified release archive as SOURCE.
Resolve SOURCE and PROJECT to actual absolute Linux paths in the project session;
do not reuse another project's paths. Work with an existing Python 3.9+ interpreter.
Do not install dependencies or change environments for this policy hotfix.

First inspect PROJECT/.framework/manifest.json and the actual local instructions.
It must be a valid format-2 installation, normally version 2.0.0. Confirm its
recorded upstream snapshots exist and verify. Missing/corrupt/older metadata is
not permission to reconstruct a receipt or overlay the template directory.
Do not use this update procedure for a 1.x/v0.5 installation.

Relative to the published 2.0.0 template, only these managed files change:

- AGENTS.md: operational Aim-scope guidance; also includes the already committed
  optional scientific-critical-thinking skill guidance.
- coordination/COORDINATION.md: consult that rule while discussing Aims.
- templates/aim.md: question/enabling objective, scope/completion boundary and
  flexible Strategy/Tactic prompts.

No scripts, report templates, CSS, managed-path list or metadata format change.
Source EN/KO specifications/philosophy and release documentation are for reference;
the updater does not copy them into existing projects. Version/snapshot state and
affected-file backups are administrative changes in .framework/.

## Preview first

Use the source release's updater, not a recursive template copy:

```bash
python3 /absolute/SOURCE/tools/update_project.py /absolute/PROJECT
```

Preview is read-only. Review every action/diff and save the displayed plan_digest
in the project session if you intend to require that exact reviewed plan. Expected
file-content writes are limited to the three files above. A project that already
contains some upstream edits can have fewer writes. Local differences in other
managed files should remain KEEP_LOCAL or UNCHANGED. Unexpected changes require
inspection before applying. Do not override a conflict merely to complete an update.

The updater also compares file permissions. Mixing a checkout with an archive
extracted under a different permission convention can show mode-only changes in
otherwise unchanged files. Inspect those differences and use a consistent source
extraction/permission convention; do not silently change project permissions as
part of this policy hotfix.

## Preserve local policy additions

Compare the recorded old upstream snapshot, local file and SOURCE/template/PATH
for each conflict. Preserve project-specific scientific-review and execution-
context instructions while integrating the common Aim guidance. Do not use a
blanket keep-local policy or overwrite the local files with upstream versions.

Prepare explicit merged files outside the project, with private permissions if
they contain local research instructions. For example, add the same reviewed
resolution option to both preview and apply:

```bash
python3 /absolute/SOURCE/tools/update_project.py /absolute/PROJECT --resolve AGENTS.md=/absolute/private/merged-AGENTS.md
```

Use an additional --resolve PATH=FILE for each other conflicted managed file.
If wording requires an ambiguous scientific or methodological choice, stop that
resolution and ask the researcher. A text merge cannot adopt scientific policy
on the researcher's behalf.

## Apply the reviewed plan

After project-level authorization, run with the exact digest and the same
resolution options, if any:

```bash
python3 /absolute/SOURCE/tools/update_project.py /absolute/PROJECT --apply --expect REVIEWED_PLAN_DIGEST
```

The updater rechecks the plan, verifies affected originals in
.framework/backups/TIMESTAMP-ID/ before managed-file changes, and records 2.0.1
only after its writes. Stop competing administrative writers during application.
There is no automatic rollback service: retain the backup path, changes.json and
previous-manifest.json. Follow [the ownership/backup procedure](OWNERSHIP_AND_UPDATES.md)
for an interruption, inspected retry or manual restoration. Never reset the project.

## Verify and report back

Check installation version 2.0.1, the three resulting policies/templates and
preservation of local additions. Confirm the official new upstream snapshots are
distinct from any locally merged results. Re-run the same-release preview:

```bash
python3 /absolute/SOURCE/tools/update_project.py /absolute/PROJECT
```

It should have no conflicts or further content changes. Inspect the actual diffs
and backup records; do not infer success merely from the version string.

Verify project-owned plans/Research Map/ID registry, settings, reports/revisions,
figures/analyses/data and independent scientific repositories remain unchanged.
Do not run new_unit.py, rerender reports, install skills, reorganize records or
execute science to validate this policy-only update. Tactic-level reporting,
stable identities and optional Run/report-revision meanings stay unchanged.

Existing Aims do not need splitting or rewriting. Apply the guidance to future
planning; any reassessment of an existing Aim is a separate researcher decision.
An empty AST registry remains empty. Summarize the actual changed files, installed
version, local additions retained, backup location and any unresolved issues.

## Prompt for a project session

The researcher may copy this instruction after the release has been validated:

```text
Update this project from its verified 2.x installation to released Framework
v2.0.1, following docs/UPDATE_2.0.1.md from the verified v2.0.1 source.
Resolve the actual project/source paths and inspect installed metadata and local
instructions first. Preview and review every change before applying. Preserve
local scientific-review and execution-context additions; explicitly merge any
conflicts rather than overwriting files or keeping all local versions blindly.
Keep project-owned plans, settings, IDs, reports, analyses and repositories intact.
Do not split existing Aims, regenerate reports, run science or install dependencies.
Stop for any genuinely ambiguous scientific decision. Apply the exact reviewed
plan, retain the verified backups, then check version 2.0.1, local modifications
and a same-release preview with no further content changes. Report the actual
changed files, preservation checks, backup path and unresolved issues in Korean.
```
