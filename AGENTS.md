# Framework Development

`template/` is the single editable project template. These development rules
must never be copied into scientific projects; use `template/AGENTS.md` there.

## Context and authorization

Explicitly check for and read `DEVELOPMENT_CONTEXT.local.md` at the checkout root.
It is Git-excluded and holds workstation paths, protected references and the HPC
manual location. Never copy its facts into public sources, fixtures or releases.
A fresh clone needs no other workstation's context.

The researcher authorizes the clean template-first redesign, tests, commits,
privacy-reviewed pushes and a new release. Use a `codex/` development branch and
validate before updating main. Preserve prior Git history and tags. Old
installations have no automatic conversion path. Do not invent a software license.

Both protected research/reference projects remain strictly read-only. Do not
migrate, update, reorganize or render into them. Test synthetic temporary projects.
Existing migration recovery records remain private and untouched.

## Scientific requirements

Read both v1.1 specifications before changing the design; English is primary.
Preserve Narrative, flexible Workstreams, AST, material Specifications, optional
Runs, Research Map, stable IDs, manuscript evidence and honest provenance.
Coordination challenges weak arguments and proposes alternatives; only explicit
researcher-approved decisions enter formal records. Sessions communicate through
persistent files; no mandatory chat handoff or extra summary is required.

Preserve detailed eleven-section EN/KO Markdown/HTML/PDF reports, publication
figure defaults, revision history and explicit rendering failures. There is no
page-count target, minimum or maximum. Scientific, bilingual and visual review
remain explicit human/agent work; software checks cannot establish scientific
truth. Preserve independent scientific repositories and their entry points.

## Engineering

Keep the architecture small: readable Markdown, one template, ordinary Python
scripts and standard-library creation/update tools. Remove obsolete migration,
compatibility, installation archives and phase documents. Do not rebuild them
without a concrete unmet requirement. Updates touch only explicit managed files,
preserve local changes and scientific records, offer read-only previews and
three-way comparison, and verify affected-file backups before modification.

Use Linux-native tools in WSL. Verify failures before changing environments.
Before changing HPC instructions, read the manual named in local context. Keep
remote submission, monitoring and transfers human-operated; preserve job-internal
initialization and separate environment provisioning from scientific jobs.

Write code/comments/docs in English except required Korean scientific artifacts.
Communicate in Korean. Audit the full publication candidate for private content
before every push. Run the complete meaningful synthetic suite before release;
distinguish local software tests from scientific or remote HPC validation.
