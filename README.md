# Ryan Ladesma — Architecture portfolio

A static portfolio built from the supplied **LADESMA - PORTFOLIO.pdf**, using the local design-taste-frontend 2.5.1 kit. No package installation or build step is required.

## Run locally

In PowerShell, from this folder:

```powershell
node serve.mjs
```

Open http://127.0.0.1:5173/. The dependency-free Node server includes byte-range support for opening the large PDF. Stop it with Ctrl+C. Any standard static-file host can also serve the website.

## Files

- `index.html`: homepage, selected projects, about and tools.
- `salupod.html`, `lakbay.html`, `dalawit.html`: project case studies.
- `site.css`: portfolio-specific artwork compositions and brand tokens.
- `assets/`: unmodified design skill kit, including its navigation and motion modules.
- `media/`: local optimized project images, drawings, portrait, and tool logos.
- `asset-manifest.json`: physical PDF page and extraction method for every source asset.
- `DESIGN_PLAN.md`: factual content and recorded design decisions.
- `.taste-skill/`: design history and validation output.
- `VERIFICATION.md`: final results, retained warnings, and publishing setup still to supply.

Project images are extracted from the source PDF, rather than recreated or replaced with stock imagery. Large technical sheets open separately at full resolution, preserving original annotations. All displayed projects are academic proposals.

## Before publishing

Confirm Ryan's current study level and approved public contact destinations. No contact form, invented social links, analytics, or external submission service is installed. Add the production domain to canonical URLs and make Open Graph image URLs absolute once hosting is known.

The original PDF is approximately 198 MB. It is linked explicitly and never preloaded. Keep it alongside the pages when serving locally. A future public deployment can point the PDF links to suitable file hosting, or use an owner-approved compressed copy.

The source PDF is unchanged and is tracked with Git LFS. After cloning, install Git LFS and run `git lfs pull` to retrieve it. Hosts that do not fetch LFS files need the actual PDF uploaded separately so the portfolio link serves the document.

Local browser profiles, test output, and screenshots are excluded from Git. The original website validation is documented in `VERIFICATION.md`; pushing this repository does not deploy the site.
