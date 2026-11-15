# Scientific Reporting Contract

Use `templates/report.en.md` and `templates/report.ko.md` for corresponding
scientific sources. Keep their eleven section markers; fill the applicable
scientific detail, rather than repeating execution logistics or linking code in
place of Methods. A scientifically trained collaborator should understand what
was done, why, how quantities/figures were derived and what they support without
opening source code. This depth must support manuscript preparation.

The sections are Motivation; Aim and Tactic Question; Strategy; Tactic and
Methods; Specifications; Execution and Validation; Figures or Primary Evidence;
Results; Analysis and Interpretation; Limitations and Next Questions;
Reproducibility and Artifact References. Their detailed prompts are in the paired
templates. Preserve the same definitions, procedures, parameters, units,
replication, equations, findings, uncertainty, claims and attribution in EN/KO.

There is **no page-count target, minimum or maximum**. Do not compress Methods,
shrink figures/typography, or force equal language page counts. Figures or primary
tables must faithfully represent evidence. Follow `docs/figure_style.md`.

Define samples, observational and independent units, measurements, denominators,
controls/comparisons, selection, missingness, filters/preprocessing and order,
calculations/statistics, uncertainty, exact settings and figure construction.
Explain actual procedures for the relevant experimental, computational,
observational, theoretical or hybrid methods. State when no control, test or
uncertainty estimate was used and its implications. Separate Results from
Interpretation, and operational status from scientific outcome.

Separate planned, default, reconstructed, verified effective and unknown
procedures/settings. An available HEAD is not the producing revision. Record
relevant dirty-source hashes, actual primary references and precise provenance
gaps. Do not turn a consistency check into a claim of historical reproduction.
Reporting does not authorize new analyses, changed statistics or provenance
investigations. Keep approved plans and previous report revisions intact.

## Producing a report

After authorized work, edit `reports/AST_ID/en/report.md`, `ko/report.md` and the
small `report.json` alongside them. The agent runs:

```bash
python tools/build_reports.py A001-S01-T01 --check
python tools/build_reports.py A001-S01-T01 --revision REV001
```

These IDs are examples, not existing approved work. Reuse a verified reporting
environment with Pandoc, WeasyPrint, Matplotlib, Pillow and FontTools. Configure
actual font files/Pandoc in `framework-project.json` when auto-discovery is not
enough. Do not provision environments inside routine reporting or science jobs.

Final rendering requires `COMPLETED`; the scientific outcome can be
`NOT_EVALUATED` with an explanation when no hypothesis was evaluated. PLANNING,
APPROVED, EXECUTING, WAITING, BLOCKED and FAILED retain their actual meanings.
Other outcomes are SUPPORTED, NOT_SUPPORTED and INCONCLUSIVE. Do not invent a
verdict or mark unperformed required work complete to satisfy a validator.

The builder checks structure, placeholders, metadata, scalar/math correspondence,
local artifacts, fonts/glyphs and declared figure settings. It cannot establish
methodological adequacy, statistical correctness, semantic equivalence or adopted
scientific claims. Review these explicitly and visually inspect HTML/PDF fonts,
glyphs, equations, figures, axes/units, captions, tables and pagination. Record
actual review references in `report.json`; rendering never sets approval.

Each final build creates a complete immutable `revisions/REV###/` containing the
six outputs, metadata and render provenance. Reusing a revision is refused. Edit
the current Markdown and metadata, increment REV and retain the same AST for a
reporting revision. `current.json` identifies the last fully published revision;
top-level HTML/PDF are convenient copies. Unarchived local output edits block
a final rebuild until they are preserved and reviewed. A failure while publishing those copies
does not damage the complete revision; restore copies from that revision after
inspection. There is no journal/recovery service or bulk historical rebuild.

`--preview` creates disclosed separate preview outputs and never replaces final
reports. Unsupported mathematics (MathText subset), missing assets or unavailable
final fonts are explicit failures. Do not claim an unchecked preview as final.
