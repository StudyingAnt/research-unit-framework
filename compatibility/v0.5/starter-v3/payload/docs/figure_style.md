# Figure Style and Export Rules

This document governs **manuscript figures**, not the body text of Markdown/HTML/PDF reports.

## Required deliverables

For each final manuscript-quality figure, generate from the same source code and dataset:

- `figure_01.png`: raster, **600 dpi** at the intended final physical dimensions.
- `figure_01.pdf`: vector graphics where possible, retaining text and lines as vector objects.
- `figure_01.svg`: editable vector graphics where possible, with correct fonts/text.

If the figure includes microscopy or other bitmap imagery, preserve its native information and embed at appropriate effective resolution. Exporting a low-resolution raster as 600 dpi does **not** restore detail.

## Typography

- Figure typography: **Arial**, 5-7 pt inclusive at **final displayed size**, including axis labels, tick labels, legends, panel letters, titles, and annotations.
- Default typography color: exact solid black `#000000`, no low-opacity gray text.
- Color in data points, lines, bars, fills, and legends is allowed when it encodes a category or quantity. Colored text is permitted **only** when its color itself communicates data grouping.
- Do not substitute Arial silently with a visually similar font. On WSL, verify that a genuine Arial family is installed. Run `fc-match Arial` and inspect the returned family; Fontconfig may otherwise select a fallback.
- Check all text again after placing the figure at manuscript column width; resizing later changes effective point size.

## Visual integrity

- Use explicit final width and height. Prefer reproducible dimensions appropriate for a journal column or multi-panel spread.
- Preserve axis scales, units, uncertainty definitions, sample sizes, and labels. Do not remove uncertainty displays for visual simplicity.
- Ensure plots and legends are not clipped. Do not crop away data points.
- Choose colors distinguishable in print where possible; do not rely on color alone for crucial categories.
- Export with stable input data, documented seeds/parameters, and predictable filenames.
- Store the figure-generating code under the appropriate publication repository task, not as an untracked copy in `analyses/`.

## Validation checklist

1. PNG metadata reports the intended pixel dimensions and 600 dpi.
2. PDF and SVG are vector outputs where possible; all text remains legible.
3. Figure text is Arial and 5-7 pt at final manuscript size.
4. Ordinary text is solid black, and color choices encode data rather than decoration.
5. No missing glyphs, clipped marks, missing legend entries, or incorrect scale/units.
6. `figure_01.png`, `figure_01.pdf`, and `figure_01.svg` match scientifically and visually.
7. The report links the figure and identifies the source script, input data, configuration, and output path.

## Report typography

For HTML/PDF *report body text*, use Noto Serif for English and Noto Serif KR / Noto Serif CJK KR for Korean. These are **not** the manuscript figure fonts. The CSS under `tools/report.css` controls report output.
