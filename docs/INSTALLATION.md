# Installation and Standalone Runtime

The standard-library administration runtime supports Python 3.9+ on Linux/WSL.
It does not install scientific environments or require a project-root repository.
Reporting has separate optional dependencies. Other operating systems are not
claimed as supported by the descriptor-relative update engine.

Build from the source checkout:

```bash
PYTHONPATH=src python3 -B -m research_program_framework build-release dist/rc
python3 dist/rc/newproj.pyz new /absolute/new/project
```

The destination must be absent. Empty existing directories are refused too.
Creation verifies the payload, writes a disposable sibling staging directory,
syncs it, and uses Linux no-clobber directory rename. No scientific IDs, scope,
Git history, environments, or remote operations are created. A failed creation
never overlays an existing directory. A process killed during staging can leave
an unpublished sibling staging directory; inspect before removing it.

Each release contains `payload/`, `manifest.json`, `newproj.pyz`, and checksums.
The zip application embeds the same editable starter source and inert legacy
ancestor; it can create projects without this development checkout. Installed
helpers delegate to `.research-framework/runtime.pyz`. Checksums prove integrity
against an expected manifest, not publisher authenticity. Only use trusted code.
Builds from dirty source are development artifacts; the recorded commit alone
does not identify uncommitted changes. Published artifacts require a clean source
revision and acceptance verification. No license grant is invented by a build.

For an existing registered installation, use an unpacked verified release:

```bash
python3 newproj.pyz update-plan /absolute/project --release /absolute/release
python3 newproj.pyz update /absolute/project --release /absolute/release --plan-digest DIGEST_FROM_PLAN
```

Plans go to standard output and never write into the project. Apply recomputes
the plan and requires the exact reviewed digest. Unresolved conflicts refuse
application. `--keep-local PATH` explicitly retains a registered managed file;
`--resolution-file FILE` maps managed paths to reviewed content-file paths or null
(keep local). Use identical options for plan/apply. Seeds and unknown collisions
cannot be overridden. Python callers can supply the same reviewed bytes directly.
Rollback and recovery use the corresponding `*-plan` command followed by its
mutation command with the returned digest and operation ID. Preserve all backup
and journal state; see [the update engine](UPDATE_ENGINE.md).

The standalone zip application is the primary self-contained delivery. An optional
regular source-package installation uses an explicit verified `--release` directory
for initialization/migration; editable development installs can use the checkout.
It never searches unrelated workstations for missing starter assets.
