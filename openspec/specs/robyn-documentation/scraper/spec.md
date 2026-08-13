# robyn-documentation/scraper Specification

## Purpose
The scraper produces an offline, single-file Markdown copy of the English Robyn documentation for quick reference while working on the `robyn` benchmark app.
## Requirements
### Requirement: Crawl documentation pages
The scraper SHALL start from `https://robyn.tech/documentation/en` and follow every internal link whose path begins with `/documentation/en`, ignoring in-page anchors and external sites.

#### Scenario: Discover linked pages
- **WHEN** the scraper is run
- **THEN** it collects the set of unique `/documentation/en` pages reachable from the start URL

### Requirement: Strip navigation and flatten content
The scraper SHALL remove site navigation, headers, and footers from each fetched page and convert the remaining content to Markdown while preserving code blocks and inline formatting.

#### Scenario: Clean output
- **WHEN** the scraper processes a documentation page
- **THEN** the resulting Markdown contains only the page's main content with code blocks intact

### Requirement: Produce a single concatenated file
The scraper SHALL merge all page Markdown into one file written to `robyn_documentation/ROBYN_DOCUMENTATION.md`.

#### Scenario: Generate offline docs
- **WHEN** the scraper has finished crawling
- **THEN** `robyn_documentation/ROBYN_DOCUMENTATION.md` exists and contains the flattened content of every discovered page

