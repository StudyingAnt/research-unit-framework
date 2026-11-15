# Reporting Setup and Validation

Project tools are readable source in template/tools and work after copying,
without a checkout, Python package or runtime archive. Core creation/update/ID
administration uses only Python 3.9+. Reporting is optional, separately configured.

Reuse an existing reporting environment when possible. For a new environment,
install Pandoc as appropriate for the system and the packages listed in
requirements/reporting.txt. This is an explicit setup step, not part of project
creation, update or ordinary science jobs. Provide licensed local font files;
the framework redistributes none.

Set reporting.pandoc, font_en, font_ko and font_family_en/font_family_ko in the
project-owned framework-project.json when needed. Defaults try Pandoc on PATH and
actual installed Noto Serif / Noto Serif KR. Font paths may be absolute or relative
to the project. Family and source glyph coverage are checked; unsupported math
fails explicitly. The math backend supports Matplotlib MathText rather than full
TeX; do not silently drop unsupported notation. Preview is always disclosed.

After filling paired Markdown/report.json for the selected approved AST:

```bash
python tools/build_reports.py A001-S01-T01 --check
python tools/build_reports.py A001-S01-T01 --revision REV001
```

These are illustrative IDs. --check reads structure, placeholders, metadata,
scalar correspondence and figures without rendering or creating project files.
Rendering also verifies bilingual equations, references, fonts and assets. Supply
complete figure metadata as described in the project's docs/figure_style.md;
600 dpi alone does not set physical display width. PNG/SVG display assets are
embedded, and external resource fetching is disabled. Source defaults or supplied
metadata are not proof of actual historical procedures or vector fidelity.

Each successful final revision contains corresponding EN/KO MD, HTML, PDF,
report.json and render.json with source/output/font hashes and informational page
counts. All eleven detailed scientific sections remain required. A table-only,
COMPLETED/NOT_EVALUATED unit with an actual reason is valid. There is no report
page-count gate. Review scientific adequacy, translation meaning and final
HTML/PDF visually; software checks do not set those review flags for you.

Edit current Markdown and increment report.json plus both source REV fields for
a reporting revision. Earlier immutable revisions remain intact; a new AST is
needed only for a substantively different evidence-producing task. A Run is an
optional execution instance, not a rendering revision. Historical work need not
be converted or bulk rebuilt. See [the project reporting contract](../template/REPORT_TEMPLATE.md) for the full
project reporting contract and [architecture](ARCHITECTURE.md) for interrupted-copy limits.
