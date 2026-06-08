"""
Index fund decomposer - breaks down index funds into constituent sectors
Fetches top holdings and calculates weighted sector allocation
"""

import json
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
FINNHUB_BASE = "https://finnhub.io/api/v1"
INDEX_DECOMPOSITION_CACHE_FILE = "index_decomposition_cache.json"
SECTOR_MAP_FILE = "sector_map.json"

# Fallback index fund decompositions (pre-configured sector allocations)
# Based on current market compositions as of 2026
INDEX_FUND_ALLOCATIONS = {
    # US Broad Market (Total Market)
    "VTI": {
        "Technology": 0.27,
        "Financials": 0.14,
        "Healthcare": 0.12,
        "Industrials": 0.08,
        "Consumer": 0.08,
        "Energy": 0.04,
        "Utilities": 0.04,
        "Materials": 0.02,
        "Real Estate": 0.03,
    },
    "VTSAX": {
        "Technology": 0.27,
        "Financials": 0.14,
        "Healthcare": 0.12,
        "Industrials": 0.08,
        "Consumer": 0.08,
        "Energy": 0.04,
        "Utilities": 0.04,
        "Materials": 0.02,
        "Real Estate": 0.03,
    },
    "VTSXF": {
        "Technology": 0.27,
        "Financials": 0.14,
        "Healthcare": 0.12,
        "Industrials": 0.08,
        "Consumer": 0.08,
        "Energy": 0.04,
        "Utilities": 0.04,
        "Materials": 0.02,
        "Real Estate": 0.03,
    },
    "FSKAX": {
        "Technology": 0.27,
        "Financials": 0.14,
        "Healthcare": 0.12,
        "Industrials": 0.08,
        "Consumer": 0.08,
        "Energy": 0.04,
        "Utilities": 0.04,
        "Materials": 0.02,
        "Real Estate": 0.03,
    },
    # US S&P 500 (Large Cap - more tech-heavy)
    "VOO": {
        "Technology": 0.30,
        "Financials": 0.13,
        "Healthcare": 0.11,
        "Industrials": 0.08,
        "Consumer": 0.08,
        "Energy": 0.04,
        "Utilities": 0.03,
        "Materials": 0.02,
        "Real Estate": 0.02,
    },
    "SPY": {
        "Technology": 0.30,
        "Financials": 0.13,
        "Healthcare": 0.11,
        "Industrials": 0.08,
        "Consumer": 0.08,
        "Energy": 0.04,
        "Utilities": 0.03,
        "Materials": 0.02,
        "Real Estate": 0.02,
    },
    "FXAIX": {
        "Technology": 0.30,
        "Financials": 0.13,
        "Healthcare": 0.11,
        "Industrials": 0.08,
        "Consumer": 0.08,
        "Energy": 0.04,
        "Utilities": 0.03,
        "Materials": 0.02,
        "Real Estate": 0.02,
    },
    "VFIAX": {
        "Technology": 0.30,
        "Financials": 0.13,
        "Healthcare": 0.11,
        "Industrials": 0.08,
        "Consumer": 0.08,
        "Energy": 0.04,
        "Utilities": 0.03,
        "Materials": 0.02,
        "Real Estate": 0.02,
    },
    "IVV": {
        "Technology": 0.30,
        "Financials": 0.13,
        "Healthcare": 0.11,
        "Industrials": 0.08,
        "Consumer": 0.08,
        "Energy": 0.04,
        "Utilities": 0.03,
        "Materials": 0.02,
        "Real Estate": 0.02,
    },
    "SPLG": {
        "Technology": 0.30,
        "Financials": 0.13,
        "Healthcare": 0.11,
        "Industrials": 0.08,
        "Consumer": 0.08,
        "Energy": 0.04,
        "Utilities": 0.03,
        "Materials": 0.02,
        "Real Estate": 0.02,
    },
    # US Mid-Cap
    "IJH": {
        "Technology": 0.20,
        "Financials": 0.16,
        "Industrials": 0.12,
        "Healthcare": 0.12,
        "Consumer": 0.10,
        "Energy": 0.06,
        "Materials": 0.05,
        "Utilities": 0.04,
        "Real Estate": 0.04,
        "Utilities": 0.05
    },
    # US Small-Cap
    "IJR": {
        "Financials": 0.18,
        "Industrials": 0.14,
        "Technology": 0.14,
        "Healthcare": 0.12,
        "Consumer": 0.10,
        "Energy": 0.08,
        "Materials": 0.06,
        "Real Estate": 0.05,
        "Utilities": 0.04,
        "Commodities": 0.01
    },
    "SCHX": {
        "Technology": 0.25,
        "Financials": 0.14,
        "Healthcare": 0.11,
        "Industrials": 0.09,
        "Consumer": 0.08,
        "Energy": 0.05,
        "Utilities": 0.04,
        "Materials": 0.02,
        "Real Estate": 0.02,
    },
    # Broad Market
    "SCHB": {
        "Technology": 0.27,
        "Financials": 0.14,
        "Healthcare": 0.12,
        "Industrials": 0.08,
        "Consumer": 0.08,
        "Energy": 0.04,
        "Utilities": 0.04,
        "Materials": 0.02,
        "Real Estate": 0.03,
    },
    "SWTSX": {
        "Technology": 0.27,
        "Financials": 0.14,
        "Healthcare": 0.12,
        "Industrials": 0.08,
        "Consumer": 0.08,
        "Energy": 0.04,
        "Utilities": 0.04,
        "Materials": 0.02,
        "Real Estate": 0.03,
    },
    # Dividend Focused
    "SCHD": {
        "Financials": 0.20,
        "Utilities": 0.18,
        "Healthcare": 0.16,
        "Consumer": 0.14,
        "Energy": 0.10,
        "Industrials": 0.08,
        "Materials": 0.04,
        "Technology": 0.04,
        "Real Estate": 0.03,
        "Commodities": 0.03
    },
    # International Equities
    "VXUS": {
        "Financials": 0.20,
        "Technology": 0.16,
        "Healthcare": 0.10,
        "Industrials": 0.10,
        "Consumer": 0.10,
        "Energy": 0.08,
        "Utilities": 0.05,
        "Materials": 0.05,
        "Real Estate": 0.04,
        "Commodities": 0.01
    },
    "VTIAX": {
        "Financials": 0.20,
        "Technology": 0.16,
        "Healthcare": 0.10,
        "Industrials": 0.10,
        "Consumer": 0.10,
        "Energy": 0.08,
        "Utilities": 0.05,
        "Materials": 0.05,
        "Real Estate": 0.04,
        "Commodities": 0.01
    },
    "SCHF": {
        "Financials": 0.20,
        "Technology": 0.16,
        "Healthcare": 0.10,
        "Industrials": 0.10,
        "Consumer": 0.10,
        "Energy": 0.08,
        "Utilities": 0.05,
        "Materials": 0.05,
        "Real Estate": 0.04,
        "Commodities": 0.01
    },
    # Emerging Markets
    "EEM": {
        "Financials": 0.22,
        "Technology": 0.20,
        "Consumer": 0.14,
        "Industrials": 0.10,
        "Healthcare": 0.08,
        "Energy": 0.08,
        "Materials": 0.06,
        "Utilities": 0.04,
        "Real Estate": 0.04
    },
    "IEMG": {
        "Financials": 0.22,
        "Technology": 0.20,
        "Consumer": 0.14,
        "Industrials": 0.10,
        "Healthcare": 0.08,
        "Energy": 0.08,
        "Materials": 0.06,
        "Utilities": 0.04,
        "Real Estate": 0.04
    },
    "VWO": {
        "Financials": 0.22,
        "Technology": 0.20,
        "Consumer": 0.14,
        "Industrials": 0.10,
        "Healthcare": 0.08,
        "Energy": 0.08,
        "Materials": 0.06,
        "Utilities": 0.04,
        "Real Estate": 0.04
    },
    # AT&T Plan Internal Funds (Large Cap U.S. Stock Index)
    "NON40OJPF": {
        "Technology": 0.33,
        "Financials": 0.16,
        "Healthcare": 0.14,
        "Industrials": 0.10,
        "Consumer": 0.10,
        "Energy": 0.05,
        "Utilities": 0.05,
        "Materials": 0.03,
        "Real Estate": 0.04
    },
    # AT&T Plan Internal Funds (Total U.S. Stock Index)
    "NON40OJJ4": {
        "Technology": 0.33,
        "Financials": 0.17,
        "Healthcare": 0.15,
        "Industrials": 0.10,
        "Consumer": 0.10,
        "Energy": 0.05,
        "Utilities": 0.05,
        "Materials": 0.03,
        "Real Estate": 0.02
    },
    # AT&T Plan Internal Funds (Small & Mid U.S. Stock Index)
    "NON40OJPG": {
        "Financials": 0.18,
        "Industrials": 0.16,
        "Technology": 0.16,
        "Healthcare": 0.14,
        "Consumer": 0.11,
        "Energy": 0.09,
        "Materials": 0.07,
        "Real Estate": 0.06,
        "Utilities": 0.05,
        "Commodities": 0.02
    },
    # AT&T Plan Internal Funds (International Stock Index)
    "NON40OJJ8": {
        "Financials": 0.23,
        "Technology": 0.18,
        "Healthcare": 0.12,
        "Industrials": 0.11,
        "Consumer": 0.11,
        "Energy": 0.09,
        "Utilities": 0.06,
        "Materials": 0.06,
        "Real Estate": 0.04
    },
    # AT&T Plan Internal Funds (International Stock Fund)
    "NON40OJJ6": {
        "Financials": 0.23,
        "Technology": 0.18,
        "Healthcare": 0.12,
        "Industrials": 0.11,
        "Consumer": 0.11,
        "Energy": 0.09,
        "Utilities": 0.06,
        "Materials": 0.06,
        "Real Estate": 0.04
    },
    # AT&T Plan Internal Funds (AT&T Shares Fund)
    "NON40OJPH": {
        "Technology": 0.33,
        "Financials": 0.16,
        "Healthcare": 0.14,
        "Industrials": 0.10,
        "Consumer": 0.10,
        "Energy": 0.05,
        "Utilities": 0.05,
        "Materials": 0.03,
        "Real Estate": 0.04
    },
    # AT&T Plan Internal Funds (Asset Allocation 2040 - Target Date Fund)
    "NON40OJI9": {
        "Technology": 0.20,
        "Financials": 0.13,
        "Healthcare": 0.10,
        "Industrials": 0.07,
        "Consumer": 0.07,
        "Bonds": 0.31,
        "Energy": 0.03,
        "Utilities": 0.03,
        "Materials": 0.02,
        "Real Estate": 0.02,
        "Commodities": 0.01,
        "Cryptocurrencies": 0.01
    },
}


