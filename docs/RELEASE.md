# Git Versioning and Release Procedure

`VERSION` is the implementation's semantic version. The scientific specification
remains v1.1 and each JSON format has an independent schema version. The source
package exposes its corresponding PEP 440 version for optional packaging.
One editable starter source and one runtime package generate all release payloads.
The observed v0.5 snapshot is an immutable migration ancestor, never current policy.

Develop on a `codex/` branch and commit logical tested milestones. Before every
push, run the public-source audit over current candidates and every unpublished
Git blob. Review content manually as well; patterns cannot establish absence of
all confidential science. Local development context and protected reference paths
must never enter Git, starter payloads, fixtures, runtime bundles or release assets.
Do not force-push, rewrite published history or mutate scientific repositories.

Acceptance includes both Python component/failure tests and archive-only
installation, migration, update and rollback tests. Actual bilingual rendering,
font/glyph/math/figure inspection and scientific-governance checks supplement the
test suite. Preserve the record of the chosen environment and limits. A pass
does not certify all science, external HPC policy or every agent loader.

Build an RC from a clean, committed source revision:

```bash
PYTHONPATH=src python3 -B -m research_program_framework build-release dist/research-program-framework-VERSION --require-clean
PYTHONPATH=src python3 -B -m research_program_framework audit-public --archive dist/research-program-framework-VERSION.tar.gz
```

Build headers, ordering, embedded runtime and gzip timestamps are normalized.
Manifests record the exact source commit and file bytes/modes/ownership.
Uncommitted development builds are not tagged releases. Release archives contain
no workstation ownership metadata, research records, fonts or installed scientific
dependencies. SHA-256 verifies integrity against an expected artifact, not identity
or publishing authority. Do not invent a license or assert unestablished rights.

Only merge to main after local acceptance and development-branch CI succeed.
Recheck upstream main before merging, preserve history and resolve changes
explicitly. Set the final version, record the changelog and acceptance evidence,
run the complete suite after final changes, then create an immutable annotated
tag. Do not tag a final release while critical capabilities or safety tests fail.

The verification workflow tests Python 3.9 and 3.11 and audits public content.
Optional reporting tests use an explicitly selected environment locally; CI does
not silently claim they ran without fonts. A version tag triggers clean-source
build and GitHub Release publication using the workflow's scoped repository token.
It uploads the archive, archive checksum, standalone zip application and payload
checksums. Existing releases are refused rather than silently replacing assets.
The developer checkout needs no personal API token for that workflow. Verify
actual workflow completion and release asset presence; a pushed tag alone is not
a completed GitHub Release. If Actions permissions/credentials block publication,
leave the tag/artifacts intact and report that operation's exact blocker.

After full implementation/acceptance, an explicitly authorized real target may
undergo its final administrative migration. Keep the original reference read-only.
Inspect an exact plan, resolve all conflicts without scientific decisions,
verify external recoverable backups before modification, preserve scientific
files and independent histories, check installed version and retained rollback.
If those conditions cannot be established, leave that target unchanged and
continue independent release work. Never regenerate historical reports to make
a migration appear successful.
