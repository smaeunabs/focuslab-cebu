#!/usr/bin/env python3
"""
update-google-reviews.py

Pulls the current Google rating + review count for FocusLab Coworking Space
from the Google Places API (New) and updates index.html in place. If the
numbers changed, commits and pushes automatically (unless --no-git/--dry-run).

ONE-TIME SETUP
--------------
1. Google Cloud Console (console.cloud.google.com) -> create/select a project.
2. APIs & Services > Library -> enable "Places API (New)".
3. APIs & Services > Credentials -> Create Credentials > API key.
   Restrict it: API restrictions -> "Places API (New)" only.
4. Copy .env.example to .env in the repo root and paste the key in as
   GOOGLE_PLACES_API_KEY. (.env is gitignored -- never commit it.)
5. Find your Place ID (only needs to be done once):
     python3 scripts/update-google-reviews.py --find-place-id
   Copy the correct "id" value into .env as GOOGLE_PLACE_ID.
6. Sanity check without writing anything:
     python3 scripts/update-google-reviews.py --dry-run
7. Schedule it weekly -- see scripts/README.md.

USAGE
-----
  python3 scripts/update-google-reviews.py             # update + commit + push if changed
  python3 scripts/update-google-reviews.py --dry-run    # show what would change, write nothing
  python3 scripts/update-google-reviews.py --no-git     # update index.html only, skip git
  python3 scripts/update-google-reviews.py --find-place-id
"""

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = REPO_ROOT / "index.html"
ENV_FILE = REPO_ROOT / ".env"

BUSINESS_NAME = "FocusLab Coworking Space"
BUSINESS_ADDRESS = "Southscape Commercial Bldg., Lawa-an, Talisay City, Cebu, Philippines"


def load_env():
    """Minimal .env loader so we don't need a third-party dependency."""
    env = dict(os.environ)
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            env.setdefault(key.strip(), val.strip().strip('"').strip("'"))
    return env


def api_call(url, api_key, field_mask=None, method="GET", body=None):
    headers = {"X-Goog-Api-Key": api_key}
    if field_mask:
        headers["X-Goog-FieldMask"] = field_mask
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, headers=headers, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Google API error {e.code}: {e.read().decode()}", file=sys.stderr)
        raise


def find_place_id(api_key):
    """One-time helper: text-search for the business and print candidate place IDs."""
    url = "https://places.googleapis.com/v1/places:searchText"
    body = {"textQuery": f"{BUSINESS_NAME}, {BUSINESS_ADDRESS}"}
    result = api_call(
        url, api_key,
        field_mask="places.id,places.displayName,places.formattedAddress",
        method="POST", body=body,
    )
    places = result.get("places", [])
    if not places:
        print("No places found. Try adjusting BUSINESS_NAME/BUSINESS_ADDRESS in the script.")
        return
    print("Candidate place IDs:\n")
    for p in places:
        print(f"  id:      {p.get('id')}")
        print(f"  name:    {p.get('displayName', {}).get('text')}")
        print(f"  address: {p.get('formattedAddress')}\n")
    print("Copy the correct 'id' value into .env as GOOGLE_PLACE_ID=...")


def fetch_rating(api_key, place_id):
    url = f"https://places.googleapis.com/v1/places/{place_id}"
    result = api_call(url, api_key, field_mask="rating,userRatingCount")
    rating = result.get("rating")
    count = result.get("userRatingCount")
    if rating is None or count is None:
        raise RuntimeError(f"Unexpected API response: {result}")
    return rating, count


def update_index_html(rating, count, dry_run=False):
    text = INDEX_HTML.read_text()
    rating_str = f"{rating:.1f}"
    count_str = str(count)

    # 1) JSON-LD aggregateRating block
    schema_pattern = re.compile(
        r'("aggregateRating":\s*\{\s*"@type":\s*"AggregateRating",\s*'
        r'"ratingValue":\s*")([\d.]+)("\s*,\s*"reviewCount":\s*")(\d+)("\s*\})'
    )
    m = schema_pattern.search(text)
    if not m:
        raise RuntimeError("Could not find aggregateRating block in index.html")
    old_rating, old_count = m.group(2), m.group(4)
    text = schema_pattern.sub(rf"\g<1>{rating_str}\g<3>{count_str}\g<5>", text, count=1)

    # 2) Visible gbp-rating widget
    widget_pattern = re.compile(r"(<span><b>)([\d.]+)(</b>\s*·\s*)(\d+)(\s*Google reviews</span>)")
    m2 = widget_pattern.search(text)
    if not m2:
        raise RuntimeError("Could not find the visible Google reviews widget in index.html")
    text = widget_pattern.sub(rf"\g<1>{rating_str}\g<3>{count_str}\g<5>", text, count=1)

    changed = (old_rating != rating_str) or (old_count != count_str)

    print(f"Live from Google:         {rating_str} stars, {count_str} reviews")
    print(f"Currently on site:        {old_rating} stars, {old_count} reviews")

    if not changed:
        print("No change needed.")
        return False

    if dry_run:
        print("[dry run] Would update index.html and stop here (no commit/push).")
        return True

    INDEX_HTML.write_text(text)
    print("index.html updated.")
    return True


def git_commit_and_push(rating_str, count_str):
    def run(cmd):
        return subprocess.run(cmd, cwd=REPO_ROOT, check=True, capture_output=True, text=True)

    run(["git", "add", "index.html"])
    run(["git", "commit", "-m", f"Auto-update Google review stats to {rating_str} stars, {count_str} reviews"])
    run(["git", "push"])
    print("Committed and pushed.")


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    no_git = "--no-git" in args
    do_find_place_id = "--find-place-id" in args

    env = load_env()
    api_key = env.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        sys.exit("Missing GOOGLE_PLACES_API_KEY. Set it in .env (see .env.example).")

    if do_find_place_id:
        find_place_id(api_key)
        return

    place_id = env.get("GOOGLE_PLACE_ID")
    if not place_id:
        sys.exit("Missing GOOGLE_PLACE_ID. Run with --find-place-id first, then set it in .env.")

    rating, count = fetch_rating(api_key, place_id)
    rating_str = f"{rating:.1f}"
    count_str = str(count)

    changed = update_index_html(rating, count, dry_run=dry_run)

    if changed and not dry_run and not no_git:
        git_commit_and_push(rating_str, count_str)


if __name__ == "__main__":
    main()