def load_sector_map() -> Dict[str, str]:
    """Load sector mappings from file"""
    if os.path.exists(SECTOR_MAP_FILE):
        try:
            with open(SECTOR_MAP_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Index Decomposer] Error loading sector map: {e}")
    return {}


def load_decomposition_cache() -> Dict:
    """Load cached index decompositions"""
    if os.path.exists(INDEX_DECOMPOSITION_CACHE_FILE):
        try:
            with open(INDEX_DECOMPOSITION_CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Index Decomposer] Error loading cache: {e}")
    return {}


def save_decomposition_cache(cache: Dict):
    """Save updated decomposition cache"""
    try:
        with open(INDEX_DECOMPOSITION_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"[Index Decomposer] Error saving cache: {e}")


def fetch_index_holdings(symbol: str) -> Optional[List[Tuple[str, float]]]:
    """
    Fetch top holdings of an index fund from Finnhub
    Returns list of (holding_symbol, weight) tuples
    """
    if not FINNHUB_API_KEY:
        return None

    try:
        url = f"{FINNHUB_BASE}/stock/holdings"
        response = requests.get(
            url,
            params={"symbol": symbol, "token": FINNHUB_API_KEY},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            holdings = data.get("holdings", [])

            if holdings:
                # Extract top holdings with their weights
                result = []
                for holding in holdings[:20]:  # Top 20 holdings
                    symbol_val = holding.get("symbol")
                    weight = holding.get("weight", 0) / 100  # Convert percentage to decimal
                    if symbol_val and weight > 0:
                        result.append((symbol_val, weight))

                return result if result else None
    except Exception as e:
        print(f"[Index Decomposer] Error fetching holdings for {symbol}: {e}")

    return None


def decompose_index(index_symbol: str, sector_map: Dict[str, str]) -> Optional[Dict[str, float]]:
    """
    Decompose an index fund into its sector allocation
    Returns dict of {sector: allocation_weight}
    """
    holdings = fetch_index_holdings(index_symbol)
    if not holdings:
        return None

    sector_weights = {}
    total_weight = 0

    for holding_symbol, holding_weight in holdings:
        # Get sector for this holding
        sector = sector_map.get(holding_symbol, "Other")

        if sector not in sector_weights:
            sector_weights[sector] = 0

        sector_weights[sector] += holding_weight
        total_weight += holding_weight

    # Normalize to 100% (in case weights don't add up perfectly)
    if total_weight > 0:
        for sector in sector_weights:
            sector_weights[sector] = sector_weights[sector] / total_weight

    return sector_weights if sector_weights else None


def decompose_all_indices():
    """
    Load pre-configured index fund sector allocations
    Updates cache with allocations
    """
    print("\n" + "="*60)
    print("[Index Decomposer] Loading index fund sector allocations")
    print(f"[Index Decomposer] Time: {datetime.now().isoformat()}")
    print("="*60)

    cache = load_decomposition_cache()
    decomposed_count = 0

    for index_symbol, allocation in INDEX_FUND_ALLOCATIONS.items():
        print(f"\n[Index Decomposer] Loading {index_symbol}...")

        cache[index_symbol] = {
            "sectors": allocation,
            "timestamp": datetime.now().isoformat(),
            "source": "static_allocation"
        }
        decomposed_count += 1

        # Print sector breakdown
        sorted_sectors = sorted(allocation.items(), key=lambda x: x[1], reverse=True)
        print(f"  [OK] Loaded allocation with {len(allocation)} sectors:")
        for sector, weight in sorted_sectors[:5]:  # Show top 5
            print(f"    - {sector}: {weight:.1%}")

    # Save cache
    save_decomposition_cache(cache)

    # Print summary
    print("\n" + "-"*60)
    print("[Index Decomposer] Allocation Summary:")
    print(f"  Loaded: {decomposed_count} index funds")
    print(f"  Cache size: {len(cache)} index funds")
    print("-"*60 + "\n")

    return cache


def get_index_decomposition(symbol: str) -> Optional[Dict[str, float]]:
    """
    Get cached decomposition for an index fund
    Returns dict of {sector: allocation_weight} or None
    """
    cache = load_decomposition_cache()

    if symbol in cache:
        decomposition = cache[symbol]
        return decomposition.get("sectors")

    return None


if __name__ == "__main__":
    # For manual testing
    decompose_all_indices()
