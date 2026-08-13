#!/usr/bin/env python3
"""Crawl the Robyn docs and flatten them into a single Markdown file."""

import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

BASE_URL = "https://robyn.tech/documentation/en"
ROOT_PATH = "/documentation/en"
OUTPUT = Path(__file__).resolve().parent / "ROBYN_DOCUMENTATION.md"


def canonical(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return None
    if not parsed.netloc:
        return None
    if parsed.netloc != "robyn.tech":
        return None
    path = parsed.path
    if path in ("", "/"):
        path = ROOT_PATH
    if not path.startswith(ROOT_PATH):
        return None
    if path.endswith("/") and path != "/":
        path = path.rstrip("/")
    return urlunparse(("https", "robyn.tech", path, "", "", ""))


def extract_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        absolute = urljoin(base_url, href)
        c = canonical(absolute)
        if c is not None:
            links.append(c)
    return links


def to_markdown(html: str) -> str:
    text = md(html, heading_style="atx")
    # Remove the "Copy/Copied" button text that gets concatenated by markdownify.
    text = re.sub(r"\s*CopyCopied!\s*", "", text)
    # Collapse duplicated nested heading links like [[text](...)](...) to [text](...).
    text = re.sub(
        r"\[\[([^\]]+)\]\(([^)]+)\)\]\(([^)]+)\)",
        r"[\1](\2)",
        text,
    )
    return text


def fetch_page(session: requests.Session, url: str) -> tuple[str, str, BeautifulSoup]:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.title
    title = title_tag.string.strip() if title_tag and title_tag.string else url

    main = soup.find("main")
    if main:
        article = main.find("article") or main
    else:
        article = soup.find("article") or soup.body

    return title, to_markdown(str(article)), soup


def crawl(session: requests.Session, start: str) -> list[tuple[str, str, str]]:
    seen = set()
    queue = [start]
    pages = []

    while queue:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)

        try:
            title, markdown, soup = fetch_page(session, url)
        except Exception as exc:  # noqa: BLE001
            print(f"warning: failed to fetch {url}: {exc}", file=sys.stderr)
            continue

        pages.append((url, title, markdown))
        print(f"fetched {url} ({len(pages)} pages)", file=sys.stderr)

        for link in extract_links(soup, url):
            if link not in seen:
                queue.append(link)

        time.sleep(0.2)

    return pages


def main() -> int:
    session = requests.Session()
    session.headers.update({"User-Agent": "robyn-docs-scraper/1.0"})

    pages = crawl(session, BASE_URL)
    pages.sort(key=lambda item: item[0])

    OUTPUT.write_text(
        "# Robyn Documentation\n\n"
        "> Generated from https://robyn.tech/documentation/en\n>\n"
        "> Do not edit manually; run `python robyn_documentation/scrape.py` to regenerate.\n\n",
        encoding="utf-8",
    )

    with OUTPUT.open("a", encoding="utf-8") as f:
        for url, _title, markdown in pages:
            f.write("---\n\n")
            f.write(f"<!-- robyn-documentation source: {url} -->\n\n")
            f.write(markdown)
            f.write("\n\n")

    print(f"wrote {len(pages)} pages to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
