#!/usr/bin/env python3
"""
Fetch Oura Ring period data (API v2) and save to docs/data.json.

Oura stores menstrual cycle data as enhanced_tag entries with
tag_type_code == "tag_generic_period". Each entry has start_day / end_day
that mark the span of a period.

Usage:
    OURA_TOKEN=<token> python fetch_oura.py
"""

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import requests

OURA_TOKEN = os.environ.get("OURA_TOKEN")
if not OURA_TOKEN:
    print("Error: OURA_TOKEN environment variable is not set.", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://api.ouraring.com/v2/usercollection"
HEADERS = {"Authorization": f"Bearer {OURA_TOKEN}"}
TIMEOUT = 30


def fetch_all(endpoint: str, params: dict) -> list:
    """Fetch all pages from an Oura API v2 endpoint (handles next_token pagination)."""
    url = f"{BASE_URL}/{endpoint}"
    all_data: list = []
    p = dict(params)

    while True:
        resp = requests.get(url, headers=HEADERS, params=p, timeout=TIMEOUT)
        resp.raise_for_status()
        body = resp.json()
        all_data.extend(body.get("data", []))
        next_token = body.get("next_token")
        if not next_token:
            break
        p = {**params, "next_token": next_token}

    return all_data


def main() -> None:
    end_date = date.today()
    # Go back 2 years to capture enough cycles for statistics
    start_date = end_date - timedelta(days=730)
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }

    print(f"Fetching Oura data: {start_date} → {end_date}")

    all_tags = fetch_all("enhanced_tag", params)
    periods = [t for t in all_tags if t.get("tag_type_code") == "tag_generic_period"]
    periods.sort(key=lambda t: t["start_day"])
    print(f"  enhanced_tag (period): {len(periods)} records")

    output = {
        "periods": periods,
        "meta": {
            "start_date": params["start_date"],
            "end_date": params["end_date"],
            "fetched_at": end_date.isoformat(),
        },
    }

    dest = Path(__file__).parent / "docs" / "data.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"Saved → {dest}")


if __name__ == "__main__":
    main()
