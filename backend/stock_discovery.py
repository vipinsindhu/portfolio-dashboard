"""
Auto-discovery of high-quality stocks/ETFs from Finnhub
Fetches and filters stocks by quality metrics (market cap, volume, price)
"""

import os
import json
import requests
from datetime import datetime, timedelta

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
FINNHUB_BASE = "https://finnhub.io/api/v1"

# Cache file for discovered stocks
STOCK_DISCOVERY_CACHE = "stock_discovery_cache.json"

# Quality filters
QUALITY_FILTERS = {
    "min_market_cap": 10_000_000_000,  # $10B minimum
    "min_daily_volume": 1_000_000,      # 1M shares/day minimum
    "min_price": 10,                    # $10 minimum (avoid penny stocks)
}

# Popular ETFs to always include
POPULAR_ETFS = [
    # Stock ETFs
    ("VTI", "Vanguard Total Stock Market ETF", "Index"),
    ("VOO", "Vanguard S&P 500 ETF", "Index"),
    ("SPY", "SPDR S&P 500 ETF Trust", "Index"),
    ("QQQ", "Invesco QQQ Trust", "Technology"),
    ("IWM", "iShares Russell 2000 ETF", "Index"),
    # Bond ETFs
    ("AGG", "iShares Core Aggregate Bond ETF", "Index"),
    ("BND", "Vanguard Total Bond Market ETF", "Index"),
]

# Sector mappings for better categorization
SECTOR_MAPPINGS = {
    # Original 9 sectors
    "Technology": "Technology",
    "Healthcare": "Healthcare",
    "Financials": "Financials",
    "Industrials": "Industrials",
    "Consumer Cyclical": "Retail & E-commerce",
    "Consumer Defensive": "Food & Beverage",
    "Energy": "Energy",
    "Utilities": "Utilities",
    "Real Estate": "Real Estate",
    "Materials": "Materials",

    # New 8 sectors
    "Semiconductors": "Semiconductors",
    "Semiconductor Equipment": "Semiconductors",
    "Telecommunications": "Telecommunications",
    "Communication Services": "Telecommunications",
    "Aerospace & Defense": "Defense & Aerospace",
    "Banks": "Banking",
    "Specialty Finance": "Banking",
    "Insurance": "Insurance",
    "Pharmaceutical": "Pharma & Biotech",
    "Biotechnology": "Pharma & Biotech",
    "Retail": "Retail & E-commerce",
    "Internet Retail": "Retail & E-commerce",
    "Food Products": "Food & Beverage",
    "Beverages": "Food & Beverage",
    "Restaurants": "Food & Beverage",
}


