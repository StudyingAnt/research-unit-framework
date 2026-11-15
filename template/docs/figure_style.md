# Publication Figure Defaults

- PNG: 600 dpi at intended physical display size.
- PDF: vector where feasible; SVG: vector/editable where feasible.
- Figure lettering: Arial, 5–7 pt at final size; non-data-encoded text black
  (#000000). Colors can encode data categories.
- Report fonts: Noto Serif (EN), Noto Serif KR/CJK KR (KO), with readable layout.

These are defaults, not universal journal or accessibility rules. Record justified
exceptions for actual journal needs, legibility or measurement-image integrity.
Do not claim raster acquisition becomes vector evidence by wrapping it in SVG.

Describe the measurements/calculations behind panels, axes, units, scales,
normalization, colors, markers, lines, thresholds, exclusions and uncertainty.
Keep legends scientifically complete. Appropriate primary evidence tables are
valid, and table-only reports need no fabricated figure.

In report.json, declare every displayed figure with path relative to the project,
width_mm, kind (plot/measurement), font_family, text_size_pt, exception (null or
reason), and raster_embedded (boolean). The renderer embeds local PNG/SVG display
exports without fetching external resources. Link other exports in provenance.
Font/content declarations supplement actual visual review; metadata is not proof
that every glyph or vector element has the claimed properties.
