# Complete project source audit

The previous implementation introduced all three projects but did not contain their complete work. Its 29-entry asset manifest was a partial extraction, not a complete source inventory. Files present in `media/` were not treated as proof that a page actually displayed them.

The new audit inspects all physical PDF pages 3–47, including image placements and the complete text of each page:

| Project | Physical PDF pages | Embedded image placements |
| --- | --- | ---: |
| Salupod | 3–17 | 32 |
| Lakbay | 18–34 | 34 |
| Dalawit | 35–47 | 32 |
| Total | 45 project pages | 98 |

Placements include repeated artwork and technical-sheet underlays/overlays. They are not described as 98 independent projects or photographs. Completed technical sheets must be rendered as compositions so vector dimensions and raster elevation overlays remain together. The client’s individual sketches, material swatches, features, perspectives, elevations, and sections also receive their own presentations.

## Missing or incomplete material in the earlier website

- Full concept narratives, project metadata, complete keyword lists, concept sketches, and the original vector-arrow sequences.
- Design-feature images and all five individually named material references per project.
- General development-control data, all ten required/actual comparison rows, parking/duplex-unit figures, and setbacks.
- Salupod’s plan on site and the remaining second/third-floor areas.
- Lakbay’s plan on site and all remaining floor-plan areas, including the covered basketball court and library areas.
- Dalawit’s second-floor plan.
- Individual views from five-image perspective sheets, Dalawit’s additional shared-space sheet, and the full explanatory narratives.
- Independently inspectable front/rear/side elevations and individual building sections, while retaining their completed sheets.
- The homepage’s second Dalawit image was hidden by a phone media query. That rule is removed.

## Implementation decisions

The client’s explicit completeness requirement takes precedence over the design skill’s short-copy and page-length preferences. The existing light palette, Red Hat pairing, hero compositions, equal edges, controls, and motion kit remain. Full source paragraphs are retained rather than replaced with marketing summaries. Mobile content stacks and grows; images are not removed to force a short page.

Full-resolution original sheets supplement the individual work and preserve all source annotations. They do not substitute for separately showcasing individual perspectives or material images. The coverage matrix distinguishes a complete sheet, an image placement, a narrative, a metadata block, a keyword list, a control row, and an individually enlarged drawing.

The PDF’s apparent numerical inconsistencies and terminology remain unchanged. The extraction-specific punctuation repairs and source ambiguities are listed in `CONTENT_COVERAGE.md`.
