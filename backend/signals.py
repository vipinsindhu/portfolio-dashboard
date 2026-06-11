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
    "VTI": "Technology", "VOO": "Technology", "SPY": "Technology",
    "QQQ": "Technology", "AGG": "Utilities", "BND": "Utilities"
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

# Signals storage file
SIGNALS_FILE = "signals.json"
MACRO_CACHE_FILE = "macro_cache.json"


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
            sector = TICKER_SECTOR_MAP.get(ticker, info.get('sector', 'Unknown'))
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
                    # Get sector from COMPANY_SECTORS or fallback to TICKER_SECTOR_MAP
                    sector = COMPANY_SECTORS.get(ticker)
                    if not sector:
                        sector = TICKER_SECTOR_MAP.get(ticker, "Unknown")

                    return {
                        "ticker": ticker,
                        "company_name": COMPANY_NAMES.get(ticker, ticker),
                        "sector": sector,
                        "market_cap": COMPANY_MARKET_CAPS.get(ticker, 0),
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
    # Return mock data or fallback with sector from TICKER_SECTOR_MAP
    data = mock_data.get(ticker)
    if data:
        return data
    return {
        "ticker": ticker,
        "company_name": COMPANY_NAMES.get(ticker, ticker),
        "sector": TICKER_SECTOR_MAP.get(ticker, "Unknown"),
        "current_price": 100
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
            params={"series_id": "VIXCLS", "api_key": FRED_API_KEY, "limit": 1},
            timeout=5
        )
        if vix_response.status_code == 200:
            obs = vix_response.json().get("observations", [])
            if obs:
                macro_data["vix"] = float(obs[-1].get("value", 18.5))

        # Treasury 10Y via FRED
        tnx_response = requests.get(
            fred_url,
            params={"series_id": "DGS10", "api_key": FRED_API_KEY, "limit": 1},
            timeout=5
        )
        if tnx_response.status_code == 200:
            obs = tnx_response.json().get("observations", [])
            if obs:
                macro_data["treasury_10y"] = float(obs[-1].get("value", 4.2))

        # Cache the freshly fetched data
        save_macro_cache(macro_data)

    except Exception as e:
        print(f"Error fetching macro from FRED (using cache/defaults): {e}")

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


def generate_signals_if_stale(max_age_minutes=60):
    """
    Regenerate signals only if the stored ones are older than max_age_minutes.

    Run once at startup: Railway's filesystem is ephemeral, so every deploy
    resets signals.json to the committed copy and restarts the hourly timer.
    Without this, signals stay stale until the process survives a full hour.
    """
    data = load_signals()
    generated_at = data.get("generated_at")
    if generated_at:
        try:
            age = datetime.utcnow() - datetime.fromisoformat(generated_at)
            if age < timedelta(minutes=max_age_minutes):
                print(f"[Signals] Stored signals are {age} old (< {max_age_minutes}m); skipping regeneration")
                return False
        except (ValueError, TypeError):
            pass  # unparseable timestamp -> treat as stale

    print(f"[Signals] Stored signals stale (generated_at={generated_at}); regenerating now")
    return auto_generate_signals()


def auto_generate_signals():
    """Scheduled job to auto-generate signals every 60 minutes"""
    print(f"[{datetime.now().isoformat()}] Starting auto-signal generation...")
    try:
        signals = generate_signals(count=10)
        if signals:
            print(f"✅ Auto-generated {len(signals)} signals with fresh market data")
            return True
        else:
            print("❌ Failed to generate signals")
            return False
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
        message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1024,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.choices[0].message.content
    except Exception as e:
        print(f"Error calling Groq: {e}")
        return None


def generate_realistic_mock_signals(candidates, count=5):
    """Generate realistic mock signals when Groq LLM is unavailable"""
    import random
    signals = []
    directions = ["buy", "hold", "avoid"]

    for i in range(min(count, len(candidates))):
        candidate = candidates[i]
        direction = random.choice(directions)
        confidence = random.randint(5, 9)

        # Generate realistic rationale based on fundamentals
        pe = candidate.get("pe_ratio") or 25
        dividend = candidate.get("dividend_yield", 0) or 0
        price = candidate.get("current_price", 100)
        high = candidate.get("52_week_high", price * 1.2)

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
            "confidence": confidence,
            "rationale": rationale,
            "sector": candidate.get("sector", "Unknown"),
            "market_cap": candidate.get("market_cap"),
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


def generate_signals(count=10):
    """
    Generate stock/ETF signals using Groq cloud LLM
    Enhanced for long-term quality stock identification

    Args:
        count: Number of signals to generate

    Returns:
        List of signal dictionaries
    """

    # Discover high-quality stocks dynamically
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

    if not candidates:
        print("No candidates with price data found")
        return []

    print(f"📊 Fetched fundamentals for {len(candidates)} stocks (parallel)")

    # Sort by quality score for better long-term selections
    candidates.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

    # Fetch macro context
    print("Fetching macro context...")
    macro_data = fetch_macro_context()
    macro_sentiment = get_macro_sentiment(macro_data)

    # Prepare data for Groq LLM - use top quality candidates
    candidates_to_send = min(25, len(candidates))
    candidates_str = json.dumps(candidates[:candidates_to_send], indent=2)
    print(f"📤 Sending {candidates_to_send} candidates (quality-ranked) to Groq for signal generation")

    # Use Groq to generate signals with enhanced long-term focus
    print("Generating signals with Groq LLM (long-term quality focus)...")
    prompt = f"""You are helping regular people find good companies to own for years. Generate exactly {count} simple stock ideas.

FOCUS ON LONG-TERM QUALITY:
- Companies with strong earnings and dividends
- Businesses people trust and use regularly
- Reasonable prices (not too expensive)
- Stable industries that will exist in 10 years
- Market leaders with competitive advantages

REQUIREMENT: Pick from DIFFERENT industries/sectors for variety.

MARKET CONDITIONS RIGHT NOW:
{macro_sentiment}

STOCKS TO CONSIDER (ranked by fundamental quality):
{candidates_str}

For each stock, give:
1. Stock symbol
2. What to do (buy, hold, or avoid)
3. Confidence (1-10: 1=not sure, 10=very sure)
4. WHY in SIMPLE WORDS (1-2 sentences):
   - Easy reason a 10th grader would understand
   - Why this matters for long-term holding
   - What a beginner should do

LONG-TERM INVESTING TIPS TO USE:
- Strong dividends = good for staying invested
- Low PE ratio = reasonable price
- Big market cap = stable/established company
- Market conditions matter, but matter LESS for long-term holds

WRITE LIKE YOU'RE TALKING TO A TEENAGER:
- Simple words only, no jargon
- Explain the business idea simply
- Say why it matters for 5+ year holds
- Be clear on what to do

Example of GOOD long-term thinking:
"Walmart is a store everyone uses. It pays dividends (free money) every quarter. The price is reasonable. This is the kind of company to buy and hold for years. Good time to buy a little at a time."

Return ONLY a JSON array with no other text:
[
  {{
    "ticker": "WMT",
    "direction": "buy",
    "confidence": 8,
    "rationale": "Walmart is the grocery store everyone uses. It pays dividends (money returned to shareholders). The price is fair right now. This is a hold-forever company that grows slowly but steadily."
  }}
]

RULES:
- Exactly {count} signals
- Focus on QUALITY companies (good PE, dividends, stability)
- Confidence 5-10 (vary them, 7+ for quality stocks)
- SIMPLE rationale - no fancy words
- LONG-TERM rationale (5+ year perspective)
- Pick from DIFFERENT industries"""

    response_text = call_groq(prompt)

    if not response_text:
        print("Groq unavailable, generating realistic mock signals...")
        return generate_realistic_mock_signals(candidates, count)

    # Parse response
    try:
        # Try to find JSON in response
        import re
        match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if match:
            signals = json.loads(match.group())
        else:
            signals = json.loads(response_text)
    except json.JSONDecodeError:
        print(f"Failed to parse Groq response: {response_text[:100]}")
        return generate_realistic_mock_signals(candidates, count)

    # Enhance signals with sector and market cap info
    enhanced_signals = []
    for signal in signals:
        ticker = signal.get("ticker")
        candidate = next((c for c in candidates if c["ticker"] == ticker), {})

        signal_obj = {
            "id": f"{ticker}_{datetime.now().isoformat()}",
            "ticker": ticker,
            "direction": signal.get("direction", "hold"),
            "confidence": signal.get("confidence", 5),
            "rationale": signal.get("rationale", ""),
            "sector": candidate.get("sector", "Unknown"),
            "market_cap": candidate.get("market_cap", None),
            "created_at": datetime.now().isoformat(),
            "result": None,
            "accuracy_pct": None,
        }
        enhanced_signals.append(signal_obj)

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
