"""Refresh the committed signals.json from the live API.

Run daily by .github/workflows/accuracy.yml. Railway's filesystem is
ephemeral, so a cold start (new environment or empty volume) boots from
the committed signals.json; keeping that copy fresh means cold starts
serve recent data and rarely trigger a token-burning regeneration.

Usage:
    python backend/refresh_committed_signals.py [--base-url https://...]
"""

import argparse
import json
import sys

import requests

DEFAULT_BASE_URL = "https://portfolio-builder.up.railway.app"
SIGNALS_PATH = "signals.json"


def fetch_live_signals(base_url):
    response = requests.get(
        f"{base_url}/api/signals", params={"limit": 50}, timeout=30
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("data", []), payload.get("generated_at")


def should_refresh(signals, generated_at, existing):
    """Refresh only with real, newer data — never regress the committed copy."""
    if not signals or not generated_at:
        return False, "live API returned no signals"
    if any(s.get("source") == "mock" for s in signals):
        return False, "live signals contain mock fallback data"
    existing_at = (existing or {}).get("generated_at") or ""
    if existing_at >= generated_at:
        return False, f"committed copy already as fresh ({existing_at})"
    return True, ""


def main(base_url=DEFAULT_BASE_URL, path=SIGNALS_PATH):
    signals, generated_at = fetch_live_signals(base_url)

    try:
        with open(path, encoding="utf-8-sig") as f:
            existing = json.load(f)
    except (OSError, json.JSONDecodeError):
        existing = None

    refresh, reason = should_refresh(signals, generated_at, existing)
    if not refresh:
        print(f"[Refresh] Keeping committed signals.json: {reason}")
        return 0

    with open(path, "w", encoding="utf-8") as f:
        json.dump({"signals": signals, "generated_at": generated_at}, f, indent=2)
    print(f"[Refresh] signals.json refreshed: {len(signals)} signals, generated_at={generated_at}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    sys.exit(main(base_url=args.base_url))
