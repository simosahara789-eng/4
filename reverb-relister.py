#!/usr/bin/env python3
"""
Reverb Auto-Relister
Polls for sold listings and automatically creates new identical listings.

Designed for "unlimited supply" storefronts (e.g., 3D-printed products)
where each sale ends the listing but stock is effectively infinite.

Setup:
  1. Get a Personal Access Token from https://reverb.com/my/api_settings
  2. Copy config.example.json to config.json and add your token
  3. Run: python3 reverb-relister.py

Can be run as a cron job, systemd timer, or manually.
No external dependencies — uses only Python stdlib.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
STATE_PATH = SCRIPT_DIR / "state.json"
LOG_PATH = SCRIPT_DIR / "relister.log"

API_BASE = "https://api.reverb.com/api"
HEADERS_BASE = {
    "Content-Type": "application/hal+json",
    "Accept": "application/hal+json",
    "Accept-Version": "3.0",
}


def log(msg: str):
    """Log to both stdout and log file."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print(f"ERROR: {CONFIG_PATH} not found.")
        print(f"Copy config.example.json to config.json and add your Reverb API token.")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_state() -> dict:
    if STATE_PATH.exists():
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"last_check": None, "relisted": {}}


def save_state(state: dict):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def api_request(method: str, path: str, token: str, data: dict = None) -> dict:
    """Make a Reverb API request. Returns parsed JSON."""
    url = f"{API_BASE}/{path.lstrip('/')}"
    headers = {**HEADERS_BASE, "Authorization": f"Bearer {token}"}

    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        log(f"API error {e.code} on {method} {url}: {error_body}")
        raise


