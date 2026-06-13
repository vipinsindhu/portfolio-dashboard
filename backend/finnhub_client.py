"""
Shared Finnhub API client.

Centralises /stock/profile2 calls with a single in-process cache so
analysis.py and signals.py never issue duplicate requests for the same
ticker within the same process.
"""
import os
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict

from sector_config import normalize_sector

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
FINNHUB_BASE = "https://finnhub.io/api/v1"

_PROFILE_CACHE: Dict = {}  # ticker -> (cached_at: datetime, data: dict)
_PROFILE_CACHE_TTL = timedelta(hours=24)


def fetch_profile(ticker: str) -> dict:
    """Return {sector, market_cap, company_name} for ticker via /stock/profile2.

    Cached in-process with a 24-hour TTL. Returns an empty-field dict on any
    failure so callers can always do result.get("sector") safely.
    """
    cached = _PROFILE_CACHE.get(ticker)
    if cached and datetime.now(timezone.utc) - cached[0] < _PROFILE_CACHE_TTL:
        return cached[1]

    result: dict = {"sector": "", "market_cap": 0, "company_name": ""}

    if FINNHUB_API_KEY:
        try:
            r = requests.get(
                f"{FINNHUB_BASE}/stock/profile2",
                params={"symbol": ticker, "token": FINNHUB_API_KEY},
                timeout=5,
            )
            if r.status_code == 200:
                data = r.json()
                mc = data.get("marketCapitalization")
                raw_sector = (data.get("finnhubIndustry") or "").strip()
                if raw_sector:
                    result["sector"] = normalize_sector(raw_sector)
                if mc:
                    result["market_cap"] = int(mc * 1_000_000)
                result["company_name"] = data.get("name") or ""
                _PROFILE_CACHE[ticker] = (datetime.now(timezone.utc), result)
        except Exception as e:
            print(f"[Finnhub] Error fetching profile for {ticker}: {e}")

    return result
