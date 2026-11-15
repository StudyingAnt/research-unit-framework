# Detailed Bilingual Scientific Reporting

The managed reporting contract and paired templates implement specification
section 10. They retain eleven corresponding sections and manuscript-level
Methods guidance. No page/word count target, limit or warning exists. Page counts
are informational. Results, Interpretation, operational status and scientific
outcome remain distinct. A table-only completed descriptive Tactic may remain
NOT_EVALUATED with a reason; never fabricate a verdict or an unperformed method.

After approved Tactic registration, `draft-reports PROJECT TACTIC_ID` creates
paired editable Markdown and `report.json` without replacing existing work.
`new-unit` performs these two administrative steps together. Complete each
section and the metadata explicitly; unknown provenance remains unknown.

Configure an existing reporting environment in project-owned
`framework-project.json`: Pandoc executable, EN/KO font files and their actual
families. Defaults are Noto Serif and Noto Serif KR; Noto Serif CJK KR can be
selected explicitly when installed. Optional dependencies are listed separately
in `requirements/reporting.txt`; Python 3.11, Pandoc 2.12, WeasyPrint 66 and
Matplotlib 3.11 are the observed acceptance environment, not an automatically
provisioned environment or a claim of all-version compatibility.

```bash
python3 .research-framework/runtime.pyz report-check /absolute/project A001-S01-T01
python3 .research-framework/runtime.pyz report /absolute/project A001-S01-T01 --revision REV001
```

Use the Python interpreter with the reporting dependencies for the render command.
No installation, environment activation or data analysis is performed by rendering.
The renderer reads both sources, checks metadata, sections, placeholders and
numeric-token correspondence, and compares mathematical expressions through the
Pandoc AST. Scalar checks cannot prove translation or statistical correctness.
Methods, bilingual scientific meaning and visual review are explicit metadata
decisions; successful rendering never sets them to true. Review references must
identify the actual review, rather than inventing a human sign-off.

Common TeX math is rendered as static SVG using Matplotlib MathText. Unsupported
commands/environments fail explicitly; this is not a complete TeX engine. Local
image assets are embedded, and local linked artifacts must exist inside the
project. Remote links may remain references, but remote images/resources and
active SVG/HTML are not fetched or executed. Required fonts and glyphs fail
explicitly. Font-family changes must be configured honestly. `preview: true`
discloses substitutions and writes `report.preview.html/pdf`, separately from
final outputs. Fonts remain external assets and are not included in framework
releases. Embedded report fonts may have their own distribution conditions.

Every displayed scientific image requires a `figures` entry in `report.json`
with project-relative path, intended width in mm, plot/measurement kind, font
family, text size in pt, raster-embedded flag and exception reason. PNG inspection
checks actual density and pixel width against 600 dpi at intended size. Defaults
are Arial 5–7 pt black non-data text, vector PDF and editable SVG when appropriate.
Scientific captions must explain construction, axes, units, scales, normalization,
symbols, lines, exclusions and uncertainty. Automated metadata checks cannot infer
every font/axis meaning from raster pixels or prove vector purity. Review actual
exports and preserve measurement-image integrity; exceptions need a real reason.

Both languages are staged before publication. Each unique REV### retains all six
files, metadata and checksums in a non-reused revision directory. Effective font
hashes, implementation version, previews and informational page counts are
recorded. Previously rendered source snapshots survive later manual Markdown
edits. The first render cannot reconstruct report versions that were never
retained; explicitly archive legacy outputs before an authorized report revision.
Rendering does not revise approved plans or launch a new analysis.

Output replacement uses verified backups and a durable journal. Interruptions
are inspected with `report-recover-plan PROJECT OPERATION`, then guarded undo
with `report-recover PROJECT OPERATION --plan-digest DIGEST`. The whole affected
set is checked before undo and later edits are protected. Failed revision
directories remain audit evidence; choose a new revision after resolution.
Framework installation/update/migration never calls this renderer.
