"""
Signal generation engine using Groq cloud LLM
Generates stock/ETF signals using Groq (Mixtral/Llama) + Finnhub data + FRED macro context
"""

import json
import os
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from groq import Groq
import yfinance as yf
from stock_discovery import discover_stocks, TICKER_SECTOR_MAP
from analysis import get_sector_for_stock

# Environment configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")  # Optional, FRED has generous free tier

# Lazy-initialize Groq client (only when needed, not at import time)
groq_client = None

def get_groq_client():
    global groq_client
    if groq_client is None:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY environment variable is required")
        groq_client = Groq(api_key=GROQ_API_KEY)
    return groq_client

# API endpoints
FINNHUB_BASE = "https://finnhub.io/api/v1"
FRED_BASE = "https://api.stlouisfed.org/fred"

# Signal candidates pool - stocks/ETFs to consider
SIGNAL_CANDIDATES = [
    # Technology (10)
    "AAPL", "MSFT", "GOOGL", "NVDA", "META", "TSLA", "AVGO", "MU", "QCOM", "AMD",
    # Financial Services (6)
    "JPM", "BAC", "GS", "MS", "BX", "KKR",
    # Healthcare (6)
    "JNJ", "UNH", "PFE", "LLY", "MRK", "TMO",
    # Consumer (6)
    "AMZN", "WMT", "MCD", "COST", "NKE", "TJX",
    # Industrials (4)
    "BA", "GE", "LMT", "CAT",
    # Energy (3)
    "XOM", "CVX", "MPC",
    # Real Estate (2)
    "AMT", "EQIX",
    # ETFs (6)
    "VTI", "VOO", "SPY", "QQQ", "AGG", "BND"
]

# Company metadata for Finnhub quote enrichment
COMPANY_NAMES = {
    "AAPL": "Apple Inc", "MSFT": "Microsoft Corporation", "GOOGL": "Alphabet Inc",
    "NVDA": "NVIDIA Corporation", "META": "Meta Platforms Inc", "TSLA": "Tesla Inc",
    "AVGO": "Broadcom Inc", "MU": "Micron Technology", "QCOM": "Qualcomm Inc", "AMD": "Advanced Micro Devices",
    "JPM": "JPMorgan Chase & Co", "BAC": "Bank of America Corp", "GS": "Goldman Sachs",
    "MS": "Morgan Stanley", "BX": "Blackstone Inc", "KKR": "KKR & Co Inc",
    "JNJ": "Johnson & Johnson", "UNH": "UnitedHealth Group Inc", "PFE": "Pfizer Inc",
    "LLY": "Eli Lilly and Company", "MRK": "Merck & Co", "TMO": "Thermo Fisher Scientific",
    "AMZN": "Amazon Inc", "WMT": "Walmart Inc", "MCD": "McDonald's Corp", "COST": "Costco Wholesale",
    "NKE": "Nike Inc", "TJX": "The TJX Companies",
    "BA": "Boeing Co", "GE": "General Electric", "LMT": "Lockheed Martin", "CAT": "Caterpillar Inc",
    "XOM": "Exxon Mobil Corp", "CVX": "Chevron Corp", "MPC": "Marathon Petroleum",
    "AMT": "American Tower Corp", "EQIX": "Equinix Inc",
    "VTI": "Vanguard Total Stock", "VOO": "Vanguard S&P 500", "SPY": "SPDR S&P 500",
    "QQQ": "Invesco QQQ Trust", "AGG": "iShares Core Aggregate", "BND": "Vanguard Total Bond"
}

COMPANY_SECTORS = {
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology",
    "NVDA": "Technology", "META": "Technology", "TSLA": "Consumer Discretionary",
    "AVGO": "Technology", "MU": "Technology", "QCOM": "Technology", "AMD": "Technology",
    "JPM": "Financials", "BAC": "Financials", "GS": "Financials",
    "MS": "Financials", "BX": "Financials", "KKR": "Financials",
    "JNJ": "Healthcare", "UNH": "Healthcare", "PFE": "Healthcare",
    "LLY": "Healthcare", "MRK": "Healthcare", "TMO": "Healthcare",
    "AMZN": "Consumer Discretionary", "WMT": "Consumer Staples", "MCD": "Consumer Discretionary",
    "COST": "Consumer Staples", "NKE": "Consumer Discretionary", "TJX": "Consumer Discretionary",
    "BA": "Industrials", "GE": "Industrials", "LMT": "Industrials", "CAT": "Industrials",
    "XOM": "Energy", "CVX": "Energy", "MPC": "Energy",
    "AMT": "Real Estate", "EQIX": "Real Estate",
    "VTI": "Index", "VOO": "Index", "SPY": "Index",
    "QQQ": "Technology", "AGG": "Index", "BND": "Index"
}

COMPANY_MARKET_CAPS = {
    "AAPL": 3000000000000, "MSFT": 3100000000000, "GOOGL": 2000000000000,
    "NVDA": 1200000000000, "META": 1300000000000, "TSLA": 900000000000,
    "AVGO": 320000000000, "MU": 160000000000, "QCOM": 220000000000, "AMD": 280000000000,
    "JPM": 500000000000, "BAC": 350000000000, "GS": 180000000000,
    "MS": 220000000000, "BX": 250000000000, "KKR": 200000000000,
    "JNJ": 450000000000, "UNH": 480000000000, "PFE": 220000000000,
    "LLY": 650000000000, "MRK": 300000000000, "TMO": 420000000000,
    "AMZN": 2000000000000, "WMT": 420000000000, "MCD": 200000000000,
    "COST": 420000000000, "NKE": 160000000000, "TJX": 100000000000,
    "BA": 200000000000, "GE": 240000000000, "LMT": 280000000000, "CAT": 220000000000,
    "XOM": 520000000000, "CVX": 420000000000, "MPC": 140000000000,
    "AMT": 200000000000, "EQIX": 180000000000,
    "VTI": 0, "VOO": 0, "SPY": 0, "QQQ": 0, "AGG": 0, "BND": 0
}

COMPANY_DIVIDEND_YIELDS = {
    "AAPL": 0.004, "MSFT": 0.007, "GOOGL": 0.0,
    "NVDA": 0.001, "META": 0.0, "TSLA": 0.0,
    "AVGO": 0.015, "MU": 0.0, "QCOM": 0.021, "AMD": 0.0,
    "JPM": 0.028, "BAC": 0.033, "GS": 0.024,
    "MS": 0.027, "BX": 0.035, "KKR": 0.031,
    "JNJ": 0.029, "UNH": 0.015, "PFE": 0.061,
    "LLY": 0.008, "MRK": 0.026, "TMO": 0.004,
    "AMZN": 0.0, "WMT": 0.014, "MCD": 0.022,
    "COST": 0.006, "NKE": 0.008, "TJX": 0.0,
    "BA": 0.0, "GE": 0.025, "LMT": 0.026, "CAT": 0.019,
    "XOM": 0.034, "CVX": 0.037, "MPC": 0.041,
    "AMT": 0.041, "EQIX": 0.019,
    "VTI": 0.015, "VOO": 0.015, "SPY": 0.015,
    "QQQ": 0.006, "AGG": 0.04, "BND": 0.042
}