def load_cache():
    """Load cached discovered stocks"""
    if os.path.exists(STOCK_DISCOVERY_CACHE):
        try:
            with open(STOCK_DISCOVERY_CACHE, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                cached_at = datetime.fromisoformat(data.get("cached_at", ""))
                # Cache valid for 24 hours
                if datetime.now() - cached_at < timedelta(hours=24):
                    print(f"Using cached stocks from {cached_at}")
                    return data.get("stocks", [])
        except Exception as e:
            print(f"Error loading cache: {e}")
    return None


def save_cache(stocks):
    """Save discovered stocks to cache"""
    try:
        with open(STOCK_DISCOVERY_CACHE, 'w', encoding='utf-8') as f:
            json.dump({
                "stocks": stocks,
                "cached_at": datetime.now().isoformat()
            }, f, indent=2)
        print(f"Cached {len(stocks)} stocks")
    except Exception as e:
        print(f"Error saving cache: {e}")


def get_major_stocks_from_finnhub():
    """Fetch major stocks from Finnhub (S&P 500 + popular)"""
    try:
        # Get S&P 500 stocks
        response = requests.get(
            f"{FINNHUB_BASE}/stock/list",
            params={"token": FINNHUB_API_KEY},
            timeout=10
        )

        if response.status_code == 200:
            stocks = response.json()
            print(f"Fetched {len(stocks)} stocks from Finnhub")
            return stocks
        else:
            print(f"Finnhub error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching from Finnhub: {e}")
        return []


def filter_quality_stocks(stocks):
    """
    Filter stocks by quality metrics
    - Market cap > $10 billion
    - Daily volume > 1 million
    - Price > $10
    """
    quality_stocks = []

    for stock in stocks:
        try:
            # Extract data
            ticker = stock.get("symbol", "")
            market_cap = stock.get("marketCap", 0) or 0
            volume = stock.get("volume", 0) or 0
            price = stock.get("last", 0) or 0
            sector = SECTOR_MAPPINGS.get(stock.get("finnhubIndustry", ""), "Other")

            # Apply quality filters
            if (market_cap >= QUALITY_FILTERS["min_market_cap"] and
                volume >= QUALITY_FILTERS["min_daily_volume"] and
                price >= QUALITY_FILTERS["min_price"]):

                quality_stocks.append({
                    "ticker": ticker,
                    "name": stock.get("description", ticker),
                    "sector": sector,
                    "market_cap": market_cap,
                    "price": price,
                    "volume": volume
                })
        except Exception as e:
            print(f"Error processing stock: {e}")
            continue

    print(f"Filtered to {len(quality_stocks)} quality stocks")
    return quality_stocks


def select_top_per_sector(stocks, top_n=5):
    """Select top N stocks per sector by market cap"""
    by_sector = {}

    # Group by sector
    for stock in stocks:
        sector = stock.get("sector", "Other")
        if sector not in by_sector:
            by_sector[sector] = []
        by_sector[sector].append(stock)

    # Select top N from each sector
    selected = []
    for sector, sector_stocks in by_sector.items():
        # Sort by market cap descending
        sorted_stocks = sorted(sector_stocks, key=lambda x: x.get("market_cap", 0), reverse=True)
        selected.extend(sorted_stocks[:top_n])

    return selected


def discover_stocks():
    """
    Main function: Discover high-quality stocks
    Returns list of tickers to analyze
    """
    print("\n🔍 Discovering high-quality stocks...")

    # Try cache first
    cached = load_cache()
    if cached:
        tickers = [s["ticker"] for s in cached]
        return tickers

    # Fetch from Finnhub
    print("Fetching from Finnhub API...")
    stocks = get_major_stocks_from_finnhub()

    if not stocks:
        print("⚠️  Could not fetch stocks from Finnhub, using fallback")
        # Convert fallback tickers to dicts with sector info
        fallback_tickers = get_fallback_stocks()
        fallback_stocks = [
            {
                "ticker": ticker,
                "name": ticker,
                "sector": TICKER_SECTOR_MAP.get(ticker, "Unknown"),
                "market_cap": 0,
                "price": 0,
                "volume": 0
            }
            for ticker in fallback_tickers
        ]
        # Return tickers from all fallback stocks
        tickers = [s["ticker"] for s in fallback_stocks]
        print(f"✅ Using {len(tickers)} fallback stocks: {', '.join(tickers[:15])}...")
        return tickers

    # Filter for quality
    print("Filtering for quality stocks...")
    quality_stocks = filter_quality_stocks(stocks)

    # Select top per sector
    print("Selecting top stocks per sector...")
    selected_stocks = select_top_per_sector(quality_stocks, top_n=5)

    # Add popular ETFs
    selected_stocks.extend([
        {
            "ticker": etf[0],
            "name": etf[1],
            "sector": etf[2],
            "market_cap": 0,
            "price": 0,
            "volume": 0
        }
        for etf in POPULAR_ETFS
    ])

    # Save to cache
    save_cache(selected_stocks)

    # Return tickers
    tickers = [s["ticker"] for s in selected_stocks]
    print(f"✅ Discovered {len(tickers)} quality stocks/ETFs: {', '.join(tickers[:10])}...")

    return tickers


# Ticker to sector mapping for fallback stocks
TICKER_SECTOR_MAP = {
    # Technology
    "AAPL": "Technology",
    "MSFT": "Technology",
    "GOOGL": "Technology",
    "META": "Technology",
    # Semiconductors
    "NVDA": "Semiconductors",
    "AMD": "Semiconductors",
    "QCOM": "Semiconductors",
    # Healthcare
    "JNJ": "Healthcare",
    "UNH": "Healthcare",
    # Pharma & Biotech
    "PFE": "Pharma & Biotech",
    "ABBV": "Pharma & Biotech",
    # Financials
    "JPM": "Financials",
    "BAC": "Financials",
    # Banking
    "C": "Banking",
    "WFC": "Banking",
    # Insurance
    "BRK.B": "Insurance",
    "MET": "Insurance",
    # Energy
    "XOM": "Energy",
    "CVX": "Energy",
    # Industrials
    "BA": "Industrials",
    "CAT": "Industrials",
    # Consumer Discretionary/Retail & E-commerce
    "AMZN": "Retail & E-commerce",
    "WMT": "Retail & E-commerce",
    "TSLA": "Retail & E-commerce",
    # Telecommunications
    "VZ": "Telecommunications",
    "T": "Telecommunications",
    # Utilities
    "NEE": "Utilities",
    "SO": "Utilities",
    # Materials
    "NEM": "Materials",
    "SCCO": "Materials",
    # Real Estate
    "PLD": "Real Estate",
    "EQIX": "Real Estate",
    # Defense & Aerospace
    "LMT": "Defense & Aerospace",
    "RTX": "Defense & Aerospace",
    # Food & Beverage
    "KO": "Food & Beverage",
    "PEP": "Food & Beverage",
    "MCD": "Food & Beverage",
    # ETFs (Index/Multi-asset)
    "VTI": "Index",
    "VOO": "Index",
    "SPY": "Index",
    "QQQ": "Technology",
    "IWM": "Index",
    "AGG": "Index",
    "BND": "Index"
}


def get_fallback_stocks():
    """Fallback list spanning 17 sectors for diverse coverage"""
    return [
        # Technology
        "AAPL", "MSFT", "GOOGL", "META",
        # Semiconductors
        "NVDA", "AMD", "QCOM",
        # Healthcare
        "JNJ", "UNH",
        # Pharma & Biotech
        "PFE", "ABBV",
        # Financials
        "JPM", "BAC",
        # Banking
        "C", "WFC",
        # Insurance
        "BRK.B", "MET",
        # Energy
        "XOM", "CVX",
        # Industrials
        "BA", "CAT",
        # Consumer Discretionary/Retail & E-commerce
        "AMZN", "WMT", "TSLA",
        # Telecommunications
        "VZ", "T",
        # Utilities
        "NEE", "SO",
        # Materials
        "NEM", "SCCO",
        # Real Estate
        "PLD", "EQIX",
        # Defense & Aerospace
        "LMT", "RTX",
        # Food & Beverage
        "KO", "PEP", "MCD",
        # ETFs
        "VTI", "VOO", "SPY", "QQQ", "IWM", "AGG", "BND"
    ]
