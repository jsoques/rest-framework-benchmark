## Why

The project now has a Robyn test app under `robyn/app.py`, and the team needs an offline, searchable copy of the official Robyn documentation. A generated `robyn_documentation/ROBYN_DOCUMENTATION.md` keeps the reference close to the code and avoids context-switching to the live site.

## What Changes

- Add a reusable Python scraper under `robyn_documentation/scrape.py`.
- Crawl every page under `https://robyn.tech/documentation/en`, skipping external links.
- Collapse in-page anchors into their parent page.
- Strip navigation, headers, and footers while preserving code blocks.
- Flatten the content to Markdown and concatenate it into one file.
- Write the final output to `robyn_documentation/ROBYN_DOCUMENTATION.md`.

## Capabilities

### New Capabilities

- `robyn-documentation/scraper`: Crawls the Robyn documentation site and produces a single, stripped Markdown file for offline use.

### Modified Capabilities

- None.

## Impact

- New `robyn_documentation/` directory with `scrape.py` and `ROBYN_DOCUMENTATION.md`.
- No changes to existing benchmark code, APIs, or dependencies.
