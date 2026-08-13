## 1. Scraper setup

- [x] 1.1 Create `robyn_documentation/` directory and add a `requirements-scraper.txt` with `requests` and `markdownify`.
- [x] 1.2 Create `robyn_documentation/scrape.py` with the crawler, HTML-to-Markdown converter, and writer.

## 2. Crawl and generate

- [x] 2.1 Run `scrape.py` to fetch all `/documentation/en` pages, strip navigation, flatten to Markdown, and concatenate into `robyn_documentation/ROBYN_DOCUMENTATION.md`.
- [x] 2.2 Verify the output file exists and contains the expected sections (Example Application, API Reference, etc.).
