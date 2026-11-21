# Ryan Ladesma — Architecture portfolio

A static portfolio built from the supplied **LADESMA - PORTFOLIO.pdf**, using the local design-taste-frontend 2.5.1 kit. No package installation or build step is required.

## Run locally

In PowerShell, from this folder:

```powershell
node serve.mjs
```

Open http://127.0.0.1:5173/. The dependency-free Node server includes byte-range support for opening the large PDF. Stop it with Ctrl+C. Any standard static-file host can also serve the website.

## Files

- `index.html`: homepage, all three projects, about and tools.
- `salupod.html`, `lakbay.html`, `dalawit.html`: complete project showcases, with contents navigation.
- `site.css`: portfolio-specific artwork compositions and brand tokens.
- `complete-portfolio.css`: full-content project layouts on desktop and mobile.
- `assets/`: unmodified design skill kit, including its navigation and motion modules.
- `media/`: local optimized project images, drawings, portrait, and tool logos.
- `asset-manifest.json`: physical PDF page and extraction method for every source asset.
- `CONTENT_COVERAGE.md` and `content-coverage.json`: 212 item-by-item source coverage records.
- `portfolio-content.json`: extracted project narratives, values, and source-asset metadata.
- `PROJECT_CONTENT_AUDIT.md`: source inventory and completeness requirements.
- `SOURCE_COPY_WAIVERS.json`: three original-source wording exceptions to the design copy checker.
- `SOURCE_LAYOUT_WAIVERS.json`: original numbered-list indentation and the technical table's content-type exceptions.
- `DESIGN_PLAN.md`: factual content and recorded design decisions.
- `.taste-skill/`: design history and validation output.
- `VERIFICATION.md`: final results, retained warnings, and publishing setup still to supply.

All 45 project pages in the PDF are represented: Salupod (pages 3–17), Lakbay (18–34), and Dalawit (35–47). The showcases include the complete narratives, keywords, concept stages, features, all five materials per project, development controls, site and floor plans, perspectives, elevations, and sections. All 98 embedded image placements are accounted for, including repeated images and technical-sheet layers; that count is not a claim of 98 independent photographs.

Every independent work is shown inline on desktop and mobile. Complete composited technical sheets retain vector annotations alongside individual drawing views. Every artwork also opens at full resolution. The original-sheet archive and PDF links supplement the showcase. All displayed projects are academic proposals; source control values are transcribed without claiming regulatory compliance.

## Rebuild and audit source coverage

The website itself needs only a static server. Regenerating its source-derived pages requires Python with `pypdf`, `pdfplumber`, `pypdfium2`, and `Pillow`, plus the actual original PDF (retrieve Git LFS content first).

```powershell
python tools/compile_portfolio.py
python tools/check_portfolio_coverage.py
```

The generator exports responsive 640px/1280px previews and full-resolution WebP files into `media/complete/`, then rebuilds the project HTML and coverage ledgers. `--reuse-extraction` reuses a local extraction cache when available. The independent audit rereads the PDF, compares complete narrative text, ordered keywords and all 30 development-control rows, checks all source placements and coverage destinations, and validates local image files and links. Its result is saved under `.taste-skill/complete-audit/`.

## Before publishing

Confirm Ryan's current study level and approved public contact destinations. No contact form, invented social links, analytics, or external submission service is installed. Add the production domain to canonical URLs and make Open Graph image URLs absolute once hosting is known.

The original PDF is approximately 198 MB. It is linked explicitly and never preloaded. Keep it alongside the pages when serving locally. A future public deployment can point the PDF links to suitable file hosting, or use an owner-approved compressed copy.

The source PDF is unchanged and is tracked with Git LFS. After cloning, install Git LFS and run `git lfs pull` to retrieve it. Hosts that do not fetch LFS files need the actual PDF uploaded separately so the portfolio link serves the document.

Local browser profiles, test output, and screenshots are excluded from Git. Source coverage and current browser checks are documented in `VERIFICATION.md`; pushing this repository does not deploy the site.
