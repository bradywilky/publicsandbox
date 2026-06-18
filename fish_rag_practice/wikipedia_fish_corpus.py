#!/usr/bin/env python3
"""Download a fish-focused Wikipedia corpus via category traversal."""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


API_URL = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "fish-rag-practice/1.0 (local corpus builder)"

SKIP_TITLE_PREFIXES = (
    "List of",
    "Outline of",
    "Index of",
    "Template:",
    "Wikipedia:",
    "Help:",
    "Portal:",
    "Draft:",
)

SKIP_TITLE_KEYWORDS = (
    "disambiguation",
    "stub",
)

SKIP_CATEGORY_KEYWORDS = (
    "stubs",
    "redirects",
    "disambiguation",
    "lists",
    "wikipedia",
    "templates",
    "navigational boxes",
    "articles",
)


@dataclass(frozen=True)
class ArticleRecord:
    title: str
    pageid: int
    source_category: str
    text: str
    url: str


def make_request(params: dict[str, object], pause_seconds: float) -> dict:
    query = urlencode(params)
    request = Request(
        f"{API_URL}?{query}",
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urlopen(request) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Wikipedia API returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach Wikipedia API: {exc.reason}") from exc

    if pause_seconds > 0:
        time.sleep(pause_seconds)
    return payload


def should_skip_title(title: str) -> bool:
    lowered = title.lower()
    if title.startswith(SKIP_TITLE_PREFIXES):
        return True
    return any(keyword in lowered for keyword in SKIP_TITLE_KEYWORDS)


def should_skip_category(category_title: str) -> bool:
    lowered = category_title.lower()
    return any(keyword in lowered for keyword in SKIP_CATEGORY_KEYWORDS)


def slugify(title: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", title.strip())
    return slug.strip("._") or "article"


def iter_category_members(
    category_title: str,
    pause_seconds: float,
) -> Iterable[dict]:
    cmcontinue: str | None = None
    while True:
        params: dict[str, object] = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtitle": category_title,
            "cmlimit": "max",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        payload = make_request(params, pause_seconds)
        members = payload.get("query", {}).get("categorymembers", [])
        for member in members:
            yield member

        cmcontinue = payload.get("continue", {}).get("cmcontinue")
        if not cmcontinue:
            return


def collect_titles(
    root_categories: list[str],
    max_depth: int,
    pause_seconds: float,
) -> tuple[dict[str, str], set[str]]:
    article_sources: dict[str, str] = {}
    visited_categories: set[str] = set()
    pending: list[tuple[str, int]] = []

    for category in root_categories:
        normalized = category if category.startswith("Category:") else f"Category:{category}"
        pending.append((normalized, 0))

    while pending:
        category_title, depth = pending.pop()
        if category_title in visited_categories:
            continue

        visited_categories.add(category_title)
        for member in iter_category_members(category_title, pause_seconds):
            namespace = member.get("ns")
            title = member.get("title", "")

            if namespace == 14:
                if depth < max_depth and not should_skip_category(title):
                    pending.append((title, depth + 1))
                continue

            if namespace != 0 or should_skip_title(title):
                continue

            article_sources.setdefault(title, category_title)

    return article_sources, visited_categories


def fetch_extract(title: str, pause_seconds: float) -> tuple[int, str]:
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts|info",
        "inprop": "url",
        "explaintext": 1,
        "redirects": 1,
        "titles": title,
    }
    payload = make_request(params, pause_seconds)
    pages = payload.get("query", {}).get("pages", {})
    page = next(iter(pages.values()))

    pageid = page.get("pageid", -1)
    extract = (page.get("extract") or "").strip()
    fullurl = page.get("fullurl") or f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
    return pageid, json.dumps({"extract": extract, "fullurl": fullurl})


def download_articles(
    article_sources: dict[str, str],
    pause_seconds: float,
) -> list[ArticleRecord]:
    records: list[ArticleRecord] = []
    total = len(article_sources)

    for index, (title, source_category) in enumerate(sorted(article_sources.items()), start=1):
        pageid, payload = fetch_extract(title, pause_seconds)
        decoded = json.loads(payload)
        text = decoded["extract"]
        if not text:
            continue

        records.append(
            ArticleRecord(
                title=title,
                pageid=pageid,
                source_category=source_category,
                text=text,
                url=decoded["fullurl"],
            )
        )

        if index % 25 == 0 or index == total:
            print(f"Downloaded {index}/{total} article extracts...", flush=True)

    return records


def write_outputs(records: list[ArticleRecord], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    article_dir = output_dir / "articles"
    article_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = output_dir / "corpus.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as jsonl_file:
        for record in records:
            json.dump(
                {
                    "title": record.title,
                    "pageid": record.pageid,
                    "source_category": record.source_category,
                    "url": record.url,
                    "text": record.text,
                },
                jsonl_file,
                ensure_ascii=False,
            )
            jsonl_file.write("\n")

            article_path = article_dir / f"{slugify(record.title)}.txt"
            article_path.write_text(record.text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download a Wikipedia fish corpus by traversing categories."
    )
    parser.add_argument(
        "--category",
        action="append",
        dest="categories",
        default=[],
        help="Root category to crawl. Can be passed multiple times.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=2,
        help="How many category levels to recurse into. Default: 2",
    )
    parser.add_argument(
        "--pause-seconds",
        type=float,
        default=0.1,
        help="Pause between API requests. Default: 0.1",
    )
    parser.add_argument(
        "--output-dir",
        default="data/wikipedia_fish_corpus",
        help="Directory where corpus files are written.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    categories = args.categories or [
        "Category:Fish",
        "Category:Freshwater fish",
        "Category:Marine fish",
        "Category:Game fish",
        "Category:Sharks",
        "Category:Rays (fish)",
    ]

    print("Collecting candidate article titles from categories...", flush=True)
    article_sources, visited_categories = collect_titles(
        root_categories=categories,
        max_depth=args.max_depth,
        pause_seconds=args.pause_seconds,
    )
    print(
        f"Found {len(article_sources)} candidate articles across "
        f"{len(visited_categories)} categories.",
        flush=True,
    )

    print("Downloading article extracts...", flush=True)
    records = download_articles(article_sources, args.pause_seconds)
    print(f"Kept {len(records)} articles with non-empty plaintext.", flush=True)

    output_dir = Path(args.output_dir)
    write_outputs(records, output_dir)
    print(f"Wrote corpus to {output_dir.resolve()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