# Signals storage file (lives on the persistent volume when DATA_DIR is set)
from storage_paths import data_path

SIGNALS_FILE = data_path("signals.json")
MACRO_CACHE_FILE = data_path("macro_cache.json")


def load_signals():
    """Load signals from JSON file"""
    if os.path.exists(SIGNALS_FILE):
        with open(SIGNALS_FILE, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    return {"signals": [], "generated_at": None}


def save_signals(data):
    """Save signals to JSON file"""
    with open(SIGNALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def save_macro_cache(macro_data):
    """Save macro data to cache file with timestamp"""
    cache = {
        "data": macro_data,
        "cached_at": datetime.now().isoformat()
    }
    try:
        with open(MACRO_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving macro cache: {e}")
        return False


def load_macro_cache():
    """Load macro data from cache file"""
    try:
        if os.path.exists(MACRO_CACHE_FILE):
            with open(MACRO_CACHE_FILE, 'r', encoding='utf-8-sig') as f:
                cache = json.load(f)
                return cache.get("data"), cache.get("cached_at")
    except Exception as e:
        print(f"Error loading macro cache: {e}")
    return None, None


def fetch_fundamentals_from_yfinance(ticker):
    """Fetch fundamentals from yfinance as fallback"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if info and info.get('currentPrice'):
            sector = get_sector_for_stock(ticker, TICKER_SECTOR_MAP)
            return {
                "ticker": ticker,
                "company_name": info.get('longName', ticker),
                "sector": sector,
                "market_cap": info.get('marketCap', 0),
                "pe_ratio": info.get('trailingPE'),
                "dividend_yield": info.get('dividendYield', 0),
                "52_week_high": info.get('fiftyTwoWeekHigh'),
                "52_week_low": info.get('fiftyTwoWeekLow'),
                "current_price": info.get('currentPrice'),
            }
    except Exception as e:
        pass

    return None


def fetch_fundamentals(ticker):
    """Fetch stock fundamentals with fallback chain: Finnhub → yfinance → mock"""
    # Priority 1: Try Finnhub
    if FINNHUB_API_KEY:
        try:
            quote_url = f"{FINNHUB_BASE}/quote"
            quote_response = requests.get(
                quote_url,
                params={"symbol": ticker, "token": FINNHUB_API_KEY},
                timeout=5
            )

            if quote_response.status_code == 200:
                quote = quote_response.json()

                if quote.get("c"):  # Current price exists
                    sector = COMPANY_SECTORS.get(ticker)
                    if not sector:
                        sector = get_sector_for_stock(ticker, TICKER_SECTOR_MAP)

                    profile = _fetch_finnhub_profile(ticker)
                    market_cap = profile.get("market_cap") or COMPANY_MARKET_CAPS.get(ticker, 0)
                    company_name = profile.get("company_name") or COMPANY_NAMES.get(ticker, ticker)

                    return {
                        "ticker": ticker,
                        "company_name": company_name,
                        "sector": sector,
                        "market_cap": market_cap,
                        "pe_ratio": quote.get("pe"),
                        "dividend_yield": COMPANY_DIVIDEND_YIELDS.get(ticker, 0),
                        "52_week_high": quote.get("h52", None),
                        "52_week_low": quote.get("l52", None),
                        "current_price": quote.get("c"),
                    }

        except requests.exceptions.RequestException as e:
            pass

    # Priority 2: Try yfinance
    yf_data = fetch_fundamentals_from_yfinance(ticker)
    if yf_data:
        return yf_data

    # Priority 3: Fall back to mock data
    return get_mock_fundamentals(ticker)


def extract_price_metrics(payload):
    """Pull short-term price cues out of a Finnhub /stock/metric response."""
    metric = (payload or {}).get("metric") or {}
    out = {}
    mapping = {
        "5DayPriceReturnDaily": "return_5d_pct",
        "13WeekPriceReturnDaily": "return_13w_pct",
        "26WeekPriceReturnDaily": "return_26w_pct",
        "beta": "beta",
        # Finnhub /quote has no 52-week fields; these fill the gap so the
        # pct_of_52_week_range cue can be computed
        "52WeekHigh": "52_week_high",
        "52WeekLow": "52_week_low",
    }
    for source, dest in mapping.items():
        value = metric.get(source)
        if isinstance(value, (int, float)):
            out[dest] = round(value, 2 if dest in ("beta", "52_week_high", "52_week_low") else 1)
    return out


def extract_fundamental_metrics(payload):
    """Pull long-term fundamental cues out of a Finnhub /stock/metric response."""
    metric = (payload or {}).get("metric") or {}
    out = {}
    mapping = {
        "revenueGrowth5Y": "revenue_growth_5y_pct",
        "epsGrowth5Y": "eps_growth_5y_pct",
        "netProfitMarginTTM": "net_margin_pct",
        "roeTTM": "roe_pct",
        "totalDebt/totalEquityQuarterly": "debt_to_equity",
        "dividendGrowthRate5Y": "dividend_growth_5y_pct",
    }
    for source, dest in mapping.items():
        value = metric.get(source)
        if isinstance(value, (int, float)):
            out[dest] = round(value, 2 if dest == "debt_to_equity" else 1)
    return out


def extract_days_until_earnings(payload, today):
    """Days until the next earnings report from a Finnhub earnings calendar response."""
    upcoming = []
    for event in (payload or {}).get("earningsCalendar") or []:
        try:
            event_date = datetime.fromisoformat(event.get("date", "")).date()
        except (ValueError, TypeError):
            continue
        if event_date >= today:
            upcoming.append(event_date)
    if not upcoming:
        return None
    return (min(upcoming) - today).days


# The long-term and short-term passes both read /stock/metric for the same
# tickers within one generation cycle; caching the payload briefly halves
# the spend against Finnhub's free-tier rate limit.
_METRIC_PAYLOAD_CACHE = {}  # ticker -> (fetched_at, payload)
METRIC_CACHE_MAX_AGE = timedelta(hours=1)

_PROFILE_CACHE: dict = {}  # ticker -> {market_cap, company_name}; reset each process lifetime


def _fetch_finnhub_profile(ticker: str) -> dict:
    """Fetch market cap and company name from Finnhub /stock/profile2.

    Cached in-process so parallel fundamentals fetches don't duplicate calls.
    Finnhub returns marketCapitalization in millions; we convert to dollars.
    """
    if ticker in _PROFILE_CACHE:
        return _PROFILE_CACHE[ticker]
    result: dict = {}
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
                result = {
                    "market_cap": int(mc * 1_000_000) if mc else 0,
                    "company_name": data.get("name") or "",
                }
        except Exception:
            pass
    _PROFILE_CACHE[ticker] = result
    return result


def fetch_metric_payload(ticker):
    """Finnhub /stock/metric payload for a ticker, or None on failure."""
    cached = _METRIC_PAYLOAD_CACHE.get(ticker)
    if cached and datetime.utcnow() - cached[0] < METRIC_CACHE_MAX_AGE:
        return cached[1]
    try:
        response = requests.get(
            f"{FINNHUB_BASE}/stock/metric",
            params={"symbol": ticker, "metric": "all", "token": FINNHUB_API_KEY},
            timeout=5,
        )
        if response.status_code == 200:
            payload = response.json()
            if len(_METRIC_PAYLOAD_CACHE) > 500:
                _METRIC_PAYLOAD_CACHE.clear()
            _METRIC_PAYLOAD_CACHE[ticker] = (datetime.utcnow(), payload)
            return payload
    except requests.exceptions.RequestException:
        pass
    return None


def fetch_long_term_metrics(ticker):
    """Fetch fundamental cues for the long-term pass (Finnhub free tier).

    Returns {} on any failure — the long-term pass degrades gracefully to
    valuation + dividend reasoning when these cues are unavailable.
    """
    if not FINNHUB_API_KEY:
        return {}
    return extract_fundamental_metrics(fetch_metric_payload(ticker))


def fetch_short_term_metrics(ticker):
    """Fetch momentum/catalyst cues for the short-term pass (Finnhub free tier).

    Returns {} on any failure — the short-term pass degrades gracefully to
    valuation + 52-week-range reasoning when these cues are unavailable.
    """
    if not FINNHUB_API_KEY:
        return {}

    out = {}
    out.update(extract_price_metrics(fetch_metric_payload(ticker)))

    try:
        today = datetime.utcnow().date()
        response = requests.get(
            f"{FINNHUB_BASE}/calendar/earnings",
            params={
                "symbol": ticker,
                "from": today.isoformat(),
                "to": (today + timedelta(days=45)).isoformat(),
                "token": FINNHUB_API_KEY,
            },
            timeout=5,
        )
        if response.status_code == 200:
            days = extract_days_until_earnings(response.json(), today)
            if days is not None:
                out["days_until_earnings"] = days
    except requests.exceptions.RequestException:
        pass

    return out


def get_mock_fundamentals(ticker):
    """Get mock fundamentals as fallback"""
    mock_data = {
        "AAPL": {"ticker": "AAPL", "company_name": "Apple Inc", "sector": "Technology", "market_cap": 3000000000000, "pe_ratio": 28.5, "dividend_yield": 0.004, "52_week_high": 220, "52_week_low": 165, "current_price": 205},
        "MSFT": {"ticker": "MSFT", "company_name": "Microsoft Corporation", "sector": "Technology", "market_cap": 3100000000000, "pe_ratio": 35.2, "dividend_yield": 0.007, "52_week_high": 465, "52_week_low": 310, "current_price": 425},
        "GOOGL": {"ticker": "GOOGL", "company_name": "Alphabet Inc", "sector": "Technology", "market_cap": 2000000000000, "pe_ratio": 25.1, "dividend_yield": 0.0, "52_week_high": 210, "52_week_low": 142, "current_price": 195},
        "NVDA": {"ticker": "NVDA", "company_name": "NVIDIA Corporation", "sector": "Technology", "market_cap": 1200000000000, "pe_ratio": 65.3, "dividend_yield": 0.001, "52_week_high": 155, "52_week_low": 68, "current_price": 142},
        "META": {"ticker": "META", "company_name": "Meta Platforms Inc", "sector": "Technology", "market_cap": 1300000000000, "pe_ratio": 32.5, "dividend_yield": 0.0, "52_week_high": 650, "52_week_low": 285, "current_price": 580},
        "JPM": {"ticker": "JPM", "company_name": "JPMorgan Chase & Co", "sector": "Financials", "market_cap": 500000000000, "pe_ratio": 12.3, "dividend_yield": 0.028, "52_week_high": 215, "52_week_low": 155, "current_price": 195},
        "BAC": {"ticker": "BAC", "company_name": "Bank of America Corp", "sector": "Financials", "market_cap": 350000000000, "pe_ratio": 11.2, "dividend_yield": 0.033, "52_week_high": 42, "52_week_low": 28, "current_price": 38},
        "JNJ": {"ticker": "JNJ", "company_name": "Johnson & Johnson", "sector": "Healthcare", "market_cap": 450000000000, "pe_ratio": 26.8, "dividend_yield": 0.029, "52_week_high": 162, "52_week_low": 124, "current_price": 155},
        "UNH": {"ticker": "UNH", "company_name": "UnitedHealth Group Inc", "sector": "Healthcare", "market_cap": 520000000000, "pe_ratio": 28.3, "dividend_yield": 0.013, "52_week_high": 665, "52_week_low": 460, "current_price": 625},
        "AMZN": {"ticker": "AMZN", "company_name": "Amazon.com Inc", "sector": "Consumer", "market_cap": 2000000000000, "pe_ratio": 48.2, "dividend_yield": 0.0, "52_week_high": 210, "52_week_low": 130, "current_price": 195},
        "WMT": {"ticker": "WMT", "company_name": "Walmart Inc", "sector": "Consumer", "market_cap": 450000000000, "pe_ratio": 32.5, "dividend_yield": 0.011, "52_week_high": 100, "52_week_low": 72, "current_price": 92},
        "VTI": {"ticker": "VTI", "company_name": "Vanguard Total Stock Market ETF", "sector": "ETF", "market_cap": None, "pe_ratio": None, "dividend_yield": 0.015, "52_week_high": 250, "52_week_low": 195, "current_price": 242},
        "VOO": {"ticker": "VOO", "company_name": "Vanguard S&P 500 ETF", "sector": "ETF", "market_cap": None, "pe_ratio": None, "dividend_yield": 0.015, "52_week_high": 545, "52_week_low": 420, "current_price": 520},
        "AGG": {"ticker": "AGG", "company_name": "iShares Core U.S. Aggregate Bond ETF", "sector": "ETF", "market_cap": None, "pe_ratio": None, "dividend_yield": 0.045, "52_week_high": 110, "52_week_low": 100, "current_price": 105},
    }
    # Return mock data or fallback with sector from TICKER_SECTOR_MAP.
    # Tagged so signal generation can avoid rating placeholder numbers.
    data = mock_data.get(ticker)
    if data:
        return {**data, "fundamentals_source": "mock"}
    return {
        "ticker": ticker,
        "company_name": COMPANY_NAMES.get(ticker, ticker),
        "sector": get_sector_for_stock(ticker, TICKER_SECTOR_MAP),
        "current_price": 100,
        "fundamentals_source": "mock",
    }


def fetch_macro_context(use_cache=True):
    """
    Fetch macro indicators from FRED API with caching
    Falls back to cache or defaults if API unavailable
    """
    # Try to use cached data if available
    if use_cache:
        cached_data, cached_at = load_macro_cache()
        if cached_data:
            print(f"Using cached macro data from {cached_at}")
            return cached_data

    # Default values
    macro_data = {
        "fed_rate": 5.25,  # As of June 2026
        "treasury_10y": 4.2,
        "vix": 18.5,
        "dxy": 102.5,
        "inflation": 3.2,
        "timestamp": datetime.now().isoformat()
    }

    if not FRED_API_KEY:
        print("FRED_API_KEY not set, using default macro values")
        return macro_data

    try:
        # Fetch recent FRED series
        fred_url = f"{FRED_BASE}/series/observations"

        # VIX via FRED
        vix_response = requests.get(
            fred_url,
            params={"series_id": "VIXCLS", "api_key": FRED_API_KEY, "limit": 1, "file_type": "json"},
            timeout=5
        )
        if vix_response.status_code == 200:
            obs = vix_response.json().get("observations", [])
            if obs:
                macro_data["vix"] = float(obs[-1].get("value", 18.5))

        # Treasury 10Y via FRED
        tnx_response = requests.get(
            fred_url,
            params={"series_id": "DGS10", "api_key": FRED_API_KEY, "limit": 1, "file_type": "json"},
            timeout=5
        )
        if tnx_response.status_code == 200:
            obs = tnx_response.json().get("observations", [])
            if obs:
                macro_data["treasury_10y"] = float(obs[-1].get("value", 4.2))

    except Exception as e:
        print(f"Error fetching macro from FRED (using cache/defaults): {e}")

    # Cache whatever we have (live data or defaults) so the next call uses cache
    save_macro_cache(macro_data)

    return macro_data


def refresh_macro_data():
    """Scheduled job to refresh macro data every hour"""
    print(f"[{datetime.now().isoformat()}] Starting macro data refresh...")
    try:
        macro_data = fetch_macro_context(use_cache=False)
        print(f"✅ Macro data refreshed: VIX={macro_data.get('vix')}, 10Y Treasury={macro_data.get('treasury_10y')}%")
        return True
    except Exception as e:
        print(f"❌ Macro data refresh failed: {e}")
        return False


# Groq's free tier is 100k tokens/day and each pass costs ~3.5k, so the
# refresh cadence is a token budget. Long-term picks are fundamentals-driven
# and shouldn't churn (daily is plenty); short-term reacts to momentum and
# macro (6h). The hourly stale-check below retries a failed pass within the
# hour instead of waiting out a full cycle.
TIMEFRAME_MAX_AGE_MINUTES = {
    "short_term": 360,    # 6h
    "long_term": 1440,    # 24h
}


def stale_timeframes(data=None, now=None):
    """Which timeframes need regeneration, judged per-signal from created_at.

    A timeframe with no stored real signals is stale by definition (this is
    what makes a failed pass retry on the next hourly check). Untagged
    legacy signals count as long_term.
    """
    if data is None:
        data = load_signals()
    now = now or datetime.utcnow()
    signals = data.get("signals", [])

    stale = []
    for timeframe, max_age in TIMEFRAME_MAX_AGE_MINUTES.items():
        newest = None
        for s in signals:
            if (s.get("timeframe") or "long_term") != timeframe:
                continue
            if s.get("source") == "mock":
                continue
            try:
                created = datetime.fromisoformat(s["created_at"])
            except (KeyError, ValueError, TypeError):
                continue
            if newest is None or created > newest:
                newest = created
        if newest is None or (now - newest) > timedelta(minutes=max_age):
            stale.append(timeframe)
    return stale


def generate_signals_if_stale():
    """
    Regenerate only the timeframes whose stored signals are too old.

    Run at startup and hourly: Railway's filesystem is ephemeral, so a cold
    start boots from the committed/seeded copy, and a rate-limited pass
    leaves its timeframe stale until a retry succeeds.
    """
    stale = stale_timeframes()
    if not stale:
        print("[Signals] All timeframes fresh; skipping regeneration")
        return False

    print(f"[Signals] Stale timeframes: {', '.join(stale)}; regenerating now")
    return auto_generate_signals(timeframes=stale)


def auto_generate_signals(timeframes=("long_term", "short_term")):
    """Regenerate the requested timeframe passes (scheduled hourly stale-check)"""
    print(f"[{datetime.now().isoformat()}] Starting auto-signal generation for: {', '.join(timeframes)}")
    try:
        # Fetch candidates once, then run the requested passes on them
        candidates = fetch_signal_candidates()
        long_term = generate_signals(count=10, candidates=candidates) if "long_term" in timeframes else []
        short_term = generate_short_term_signals(count=10, candidates=candidates) if "short_term" in timeframes else []

        # Never silently replace real LLM signals with mock fallback data —
        # stale-but-real beats fresh-but-fake (see docs/PRD.md, trust pillar).
        # Each timeframe pass succeeds or keeps its existing signals
        # independently: discarding a successful pass because the other one
        # hit a rate limit burns tokens for nothing and stalls recovery.
        real_long = [s for s in long_term if s.get("source") != "mock"]
        real_short = [s for s in short_term if s.get("source") != "mock"]
        existing = load_signals().get("signals", [])

        if not real_long and not real_short:
            if existing:
                print("⚠️ LLM unavailable; generated mock fallback signals — keeping existing real signals instead")
                return False
            mocks = long_term + short_term
            if not mocks:
                print("❌ Failed to generate signals")
                return False
            print("⚠️ LLM unavailable and no stored signals; saving mock fallback so the app isn't empty")
            save_signals({
                "signals": mocks,
                "generated_at": datetime.utcnow().isoformat(),
            })
            return True

        # Untagged legacy signals count as long_term
        signals = real_long or [
            s for s in existing
            if (s.get("timeframe") or "long_term") == "long_term" and s.get("source") != "mock"
        ]
        signals = signals + (real_short or [
            s for s in existing
            if s.get("timeframe") == "short_term" and s.get("source") != "mock"
        ])
        for timeframe, real in (("long_term", real_long), ("short_term", real_short)):
            if timeframe in timeframes and not real:
                print(f"⚠️ {timeframe} pass unavailable; kept existing signals for that timeframe")

        save_signals({
            "signals": signals,
            "generated_at": datetime.utcnow().isoformat(),
        })
        print(f"✅ Auto-generated and saved {len(signals)} signals with fresh market data")
        return True
    except Exception as e:
        print(f"❌ Signal auto-generation failed: {e}")
        return False


def get_macro_sentiment(macro_data):
    """Interpret macro data for signal generation context"""
    sentiment = []

    if macro_data.get("fed_rate"):
        rate = macro_data["fed_rate"]
        if rate > 5:
            sentiment.append(f"Fed Funds Rate is elevated at {rate}% (restrictive)")
        elif rate > 4:
            sentiment.append(f"Fed Funds Rate is moderately restrictive at {rate}%")
        else:
            sentiment.append(f"Fed Funds Rate is accommodative at {rate}%")

    if macro_data.get("vix"):
        vix = macro_data["vix"]
        if vix > 25:
            sentiment.append(f"VIX is elevated at {vix:.1f} (high volatility)")
        elif vix > 20:
            sentiment.append(f"VIX is moderate at {vix:.1f}")
        else:
            sentiment.append(f"VIX is calm at {vix:.1f} (low volatility, risk-on)")

    if macro_data.get("inflation"):
        infl = macro_data["inflation"]
        if infl > 3.5:
            sentiment.append(f"Inflation elevated at {infl}% (above Fed target)")
        elif infl > 2.5:
            sentiment.append(f"Inflation moderate at {infl}%")
        else:
            sentiment.append(f"Inflation low at {infl}%")

    return " ".join(sentiment) if sentiment else "Macro data available"


def call_groq(prompt):
    """Call Groq cloud LLM for signal generation"""
    try:
        client = get_groq_client()
        # 10 signals with the per-timeframe schema (label, catalyst/invalidation
        # or moat/what_to_watch) run well past 1024 tokens; a truncated answer
        # fails JSON parsing and silently drops the pass to mock fallback
        message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=3000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.choices[0].message.content
    except Exception as e:
        print(f"Error calling Groq: {e}")
        return None


def generate_realistic_mock_signals(candidates, count=5, timeframe="long_term"):
    """Generate realistic mock signals when Groq LLM is unavailable"""
    import random
    signals = []
    directions = ["buy", "hold", "avoid"]

    for i in range(min(count, len(candidates))):
        candidate = candidates[i]
        direction = random.choice(directions)
        confidence = random.randint(5, 9)

        # Generate realistic rationale based on fundamentals.
        # `or` fallbacks throughout: keys are often present but None
        # (e.g. Finnhub /quote has no 52-week fields), and a None here
        # crashes the f-string format specs below
        pe = candidate.get("pe_ratio") or 25
        dividend = candidate.get("dividend_yield") or 0
        price = candidate.get("current_price") or 100
        high = candidate.get("52_week_high") or price * 1.2

        company = candidate.get("company_name") or candidate.get("ticker", "This company")
        if direction == "buy":
            rationale = f"{company} trading at P/E of {pe:.1f}. Strong fundamentals with {dividend*100:.1f}% dividend yield. Current price of ${price:.2f} offers good entry point below 52-week high of ${high:.2f}."
        elif direction == "hold":
            rationale = f"{company} shows stable fundamentals at P/E {pe:.1f}. With dividend yield of {dividend*100:.1f}%, suitable for long-term holders. Hold at current levels, monitor macro environment."
        else:  # avoid
            rationale = f"{company} appears overvalued at P/E {pe:.1f} relative to sector average. Limited upside potential. Consider avoiding until better entry point emerges."

        signals.append({
            "id": f"{candidate['ticker']}_{datetime.now().isoformat()}",
            "ticker": candidate["ticker"],
            "direction": direction,
            "label": resolve_label(None, direction, timeframe),
            "confidence": confidence,
            "source": "mock",
            "rationale": rationale,
            "sector": candidate.get("sector", "Other"),
            "market_cap": candidate.get("market_cap"),
            "timeframe": timeframe,
            "created_at": datetime.now().isoformat(),
            "result": None,
            "accuracy_pct": None,
        })

    return signals


def score_company_quality(company_data):
    """
    Score a company for long-term investment quality (0-100)
    Looks at fundamentals, stability, and growth characteristics
    """
    score = 50  # Start at neutral

    pe_ratio = company_data.get("pe_ratio")
    dividend_yield = company_data.get("dividend_yield", 0)
    market_cap = company_data.get("market_cap", 0)

    # PE Ratio evaluation (lower is often better, but not too low)
    # Target range: 15-35 for quality companies
    if pe_ratio:
        if 15 <= pe_ratio <= 35:
            score += 15  # Reasonable valuation
        elif pe_ratio < 15:
            score += 10  # Potentially undervalued
        elif 35 < pe_ratio <= 50:
            score += 5   # Growth premium (acceptable)
        else:
            score -= 10  # Very expensive

    # Dividend yield (stability indicator)
    if dividend_yield and dividend_yield > 0:
        if dividend_yield >= 0.01:  # At least 1%
            score += 15  # Good income return
        if dividend_yield >= 0.02:
            score += 5   # Strong dividend
    else:
        score -= 5  # No dividend may indicate growth-stage (still okay)

    # Market cap (larger = more stable for long-term)
    if market_cap:
        if market_cap >= 100_000_000_000:  # $100B+
            score += 10  # Large-cap stability
        elif market_cap >= 10_000_000_000:  # $10B+
            score += 5   # Mid-cap decent

    return min(100, max(0, score))


def build_candidate_slate(candidates, top_n=15, bottom_n=10):
    """Mix the strongest and weakest quality-ranked candidates.

    Sending only top-quality stocks meant the LLM had nothing to rate
    "hold" or "avoid" — every signal came back "buy". The bottom slice
    gives it genuinely weak candidates to flag honestly.
    Expects candidates sorted by quality score, best first.
    """
    if len(candidates) <= top_n + bottom_n:
        return list(candidates)
    return candidates[:top_n] + candidates[-bottom_n:]


def build_short_term_slate(candidates, max_size=25):
    """Select short-term candidates on momentum grounds, not just quality.

    Mixes the biggest 13-week losers (recovery or avoid material), the
    strongest movers (momentum), and quality anchors — so the short-term
    pass rates a genuinely different set of stocks than the long-term one.
    Falls back to the quality slate when momentum data is unavailable.
    Expects candidates sorted by quality score, best first.
    """
    with_momentum = [c for c in candidates if isinstance(c.get("return_13w_pct"), (int, float))]
    if len(with_momentum) < 10:
        return build_candidate_slate(candidates)

    by_return = sorted(with_momentum, key=lambda c: c["return_13w_pct"])
    dips = by_return[:8]
    movers = by_return[-8:]
    quality_anchors = candidates[:9]

    slate, seen = [], set()
    for candidate in quality_anchors + dips + movers:
        ticker = candidate.get("ticker")
        if ticker and ticker not in seen:
            seen.add(ticker)
            slate.append(candidate)
    return slate[:max_size]


# Per-timeframe display vocabulary. `direction` (buy/hold/avoid) stays the
# machine contract — filters, accuracy scoring, and history all key off it —
# while `label` is presentation only. First entry per direction is the
# fallback when the LLM omits or invents a label.
TIMEFRAME_LABELS = {
    "short_term": {
        "buy": ("Momentum Buy", "Dip Buy"),
        "hold": ("Wait",),
        "avoid": ("Avoid", "Avoid Pre-Earnings"),
    },
    "long_term": {
        "buy": ("Accumulate",),
        "hold": ("Core Holding", "Hold"),
        "avoid": ("Avoid", "Trim"),
    },
}


def resolve_label(label, direction, timeframe):
    """Validate an LLM-chosen label against the timeframe vocabulary.

    Returns the canonical spelling on a (case-insensitive) match, the
    timeframe's fallback label for that direction otherwise, or None when
    the direction itself is unknown.
    """
    allowed = TIMEFRAME_LABELS.get(timeframe, {}).get(direction)
    if not allowed:
        return None
    if isinstance(label, str):
        normalized = label.strip().lower()
        for candidate in allowed:
            if normalized == candidate.lower():
                return candidate
    return allowed[0]


def clean_signal_text(value, max_len=220):
    """Whitespace-normalize and cap an LLM free-text field; None if empty."""
    if isinstance(value, str):
        text = " ".join(value.split())
        if text:
            return text[:max_len]
    return None


def parse_llm_signals(response_text):
    """Extract the JSON array of signals from an LLM response, or None."""
    import re
    try:
        match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(response_text)
    except json.JSONDecodeError:
        return None


def is_single_direction(signals):
    """True when every signal has the same direction (suspicious for 5+)."""
    directions = {s.get("direction") for s in signals}
    return len(signals) >= 5 and len(directions) == 1


RETRY_NUDGE = (
    "\n\nIMPORTANT: Your previous answer rated every stock the same way. "
    "That is not an honest assessment of a list that mixes strong and weak "
    "companies. Re-rate them: use hold and avoid where the data supports it."
)


def fetch_signal_candidates():
    """Discover stocks and fetch fundamentals, sorted by quality (best first).

    Shared by the long-term and short-term generation passes so candidates
    are only fetched once per cycle.
    """
    print("Discovering high-quality stocks...")
    signal_candidates = discover_stocks()

    # Fetch fundamentals in parallel for better performance
    max_candidates_to_fetch = 50
    candidates_to_fetch = signal_candidates[:max_candidates_to_fetch]
    print(f"Fetching fundamentals for {len(candidates_to_fetch)} of {len(signal_candidates)} discovered stocks (parallel)...")

    candidates = []
    # Use ThreadPoolExecutor to fetch fundamentals in parallel (max 5 concurrent requests)
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_ticker = {executor.submit(fetch_fundamentals, ticker): ticker for ticker in candidates_to_fetch}

        for future in as_completed(future_to_ticker):
            try:
                data = future.result()
                if data.get("current_price"):
                    # Score company for quality (long-term perspective)
                    data["quality_score"] = score_company_quality(data)
                    candidates.append(data)
            except Exception as e:
                ticker = future_to_ticker[future]
                print(f"Warning: Failed to fetch fundamentals for {ticker}: {e}")

    if candidates:
        print(f"📊 Fetched fundamentals for {len(candidates)} stocks (parallel)")

        # Don't rate placeholder numbers as if they were real market data —
        # mock-fundamentals candidates produced live avoid signals citing
        # "current price is 100". Keep them only when APIs are so degraded
        # that we'd otherwise have nothing to work with.
        real = [c for c in candidates if c.get("fundamentals_source") != "mock"]
        if len(real) >= 10:
            if len(real) < len(candidates):
                print(f"Excluding {len(candidates) - len(real)} candidates with placeholder fundamentals")
            # Filter out microcaps and tickers with no market cap data
            MIN_MARKET_CAP = 1_000_000_000  # $1B floor
            qualified = [c for c in real if c.get("market_cap", 0) >= MIN_MARKET_CAP]
            if len(qualified) >= 10:
                print(f"Market cap filter (>$1B): {len(real) - len(qualified)} removed, {len(qualified)} remain")
                real = qualified
            candidates = real

        candidates.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

    return candidates


# Internal bookkeeping fields confuse the LLM and leak into rationales
# ("quality score of 45") if sent along with the market data
INTERNAL_CANDIDATE_FIELDS = {"quality_score", "fundamentals_source"}


def candidate_prompt_fields(candidate):
    """Candidate dict with internal fields stripped, safe to show the LLM."""
    return {k: v for k, v in candidate.items() if k not in INTERNAL_CANDIDATE_FIELDS}


def generate_signals(count=10, candidates=None):
    """
    Generate long-term (5+ year) stock/ETF signals using Groq cloud LLM

    Args:
        count: Number of signals to generate
        candidates: pre-fetched candidate list (fetched fresh when None)

    Returns:
        List of signal dictionaries tagged timeframe="long_term"
    """

    if candidates is None:
        candidates = fetch_signal_candidates()
    if not candidates:
        print("No candidates with price data found")
        return []

    # Fetch macro context
    print("Fetching macro context...")
    macro_data = fetch_macro_context()
    macro_sentiment = get_macro_sentiment(macro_data)

    # Prepare data for Groq LLM - mix strong and weak candidates so the
    # LLM has genuine hold/avoid material, not just pre-vetted winners
    slate = build_candidate_slate(candidates)

    # Attach fundamental cues (revenue growth, margins, ROE, leverage) so the
    # long-term pass reasons over business quality, not just price and PE —
    # the short-term pass sees momentum data, this pass sees fundamentals.
    # 3 workers to stay friendly to Finnhub's free-tier rate limit.
    print(f"Fetching long-term fundamentals for {len(slate)} candidates...")
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_candidate = {
            executor.submit(fetch_long_term_metrics, c["ticker"]): c
            for c in slate
        }
        for future in as_completed(future_to_candidate):
            try:
                future_to_candidate[future].update(future.result())
            except Exception:
                pass

    candidates_str = json.dumps([candidate_prompt_fields(c) for c in slate], indent=2)
    print(f"📤 Sending {len(slate)} candidates (top + bottom of quality ranking) to Groq for signal generation")

    # Use Groq to generate signals with enhanced long-term focus
    print("Generating signals with Groq LLM (long-term quality focus)...")
    prompt = f"""You are helping regular people decide which companies to own for years — and which to skip. Rate stocks honestly and generate exactly {count} simple stock signals.

THE LIST BELOW MIXES STRONG AND WEAK COMPANIES (ranked by fundamental quality, best first). Not everything is a buy:
- buy = strong business at a reasonable price (good PE, dividends, stability)
- hold = good business but the price is stretched or growth is slowing — fine to keep, don't rush to add
- avoid = real problems in the data: very high PE, no dividend with weak growth, shrinking business

USE ONLY THE DATA PROVIDED. Key long-term cues (may be missing for some stocks — skip what isn't there):
- revenue_growth_5y_pct: how fast sales grew per year over 5 years. Above 8 = healthy grower; negative = shrinking business
- eps_growth_5y_pct: profit-per-share growth over 5 years — the engine of long-term returns
- net_margin_pct: how much of each sales dollar becomes profit. Above 15 = strong business; below 5 = thin cushion
- roe_pct: how well the company turns shareholder money into profit. Above 15 = quality; below 8 = mediocre
- debt_to_equity: above 2 = heavy debt load (risky if times get hard); below 0.5 = conservative
- dividend_growth_5y_pct: a dividend that GROWS every year is a sign of a durable business
- Very high PE (above 50) = paying a premium for hope; needs the growth numbers to back it up

MARKET CONDITIONS RIGHT NOW:
{macro_sentiment}

STOCKS TO RATE:
{candidates_str}

For each stock, give:
1. Stock symbol
2. What to do (buy, hold, or avoid)
3. A label that says it more precisely:
   - "Accumulate" (for buy): worth adding to steadily over time
   - "Core Holding" (for hold): great business, keep it — but the price is stretched, don't add now
   - "Hold" (for hold): fine business, nothing special at this price
   - "Trim" (for avoid): own less of it — numbers are deteriorating or the price ran way ahead
   - "Avoid" (for avoid): don't own it — real problems in the data
4. Confidence (1-10: 1=not sure, 10=very sure)
5. WHY in SIMPLE WORDS (1-2 sentences) citing a specific number from the data
6. moat: ONE short phrase saying what protects this business from competitors (or what fails to)
7. what_to_watch: ONE specific number from the data to check once a year to know the story is intact

LONG-TERM INVESTING TIPS TO USE:
- Strong and growing dividends = good for staying invested
- Low PE ratio = reasonable price; PE above 50 = paying a lot for hope
- Big market cap = stable/established company
- Market conditions matter, but matter LESS for long-term holds

WRITE LIKE YOU'RE TALKING TO A TEENAGER:
- Simple words only, no jargon
- Explain the business idea simply
- Be clear on what to do

Examples of GOOD honest ratings:
- Accumulate: "Walmart is a store everyone uses. Sales grew 5% a year for 5 years and the dividend keeps rising. The price is reasonable. This is the kind of company to buy and hold for years."
- Core Holding: "Costco is a great business with 12% yearly sales growth, but the price is high right now (PE of 50). If you own it, keep it. If you don't, wait for a better price."
- Avoid: "This company trades at a PE of 80 with profit margins of just 3%. You're paying a premium price for a thin-cushion business. Skip it until the numbers improve."

Return ONLY a JSON array with no other text:
[
  {{
    "ticker": "WMT",
    "direction": "buy",
    "label": "Accumulate",
    "confidence": 8,
    "rationale": "Walmart is the grocery store everyone uses. Sales grew 5% a year for 5 years and it pays a rising dividend. The price is fair right now. This is a hold-forever company that grows slowly but steadily.",
    "moat": "Biggest store network in America — rivals can't match its prices",
    "what_to_watch": "Revenue growth staying above 4% a year"
  }}
]

RULES:
- Exactly {count} signals
- Rate HONESTLY: aim for a mix — if the data shows weak companies, say avoid; do NOT call everything a buy
- An avoid rationale must cite the specific risk from the data
- label must be one of: Accumulate, Core Holding, Hold, Trim, Avoid — and must match the direction
- Confidence 5-10 (vary them)
- SIMPLE rationale - no fancy words
- LONG-TERM rationale (5+ year perspective)
- Pick from DIFFERENT industries"""

    response_text = call_groq(prompt)

    if not response_text:
        print("Groq unavailable, generating realistic mock signals...")
        return generate_realistic_mock_signals(candidates, count)

    signals = parse_llm_signals(response_text)
    if signals is None:
        print(f"Failed to parse Groq response: {response_text[:100]}")
        return generate_realistic_mock_signals(candidates, count)

    # All-one-direction output means the model ignored the honest-mix
    # instruction; nudge it once, keep the original answer if the retry
    # doesn't improve things
    if is_single_direction(signals):
        print("Warning: LLM rated every stock the same way; retrying once for an honest mix")
        retry_text = call_groq(prompt + RETRY_NUDGE)
        retry_signals = parse_llm_signals(retry_text) if retry_text else None
        if retry_signals and not is_single_direction(retry_signals):
            signals = retry_signals

    # Enhance signals with sector and market cap info
    enhanced_signals = []
    for signal in signals:
        ticker = signal.get("ticker")
        candidate = next((c for c in candidates if c["ticker"] == ticker), {})

        direction = signal.get("direction", "hold")
        signal_obj = {
            "id": f"{ticker}_{datetime.now().isoformat()}",
            "ticker": ticker,
            "direction": direction,
            "label": resolve_label(signal.get("label"), direction, "long_term"),
            "confidence": signal.get("confidence", 5),
            "rationale": signal.get("rationale", ""),
            "moat": clean_signal_text(signal.get("moat"), max_len=120),
            "what_to_watch": clean_signal_text(signal.get("what_to_watch"), max_len=120),
            "sector": candidate.get("sector", "Other"),
            "market_cap": candidate.get("market_cap", None),
            "pe_ratio": candidate.get("pe_ratio"),
            "dividend_yield": candidate.get("dividend_yield"),
            "revenue_growth_5y_pct": candidate.get("revenue_growth_5y_pct"),
            "net_margin_pct": candidate.get("net_margin_pct"),
            "timeframe": "long_term",
            "created_at": datetime.now().isoformat(),
            "result": None,
            "accuracy_pct": None,
        }
        enhanced_signals.append(signal_obj)

    return enhanced_signals


def generate_short_term_signals(count=10, candidates=None):
    """
    Generate short-term (1-3 month) signals with their own LLM pass.

    Reasons only over data we actually have — price vs 52-week range,
    valuation, and macro conditions — so rationales stay honest (no
    invented technical analysis).

    Returns:
        List of signal dictionaries tagged timeframe="short_term"
    """

    if candidates is None:
        candidates = fetch_signal_candidates()
    if not candidates:
        print("No candidates with price data found")
        return []

    macro_data = fetch_macro_context()
    macro_sentiment = get_macro_sentiment(macro_data)

    # Attach momentum/catalyst cues (13-week return, beta, earnings date) to
    # the strongest candidates, then select the slate on momentum grounds so
    # short-term rates a different set of stocks than long-term. Capped at 40
    # tickers and 3 workers to stay friendly to Finnhub's free-tier rate limit.
    metric_targets = candidates[:40]
    print(f"Fetching short-term metrics for {len(metric_targets)} candidates...")
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_candidate = {
            executor.submit(fetch_short_term_metrics, c["ticker"]): c
            for c in metric_targets
        }
        for future in as_completed(future_to_candidate):
            try:
                future_to_candidate[future].update(future.result())
            except Exception:
                pass

    slate = build_short_term_slate(candidates)
    # Derive a position-in-range cue so the model reasons from real numbers
    slate_for_prompt = []
    for c in slate:
        entry = candidate_prompt_fields(c)
        price, high, low = c.get("current_price"), c.get("52_week_high"), c.get("52_week_low")
        if price and high and low and high > low:
            entry["pct_of_52_week_range"] = round((price - low) / (high - low) * 100)
        slate_for_prompt.append(entry)
    candidates_str = json.dumps(slate_for_prompt, indent=2)
    print(f"📤 Sending {len(slate_for_prompt)} candidates to Groq for short-term signal generation")

    print("Generating signals with Groq LLM (short-term, 1-3 month focus)...")
    prompt = f"""You are helping regular people decide which stocks look good or risky over the NEXT 1-3 MONTHS. Rate stocks honestly and generate exactly {count} simple short-term signals.

THE LIST BELOW MIXES STRONG AND WEAK COMPANIES. Not everything is a buy:
- buy = reasonable price right now with room to recover or grow this quarter
- hold = fine company but nothing suggests the price moves soon, or it already ran up a lot
- avoid = stretched price or weak numbers that could fall in the next few months

USE ONLY THE DATA PROVIDED. Key short-term cues:
- return_13w_pct: price change over the last 3 months. Big negative = beaten down (bargain only if the business is solid); big positive = strong momentum (but check it isn't overextended)
- return_5d_pct: what the stock did this week — recent direction
- days_until_earnings: earnings report coming up = expect a price swing soon; risky for expensive stocks, an opportunity for cheap solid ones
- beta: above 1 = moves more than the market; in a shaky market, high-beta stocks fall harder
- pct_of_52_week_range: near 100 = at its yearly high (already ran up, less room); near 0 = at its yearly low (beaten down — bargain only if the business is solid)
- Very high PE = priced for perfection; bad news hits these hardest
- Market conditions below affect the next few months MORE than they affect long-term holds

MARKET CONDITIONS RIGHT NOW:
{macro_sentiment}

STOCKS TO RATE:
{candidates_str}

For each stock, give:
1. Stock symbol
2. What to do over the next 1-3 months (buy, hold, or avoid)
3. A label that says it more precisely:
   - "Momentum Buy" (for buy): riding strength — positive recent returns with room left
   - "Dip Buy" (for buy): solid company at a beaten-down price — recovery setup
   - "Wait" (for hold): fine company, but nothing suggests the price moves soon
   - "Avoid Pre-Earnings" (for avoid): expensive stock with earnings coming up — too risky right now
   - "Avoid" (for avoid): stretched price or weak numbers
4. Confidence (1-10: 1=not sure, 10=very sure)
5. WHY in SIMPLE WORDS (1-2 sentences) citing a specific number from the data
6. catalyst: ONE short phrase naming what could move the price soon, taken from the data (an earnings date, a big recent drop, strong momentum)
7. expected_window: how soon this call should play out, like "2-6 weeks" or "1-3 months"
8. invalidation: ONE simple sentence saying what would prove this call wrong (e.g. "If earnings disappoint this month" or "If it keeps falling past its yearly low")

WRITE LIKE YOU'RE TALKING TO A TEENAGER: simple words, no jargon, be clear on what to do.

Examples of GOOD honest short-term ratings:
- Dip Buy: "Bank of America is down 12% over the last 3 months but still earns well (PE of 11). Beaten-down solid bank - good setup for a recovery in the next few months."
- Wait: "Microsoft is a great company, but it's up 18% in 3 months and sits at 95% of its yearly range. It already ran up - wait for a dip before adding."
- Avoid Pre-Earnings: "This stock trades at a PE of 70 with earnings in 12 days. Priced for perfection - one disappointing report and it drops hard. Skip it until after earnings."

Return ONLY a JSON array with no other text:
[
  {{
    "ticker": "BAC",
    "direction": "buy",
    "label": "Dip Buy",
    "confidence": 7,
    "rationale": "Bank of America sits at just 30% of its yearly price range with a low PE of 11. Solid bank at a beaten-down price.",
    "catalyst": "Down 12% in 3 months while profits held up",
    "expected_window": "1-3 months",
    "invalidation": "If the price keeps sliding below its yearly low, the recovery idea is wrong."
  }}
]

RULES:
- Exactly {count} signals
- Rate HONESTLY: aim for a mix - do NOT call everything a buy
- Every rationale must cite a specific number from the data
- label must be one of: Momentum Buy, Dip Buy, Wait, Avoid Pre-Earnings, Avoid — and must match the direction
- catalyst and invalidation must come from the data provided, not invented news
- Confidence 5-10 (vary them)
- SHORT-TERM rationale (1-3 month perspective, not "hold forever")
- Pick from DIFFERENT industries"""

    response_text = call_groq(prompt)

    if not response_text:
        print("Groq unavailable, generating realistic mock signals...")
        return generate_realistic_mock_signals(candidates, count, timeframe="short_term")

    signals = parse_llm_signals(response_text)
    if signals is None:
        print(f"Failed to parse Groq response: {response_text[:100]}")
        return generate_realistic_mock_signals(candidates, count, timeframe="short_term")

    if is_single_direction(signals):
        print("Warning: LLM rated every stock the same way; retrying once for an honest mix")
        retry_text = call_groq(prompt + RETRY_NUDGE)
        retry_signals = parse_llm_signals(retry_text) if retry_text else None
        if retry_signals and not is_single_direction(retry_signals):
            signals = retry_signals

    enhanced_signals = []
    for signal in signals:
        ticker = signal.get("ticker")
        candidate = next((c for c in candidates if c["ticker"] == ticker), {})
        price, high, low = (
            candidate.get("current_price"), candidate.get("52_week_high"), candidate.get("52_week_low")
        )
        pct_of_range = None
        if price and high and low and high > low:
            pct_of_range = round((price - low) / (high - low) * 100)
        direction = signal.get("direction", "hold")
        enhanced_signals.append({
            "id": f"{ticker}_{datetime.now().isoformat()}",
            "ticker": ticker,
            "direction": direction,
            "label": resolve_label(signal.get("label"), direction, "short_term"),
            "confidence": signal.get("confidence", 5),
            "rationale": signal.get("rationale", ""),
            "catalyst": clean_signal_text(signal.get("catalyst"), max_len=120),
            "expected_window": clean_signal_text(signal.get("expected_window"), max_len=40),
            "invalidation": clean_signal_text(signal.get("invalidation")),
            "sector": candidate.get("sector", "Other"),
            "market_cap": candidate.get("market_cap", None),
            "return_13w_pct": candidate.get("return_13w_pct"),
            "days_until_earnings": candidate.get("days_until_earnings"),
            "pct_of_52_week_range": pct_of_range,
            "timeframe": "short_term",
            "created_at": datetime.now().isoformat(),
            "result": None,
            "accuracy_pct": None,
        })

    return enhanced_signals


def update_signal_accuracy():
    """
    Update signal accuracy by checking price movement 30 days later
    This should be run daily by a scheduled task
    """
    signals_data = load_signals()
    signals = signals_data.get("signals", [])

    for signal in signals:
        if signal.get("result") is None:
            created_at = datetime.fromisoformat(signal["created_at"])
            if datetime.now() - created_at > timedelta(days=30):
                signal["result"] = "pending"


def update_signal_accuracy(signal_id, result, accuracy):
    """Update a specific signal's accuracy"""
    signals_data = load_signals()
    for signal in signals_data.get("signals", []):
        if signal["id"] == signal_id:
            signal["result"] = result
            signal["accuracy_pct"] = accuracy
            save_signals(signals_data)
            return True
    return False
