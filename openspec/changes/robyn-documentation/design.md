## Context

The project already has a small Robyn benchmark in `robyn/app.py`. The live docs at `https://robyn.tech/documentation/en` are the source of truth; we want an offline copy that can be regenerated on demand. The scraper must respect the user's scope rules: only `/documentation/en` pages, collapse anchors, strip chrome, keep code blocks, flatten to Markdown.

## Goals / Non-Goals

**Goals:**
- Reusable `robyn_documentation/scrape.py` that crawls the docs and writes `robyn_documentation/ROBYN_DOCUMENTATION.md`.
- No extra runtime dependencies for the benchmark; the scraper can use its own small set.

**Non-Goals:**
- Live sync, incremental updates, or storing old versions.
- Generalizing the scraper to arbitrary sites.

## Decisions

- **Python with minimal dependencies**: Use `requests` or `httpx` for fetching and `markdownify` for HTML-to-Markdown conversion because they are small, widely used, and preserve code blocks well.
  - *Alternative considered*: Shell `wget` mirror. Rejected because it does not strip navigation or flatten to Markdown.
  - *Alternative considered*: `html2text`. Rejected because `markdownify` produces cleaner GitHub-Flavored Markdown from the fetched HTML.
- **Directory layout**: `robyn_documentation/scrape.py` and `robyn_documentation/ROBYN_DOCUMENTATION.md` keep the docs and tool together and out of the benchmark source tree.
- **Deduplication by canonical path**: URLs with hash fragments are normalized to their base URL before fetching so anchors are collapsed.

## Risks / Trade-offs

- Site structure changes can break the scraper. → Mitigation: the scraper logs any 404 or parse errors and can be re-run after fixing the selector.
- Some code blocks may be inside JavaScript-rendered sections. → Mitigation: the docs appear to be server-rendered from the landing page fetch; if a page is empty we will fall back to preserving the raw HTML for that page.
