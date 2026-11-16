# Baseline-2 Acceptance

Validation uses synthetic temporary projects only. Existing protected research
projects, historical reports, scientific repositories, data and recovery records
are outside the redesign scope and are not test fixtures.

## Observed local checks

The final suite contains 44 tests: all 44 pass with rendering enabled. The core
Python 3.9 run passes 38 with six optional renderer tests explicitly skipped.

- Python 3.9 standard-library project creation/update/ID and report-source checks.
- Python 3.11 renderer-enabled suite with Pandoc 2.12, WeasyPrint 66.0,
  Matplotlib 3.11.2, Pillow and FontTools. Actual installed Noto Serif / Noto Serif
  KR and Arial assets were used; no fonts or workstation paths are distributed.
- Creation at configured/default/explicit destinations, standalone copied helpers,
  visible Coordination policy, empty unadopted planning, no root Git initialization.
- Stable IDs, occupied/retired IDs, same-ID resume, explicit allocation approval
  and non-reuse after interrupted draft creation.
- Detailed eleven-section paired reports, table-only COMPLETED/NOT_EVALUATED,
  numeric/metadata/math checks, missing assets/fonts and unsupported math failures,
  600 dpi PNG validation, intended physical image width, separate previews,
  immutable revisions and protection of unarchived local output edits.
- Read-only update previews, unchanged/local/deleted files, disjoint merges,
  overlapping/binary/delete-change conflicts, explicit merged resolutions,
  unmanaged collisions, seeds/science/Git protection, symlink/hard-link refusal,
  stale plans, verified backups and inspected retry after interrupted writes.
- Synthetic HTML browser inspection with external requests blocked: loaded
  EN/KO fonts, no horizontal overflow/broken images/page errors. PDF visual review
  included inline/display equations, figures, tables/captions and both languages.
  Short-table pagination was adjusted after inspection; page counts are never
  pass/fail criteria or required to match across languages.
- A framework update of the synthetic visual project preserved its archived
  report bytes, followed by a new revision under the same AST.

Run core checks with `python3 -B -m unittest discover -s tests -v`. Set
RPF_RENDER_TESTS=1 in an existing reporting interpreter for actual rendering;
RPF_PANDOC, RPF_FONT_EN, RPF_FONT_KO and RPF_ARIAL can select verified local tools
and fonts for tests. Without that opt-in, six renderer tests are explicitly skipped.
No dependencies are installed by the framework helpers.

## Release checks

### 2.0.1 Aim-guidance hotfix

The hotfix changes only three installed managed texts: AGENTS.md,
coordination/COORDINATION.md and templates/aim.md. Runtime scripts, the managed
allowlist, report templates/CSS and metadata format remain unchanged. EN/KO design
and philosophy were reviewed for corresponding default scope, researcher-chosen
broader Aims, enabling objectives, flexible composition and preservation of
scientific identity/reporting.

Synthetic acceptance used the exact published 2.0.0 Git template as an ephemeral
ancestor. Linux tar extraction and the checkout had matching permissions; the
preview also exposed mode-only changes when a different extraction convention
was tested. The [project update guide](UPDATE_2.0.1.md) explains that distinction.
The checks passed for current new-project propagation, one Strategy/Tactic and
multiple Strategies/Tactics, enabling-work draft creation without an invented
hypothesis, and optional Runs remaining optional. A 2.0.0-to-2.0.1 update preserved
local review/context additions, project settings, scientific records, stable IDs
and archived reports byte-for-byte. The three affected originals were verified
in backups; repeat preview had no further content changes. An intentionally
overlapping local scope addition blocked all writes, then accepted explicit
merged bytes. No actual research project was updated.

These observations validate propagation and administrative behavior. They do not
establish the quality or consistency of an assistant's scientific scope choices;
that remains a researcher-reviewed planning decision. Version-transition tests
use an explicitly synthetic 2.0.0 starting number, independent of the current
release, rather than retaining a legacy baseline in the repository.

The first remote run stopped before testing: ubuntu-latest selected Ubuntu 26.04,
where setup-python could not provide Python 3.9. The CI-only runner was pinned to
Ubuntu 22.04 after checking the [official Python build manifest](https://github.com/actions/python-versions/blob/main/versions-manifest.json)
for the existing Python 3.9/3.11 matrix. Project environments are unchanged.

### Archive and publication

CI exercises Python 3.9 and 3.11, candidate privacy checks, clean committed-tree
packaging and archive-only project/AST creation. Tag publication depends on these
checks and never replaces an existing release. The source archive is browsable
and includes the one visible template, tools, docs and tests. It contains no
runtime ZIP, legacy snapshot, private context or research project records.

## Practical limits

Automated checks cannot prove methodological adequacy, statistical correctness,
translation semantics, researcher approval or figure/vector fidelity. Scientific,
bilingual and visual review remain explicit. Math is the MathText subset rather
than full TeX. A variable-font deprecation warning from the installed PDF/font
libraries was informational; no glyph loss was observed.

Supported administration is ordinary Linux/WSL, trusted project metadata and
cooperating single-user writers. There is no hostile-process race protection,
network-filesystem/power-loss certification, full ACL/xattr backup, automatic
rollback or previous-installation conversion. Retained snapshots/backups support
inspected retry/manual restoration; report archives remain complete if publishing
latest copies is interrupted. Remote HPC, regulated records and real experiments
were not executed or certified by these local tests.
