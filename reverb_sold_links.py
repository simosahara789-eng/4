#!/usr/bin/env python3
"""Collect sold Reverb listing links while excluding Brand New products."""

from __future__ import annotations

import argparse
<<<<<< codex/create-tool-to-retrieve-sold-reverb-products-jcu4h5
import json
=======
>>>>>> main
import re
import sys
import time
from dataclasses import dataclass
from html import unescape
<<<<<< codex/create-tool-to-retrieve-sold-reverb-products-jcu4h5
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.error import HTTPError, URLError
=======
from typing import Iterable, List, Optional, Set, Tuple
>>>>>> main
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

BASE_MARKETPLACE_URL = "https://reverb.com/marketplace"
ITEM_LINK_RE = re.compile(r'href=["\'](/item/[^"\'#?]+(?:\?[^"\'#]*)?)["\']', re.IGNORECASE)
CARD_RE = re.compile(
    r'<li[^>]*data-test=["\']listing-grid-card["\'][^>]*>(.*?)</li>',
    re.IGNORECASE | re.DOTALL,
)
<<<<<< codex/create-tool-to-retrieve-sold-reverb-products-jcu4h5
NEXT_DATA_RE = re.compile(
    r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
=======
>>>>>> main


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
<<<<<< codex/create-tool-to-retrieve-sold-reverb-products-jcu4h5
=======
    # URL slugs for Brand New listings often include this marker.
>>>>>> main
    if "-brand-new" in href_lower or "-new-" in href_lower:
        return True
    return False


<<<<<< codex/create-tool-to-retrieve-sold-reverb-products-jcu4h5
def _condition_value(listing: Dict[str, Any]) -> str:
    condition = listing.get("condition")
    if isinstance(condition, str):
        return condition.lower()
    if isinstance(condition, dict):
        for key in ("display_name", "name", "slug"):
            value = condition.get(key)
            if isinstance(value, str):
                return value.lower()
    return ""


def _extract_listing_dicts(obj: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(obj, dict):
        if any(k in obj for k in ("item_url", "url", "absolute_url", "slug")):
            yield obj
        for value in obj.values():
            yield from _extract_listing_dicts(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _extract_listing_dicts(item)


def parse_listings_from_next_data(html: str) -> List[str]:
    match = NEXT_DATA_RE.search(html)
    if not match:
        return []

    try:
        payload = json.loads(unescape(match.group(1)))
    except json.JSONDecodeError:
        return []

    links: List[str] = []
    seen: Set[str] = set()
    for listing in _extract_listing_dicts(payload):
        href = ""
        for key in ("item_url", "url", "absolute_url"):
            value = listing.get(key)
            if isinstance(value, str) and "/item/" in value:
                href = value
                break
        if not href:
            slug = listing.get("slug")
            item_id = listing.get("id")
            if isinstance(slug, str) and isinstance(item_id, (int, str)):
                href = f"/item/{item_id}-{slug}"

        if not href:
            continue
        if "brand new" in _condition_value(listing):
            continue
        if is_brand_new_fragment("", href):
            continue

        normalized = normalize_item_url(href)
        if normalized not in seen:
            seen.add(normalized)
            links.append(normalized)
    return links


=======
>>>>>> main
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
<<<<<< codex/create-tool-to-retrieve-sold-reverb-products-jcu4h5
        if links:
            return links

    next_data_links = parse_listings_from_next_data(html)
    if next_data_links:
        return next_data_links
=======
        return links
>>>>>> main

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
<<<<<< codex/create-tool-to-retrieve-sold-reverb-products-jcu4h5
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://reverb.com/",
=======
>>>>>> main
        },
    )
    with urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


<<<<<< codex/create-tool-to-retrieve-sold-reverb-products-jcu4h5
def collect_links_with_warnings(config: FetchConfig) -> Tuple[List[str], List[str]]:
    results: List[str] = []
    seen: Set[str] = set()
    warnings: List[str] = []
=======
def collect_links(config: FetchConfig) -> List[str]:
    results: List[str] = []
    seen: Set[str] = set()
>>>>>> main
    page = config.start_page

    while len(results) < config.count:
        url = build_marketplace_url(page, config.min_price, config.max_price, config.query)
        try:
            html = fetch_marketplace_page(url)
<<<<<< codex/create-tool-to-retrieve-sold-reverb-products-jcu4h5
        except HTTPError as exc:  # pragma: no cover
            warnings.append(f"Failed page {page}: HTTP {exc.code}.")
            break
        except URLError as exc:  # pragma: no cover
            warnings.append(f"Failed page {page}: network error ({exc.reason}).")
            break
        except Exception as exc:  # pragma: no cover
            warnings.append(f"Failed page {page}: {exc}")
=======
        except Exception as exc:  # pragma: no cover - network/environment dependent
            print(f"[warn] Failed to fetch page {page}: {exc}", file=sys.stderr)
>>>>>> main
            break

        page_links = parse_listings_from_html(html)
        if not page_links:
<<<<<< codex/create-tool-to-retrieve-sold-reverb-products-jcu4h5
            warnings.append(
                f"Page {page} returned no parseable listings. Reverb may be serving JS-only or blocking this host."
            )
=======
>>>>>> main
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

<<<<<< codex/create-tool-to-retrieve-sold-reverb-products-jcu4h5
    if len(results) < config.count:
        warnings.append(f"Collected {len(results)} links, fewer than requested ({config.count}).")
    return results, warnings


def collect_links(config: FetchConfig) -> List[str]:
    links, warnings = collect_links_with_warnings(config)
    for warning in warnings:
        print(f"[warn] {warning}", file=sys.stderr)
    return links
=======
    return results
>>>>>> main


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
<<<<<< codex/create-tool-to-retrieve-sold-reverb-products-jcu4h5
        with open(args.output, "w", encoding="utf-8") as file:
            if out:
                file.write(out + "\n")
        print(f"Saved {len(links)} links to {args.output}", file=sys.stderr)
    elif out:
        print(out)
=======
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
>>>>>> main

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
