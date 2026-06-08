"""
Automated sector mapping updates from Finnhub
Runs on a scheduled interval to keep sector classifications current
"""

import json
import os
import requests
from datetime import datetime
from typing import Dict, List, Tuple

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
FINNHUB_BASE = "https://finnhub.io/api/v1"
SECTOR_MAP_FILE = "sector_map.json"
SECTOR_UPDATE_LOG_FILE = "sector_update_history.json"


def load_sector_map() -> Dict[str, str]:
    """Load sector mappings from file"""
    if os.path.exists(SECTOR_MAP_FILE):
        try:
            with open(SECTOR_MAP_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Sector Updater] Error loading sector map: {e}")
    return {}


def save_sector_map(sector_map: Dict[str, str]):
    """Save sector mappings to file"""
    try:
        with open(SECTOR_MAP_FILE, "w") as f:
            json.dump(sector_map, f, indent=2, sort_keys=True)
        print(f"[Sector Updater] Saved {len(sector_map)} sector mappings")
    except Exception as e:
        print(f"[Sector Updater] Error saving sector map: {e}")


def load_update_history() -> List[Dict]:
    """Load update history log"""
    if os.path.exists(SECTOR_UPDATE_LOG_FILE):
        try:
            with open(SECTOR_UPDATE_LOG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Sector Updater] Error loading history: {e}")
    return []


def save_update_history(history: List[Dict]):
    """Save update history log"""
    try:
        with open(SECTOR_UPDATE_LOG_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"[Sector Updater] Error saving history: {e}")


def fetch_sector_from_finnhub(symbol: str) -> Tuple[str, bool]:
    """
    Fetch sector from Finnhub API
    Returns (sector_name, success_flag)
    """
    if not FINNHUB_API_KEY:
        return None, False

    try:
        # Try company profile endpoint
        profile_url = f"{FINNHUB_BASE}/stock/profile2"
        response = requests.get(
            profile_url,
            params={"symbol": symbol, "token": FINNHUB_API_KEY},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            sector = data.get("finnhubIndustry")
            if sector:
                sector = sector.title() if isinstance(sector, str) else None
                return sector, True
    except Exception as e:
        print(f"[Sector Updater] Error fetching {symbol}: {e}")

    return None, False


def update_sector_mappings():
    """
    Scheduled job to update sector mappings from Finnhub
    Runs every 7 days to keep data current
    """
    print("\n" + "="*60)
    print("[Sector Updater] Starting scheduled update")
    print(f"[Sector Updater] Time: {datetime.now().isoformat()}")
    print("="*60)

    sector_map = load_sector_map()
    if not sector_map:
        print("[Sector Updater] No sector map found, skipping update")
        return

    history = load_update_history()
    update_record = {
        "timestamp": datetime.now().isoformat(),
        "changes": [],
        "checked": 0,
        "updated": 0,
        "failed": 0
    }

    total_stocks = len(sector_map)
    print(f"[Sector Updater] Checking {total_stocks} stocks for sector updates...")

    for idx, (symbol, current_sector) in enumerate(sector_map.items(), 1):
        # Rate limiting: print progress every 25 stocks
        if idx % 25 == 0:
            print(f"[Sector Updater] Progress: {idx}/{total_stocks}")

        update_record["checked"] += 1
        sector, success = fetch_sector_from_finnhub(symbol)

        if success and sector:
            if sector != current_sector:
                # Sector changed!
                old_sector = current_sector
                sector_map[symbol] = sector
                update_record["updated"] += 1

                change_record = {
                    "symbol": symbol,
                    "old_sector": old_sector,
                    "new_sector": sector,
                    "timestamp": datetime.now().isoformat()
                }
                update_record["changes"].append(change_record)
                print(f"  ✓ {symbol}: {old_sector} → {sector}")
        else:
            update_record["failed"] += 1

    # Save updated mappings
    if update_record["updated"] > 0:
        save_sector_map(sector_map)

    # Save update history
    history.append(update_record)
    save_update_history(history)

    # Print summary
    print("\n" + "-"*60)
    print("[Sector Updater] Update Summary:")
    print(f"  Checked: {update_record['checked']} stocks")
    print(f"  Updated: {update_record['updated']} stocks")
    print(f"  Failed:  {update_record['failed']} stocks")

    if update_record["changes"]:
        print("\n  Sector Changes:")
        for change in update_record["changes"]:
            print(f"    • {change['symbol']}: {change['old_sector']} → {change['new_sector']}")
    else:
        print("  No sector changes detected")

    print("-"*60 + "\n")


if __name__ == "__main__":
    # For manual testing
    update_sector_mappings()