def get_sold_orders(token: str, since: str) -> list:
    """Fetch selling orders updated since a given ISO timestamp."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    path = f"/my/orders/selling/all?updated_start_date={since}&updated_end_date={now}"

    all_orders = []
    page = 1
    while True:
        resp = api_request("GET", f"{path}&page={page}&per_page=50", token)
        orders = resp.get("orders", [])
        all_orders.extend(orders)
        if page >= resp.get("total_pages", 1):
            break
        page += 1
        time.sleep(0.5)  # Be nice to the API

    return all_orders


def get_listing(token: str, listing_id: str) -> dict:
    """Fetch full listing details by ID."""
    return api_request("GET", f"/listings/{listing_id}", token)


def get_my_listings(token: str, state: str = "sold") -> list:
    """Fetch your listings filtered by state."""
    all_listings = []
    page = 1
    while True:
        resp = api_request("GET", f"/my/listings?state={state}&per_page=50&page={page}", token)
        listings = resp.get("listings", [])
        all_listings.extend(listings)
        if page >= resp.get("total_pages", 1):
            break
        page += 1
        time.sleep(0.5)
    return all_listings


def create_listing(token: str, listing_data: dict) -> dict:
    """Create a new listing from the given data and publish it."""
    return api_request("POST", "/listings", token, listing_data)


def build_relist_payload(original: dict, config: dict) -> dict:
    """
    Build a new listing payload from an original sold listing.
    Copies all relevant fields to create an identical new listing.
    """
    payload = {
        "publish": True,  # Auto-publish immediately
    }

    # Copy standard fields if present
    field_map = {
        "make": "make",
        "model": "model",
        "finish": "finish",
        "year": "year",
        "title": "title",
        "description": "description",
        "sku": "sku",
        "upc": "upc",
        "upc_does_not_apply": "upc_does_not_apply",
        "handmade": "handmade",
        "offers_enabled": "offers_enabled",
        "shipping_profile_id": "shipping_profile_id",
    }

    for src, dst in field_map.items():
        val = original.get(src)
        if val is not None:
            payload[dst] = val

    # Price
    if "price" in original:
        price = original["price"]
        if isinstance(price, dict):
            payload["price"] = {
                "amount": price.get("amount", price.get("display", "0")),
                "currency": price.get("currency", "USD"),
            }

    # Condition
    if "condition" in original:
        cond = original["condition"]
        if isinstance(cond, dict) and "uuid" in cond:
            payload["condition"] = {"uuid": cond["uuid"]}

    # Categories
    if "categories" in original:
        cats = original["categories"]
        if isinstance(cats, list) and len(cats) > 0:
            payload["categories"] = [{"uuid": c["uuid"]} for c in cats if "uuid" in c]

    # Photos — use full-size URLs
    if "photos" in original:
        photos = original["photos"]
        photo_urls = []
        for p in photos:
            if isinstance(p, dict):
                links = p.get("_links", {})
                # Try to get the largest image
                for key in ["original", "large_crop", "full", "large", "small_crop", "thumbnail"]:
                    if key in links and "href" in links[key]:
                        photo_urls.append(links[key]["href"])
                        break
            elif isinstance(p, str):
                photo_urls.append(p)
        if photo_urls:
            payload["photos"] = photo_urls

    # Videos
    if "videos" in original:
        videos = original["videos"]
        if isinstance(videos, list) and len(videos) > 0:
            payload["videos"] = [{"link": v.get("link", v)} for v in videos if v]

    # Shipping rates (if no shipping profile)
    if "shipping_profile_id" not in payload or payload["shipping_profile_id"] is None:
        if "shipping" in original:
            ship = original["shipping"]
            if isinstance(ship, dict) and "rates" in ship:
                payload["shipping"] = ship
            payload.pop("shipping_profile_id", None)

    # has_inventory / inventory — set to 1 for unlimited supply items
    payload["has_inventory"] = True
    payload["inventory"] = config.get("default_inventory", 1)

    return payload


def run(config: dict):
    """Main run loop — check for sold listings and relist them."""
    token = config["api_token"]
    state = load_state()

    # Determine time window
    if state["last_check"]:
        since = state["last_check"]
    else:
        # First run — look back N days (configurable, default 7)
        lookback_days = config.get("initial_lookback_days", 7)
        since = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime(
            "%Y-%m-%dT%H:%M:%S+00:00"
        )
        log(f"First run — looking back {lookback_days} days")

    log(f"Checking for sold orders since {since}")

    # Get sold listings directly (more reliable than parsing orders)
    sold_listings = get_my_listings(token, state="sold")
    log(f"Found {len(sold_listings)} total sold listings")

    # Filter by SKU allowlist if configured
    sku_allowlist = config.get("sku_allowlist", None)

    relisted_count = 0
    skipped_count = 0

    for listing in sold_listings:
        listing_id = str(listing.get("id", ""))
        sku = listing.get("sku", "")
        title = listing.get("title", "Unknown")

        # Skip if already relisted
        if listing_id in state["relisted"]:
            skipped_count += 1
            continue

        # Skip if not in allowlist (when configured)
        if sku_allowlist is not None and sku not in sku_allowlist:
            log(f"Skipping '{title}' (SKU: {sku}) — not in allowlist")
            state["relisted"][listing_id] = {
                "skipped": True,
                "reason": "not_in_allowlist",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            continue

        log(f"Relisting: '{title}' (ID: {listing_id}, SKU: {sku})")

        try:
            # Fetch full listing details
            full_listing = get_listing(token, listing_id)
            time.sleep(0.5)

            # Build new listing payload
            payload = build_relist_payload(full_listing, config)

            if config.get("dry_run", False):
                log(f"  [DRY RUN] Would create listing: {json.dumps(payload, indent=2)[:200]}...")
                state["relisted"][listing_id] = {
                    "dry_run": True,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            else:
                # Create the new listing
                result = create_listing(token, payload)
                new_id = result.get("listing", {}).get("id", "unknown")
                log(f"  ✅ Created new listing ID: {new_id}")

                state["relisted"][listing_id] = {
                    "new_listing_id": str(new_id),
                    "title": title,
                    "sku": sku,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                time.sleep(1)  # Rate limiting

            relisted_count += 1

        except Exception as e:
            log(f"  ❌ Failed to relist '{title}': {e}")
            state["relisted"][listing_id] = {
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    # Update state
    state["last_check"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    save_state(state)

    log(f"Done. Relisted: {relisted_count}, Skipped (already processed): {skipped_count}")


def reset_state():
    """Reset state file to start fresh."""
    if STATE_PATH.exists():
        STATE_PATH.unlink()
    log("State reset. Next run will look back to initial_lookback_days.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_state()
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(__doc__)
        print("\nUsage:")
        print("  python3 reverb-relister.py          # Run the relister")
        print("  python3 reverb-relister.py --dry-run # Preview without creating listings")
        print("  python3 reverb-relister.py --reset   # Reset state (reprocess all)")
        sys.exit(0)

    config = load_config()

    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        config["dry_run"] = True
        log("=== DRY RUN MODE ===")

    run(config)
