#!/usr/bin/env python3
"""Collect sold Reverb listing links while excluding Brand New products."""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from html import unescape
from typing import Iterable, List, Optional, Set, Tuple
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

BASE_MARKETPLACE_URL = "https://reverb.com/marketplace"
ITEM_LINK_RE = re.compile(r'href=["\'](/item/[^"\'#?]+(?:\?[^"\'#]*)?)["\']', re.IGNORECASE)
CARD_RE = re.compile(
    r'<li[^>]*data-test=["\']listing-grid-card["\'][^>]*>(.*?)</li>',
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class FetchConfig:
    count: int
    min_price: Optional[int]
    max_price: Optional[int]
    query: str
    start_page: int
    delay: float


def build_marketplace_url(page: int, min_price: Optional[int], max_price: Optional[int], query: str) -> str:
    params = {
        "skip_autodirects": "true",
        "show_only_sold": "true",
        "query": query,
        "page": page,
    }
    if min_price is not None:
        params["price_min"] = min_price
    if max_price is not None:
        params["price_max"] = max_price
    return f"{BASE_MARKETPLACE_URL}?{urlencode(params)}"


def normalize_item_url(href: str) -> str:
    clean_href = unescape(href)
    if "show_sold=true" not in clean_href:
        separator = "&" if "?" in clean_href else "?"
        clean_href = f"{clean_href}{separator}show_sold=true"
    return urljoin("https://reverb.com", clean_href)


def is_brand_new_fragment(fragment: str, href: str) -> bool:
    lowered = fragment.lower()
    if "brand new" in lowered:
        return True

    href_lower = href.lower()
    # URL slugs for Brand New listings often include this marker.
    if "-brand-new" in href_lower or "-new-" in href_lower:
        return True
    return False


def parse_listings_from_html(html: str) -> List[str]:
    links: List[str] = []
    seen: Set[str] = set()

    cards = CARD_RE.findall(html)
    if cards:
        for card in cards:
            match = ITEM_LINK_RE.search(card)
            if not match:
                continue
            href = match.group(1)
            if is_brand_new_fragment(card, href):
                continue
            normalized = normalize_item_url(href)
            if normalized not in seen:
                seen.add(normalized)
                links.append(normalized)
        return links

    for href in ITEM_LINK_RE.findall(html):
        if is_brand_new_fragment("", href):
            continue
        normalized = normalize_item_url(href)
        if normalized not in seen:
            seen.add(normalized)
            links.append(normalized)
    return links


def fetch_marketplace_page(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def collect_links(config: FetchConfig) -> List[str]:
    results: List[str] = []
    seen: Set[str] = set()
    page = config.start_page

    while len(results) < config.count:
        url = build_marketplace_url(page, config.min_price, config.max_price, config.query)
        try:
            html = fetch_marketplace_page(url)
        except Exception as exc:  # pragma: no cover - network/environment dependent
            print(f"[warn] Failed to fetch page {page}: {exc}", file=sys.stderr)
            break

        page_links = parse_listings_from_html(html)
        if not page_links:
            break

        for link in page_links:
            if link in seen:
                continue
            seen.add(link)
            results.append(link)
            if len(results) >= config.count:
                break

        page += 1
        if config.delay > 0:
            time.sleep(config.delay)

    return results


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Retrieve sold Reverb item links while excluding Brand New products."
    )
    parser.add_argument("--count", type=int, choices=[100, 500, 1000], required=True)
    parser.add_argument("--min-price", type=int, default=None, help="Minimum price (USD).")
    parser.add_argument("--max-price", type=int, default=None, help="Maximum price (USD).")
    parser.add_argument("--query", default="", help="Optional Reverb search query.")
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--delay", type=float, default=0.25, help="Delay between page requests (seconds).")
    parser.add_argument("--output", default="", help="Optional output file for links (one per line).")
    args = parser.parse_args(argv)

    if args.min_price is not None and args.max_price is not None and args.min_price > args.max_price:
        parser.error("--min-price cannot be greater than --max-price")
    if args.start_page < 1:
        parser.error("--start-page must be at least 1")
    if args.delay < 0:
        parser.error("--delay cannot be negative")

    return args


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    config = FetchConfig(
        count=args.count,
        min_price=args.min_price,
        max_price=args.max_price,
        query=args.query,
        start_page=args.start_page,
        delay=args.delay,
    )
    links = collect_links(config)

    out = "\n".join(links)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            if out:
                f.write(out + "\n")
        print(f"Saved {len(links)} links to {args.output}", file=sys.stderr)
    else:
        if out:
            print(out)

    if len(links) < args.count:
        print(
            f"[warn] Collected {len(links)} links, fewer than requested ({args.count}).",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
