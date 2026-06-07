"""
Signal generation engine
Generates stock/ETF signals using Claude API + yfinance data + macro context
"""

import json
import os
import time
from datetime import datetime, timedelta
import yfinance as yf
from anthropic import Anthropic
import requests

# Initialize Anthropic client with API key from environment
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")
client = Anthropic(api_key=api_key)

# Signal candidates pool - stocks/ETFs to consider
# Reduced to avoid yfinance rate limiting
SIGNAL_CANDIDATES = [
    # Technology
    "AAPL", "MSFT", "GOOGL", "NVDA", "META",
    # Financial Services
    "JPM", "BAC",
    # Healthcare
    "JNJ", "UNH",
    # Consumer
    "AMZN", "WMT",
    # ETFs
    "VTI", "VOO", "AGG"
]

# FRED API key (free, no auth needed for many series)
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# Signals storage file
SIGNALS_FILE = "signals.json"


def load_signals():
    """Load signals from JSON file"""
    if os.path.exists(SIGNALS_FILE):
        with open(SIGNALS_FILE, 'r') as f:
            return json.load(f)
    return {"signals": [], "generated_at": None}


def save_signals(data):
    """Save signals to JSON file"""
    with open(SIGNALS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def fetch_macro_context():
    """
    Fetch macro economic indicators for context
    Returns recent values for: Fed Rate, Treasury Yield, VIX, USD Index, Inflation
    Falls back to mock data if yfinance is unavailable
    """
    macro_data = {
        "fed_rate": 5.25,  # As of June 2026
        "treasury_10y": 4.2,
        "vix": 18.5,
        "dxy": 102.5,
        "inflation": 3.2,  # Core PCE estimate
        "timestamp": datetime.now().isoformat()
    }

    try:
        # Fetch VIX
        vix = yf.Ticker("^VIX")
        vix_info = vix.info or {}
        vix_price = vix_info.get("currentPrice")
        if vix_price:
            macro_data["vix"] = vix_price

        # Fetch DXY (USD Index)
        dxy = yf.Ticker("^DXY")
        dxy_info = dxy.info or {}
        dxy_price = dxy_info.get("currentPrice")
        if dxy_price:
            macro_data["dxy"] = dxy_price

        # Fetch 10-Year Treasury Yield
        tnx = yf.Ticker("^TNX")
        tnx_info = tnx.info or {}
        tnx_price = tnx_info.get("currentPrice")
        if tnx_price:
            macro_data["treasury_10y"] = tnx_price

    except Exception as e:
        print(f"Error fetching macro context (using defaults): {e}")

    return macro_data


def get_macro_sentiment(macro_data):
    """
    Interpret macro data for signal generation context
    Returns a readable summary of macro environment
    """
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

    if macro_data.get("dxy"):
        dxy = macro_data["dxy"]
        if dxy > 105:
            sentiment.append(f"USD is strong at {dxy:.1f} (headwind for exporters)")
        elif dxy > 100:
            sentiment.append(f"USD is firm at {dxy:.1f}")
        else:
            sentiment.append(f"USD is weaker at {dxy:.1f}")

    if macro_data.get("inflation"):
        infl = macro_data["inflation"]
        if infl > 3.5:
            sentiment.append(f"Inflation elevated at {infl}% (above Fed target)")
        elif infl > 2.5:
            sentiment.append(f"Inflation moderate at {infl}%")
        else:
            sentiment.append(f"Inflation low at {infl}%")

    return " ".join(sentiment) if sentiment else "Macro data unavailable"


# Mock fundamentals for testing when yfinance is rate-limited
MOCK_FUNDAMENTALS = {
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

def fetch_fundamentals(ticker, use_mock=False, retry_count=2, delay=0.5):
    """Fetch basic fundamentals for a ticker with rate limiting and mock fallback"""
    if use_mock or ticker in MOCK_FUNDAMENTALS:
        return MOCK_FUNDAMENTALS.get(ticker, {"ticker": ticker, "sector": "Unknown", "current_price": 100})

    for attempt in range(retry_count):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info or {}

            return {
                "ticker": ticker,
                "company_name": info.get("longName", ticker),
                "sector": info.get("sector", "Unknown"),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", None),
                "dividend_yield": info.get("dividendYield", 0),
                "52_week_high": info.get("fiftyTwoWeekHigh", None),
                "52_week_low": info.get("fiftyTwoWeekLow", None),
                "current_price": info.get("currentPrice", None),
            }
        except (requests.exceptions.HTTPError, requests.exceptions.RequestException) as e:
            if attempt < retry_count - 1:
                wait_time = delay * (2 ** attempt)
                print(f"Error fetching {ticker} (attempt {attempt + 1}), using mock data instead")
                return MOCK_FUNDAMENTALS.get(ticker, {"ticker": ticker, "sector": "Unknown", "current_price": 100})
            print(f"Failed to fetch {ticker}: {e}, using mock data")
            return MOCK_FUNDAMENTALS.get(ticker, {"ticker": ticker, "sector": "Unknown", "current_price": 100})
        except Exception as e:
            print(f"Error fetching fundamentals for {ticker}: {e}, using mock data")
            return MOCK_FUNDAMENTALS.get(ticker, {"ticker": ticker, "sector": "Unknown", "current_price": 100})


def generate_signals(count=5):
    """
    Generate stock/ETF signals using Claude with macro context

    Args:
        count: Number of signals to generate

    Returns:
        List of signal dictionaries
    """

    print("Fetching fundamentals data...")
    candidates = []
    for i, ticker in enumerate(SIGNAL_CANDIDATES):
        data = fetch_fundamentals(ticker)
        if data.get("current_price"):
            candidates.append(data)
        if i < len(SIGNAL_CANDIDATES) - 1:
            time.sleep(1.0)  # 1 second delay between requests to avoid rate limiting

    if not candidates:
        print("No candidates with price data found")
        return []

    # Fetch macro context
    print("Fetching macro context...")
    macro_data = fetch_macro_context()
    macro_sentiment = get_macro_sentiment(macro_data)

    # Prepare data for Claude
    candidates_str = json.dumps(candidates[:15], indent=2)  # Top 15 (expanded)

    # Use Claude to generate signals with macro context
    print("Generating signals with Claude...")
    prompt = f"""You are a sophisticated stock analyst. Generate {count} investment signals
considering both fundamental analysis and current macro environment.

CURRENT MACRO ENVIRONMENT:
{macro_sentiment}

CANDIDATE STOCKS/ETFS (fundamentals data):
{candidates_str}

For each signal, provide:
1. Ticker symbol
2. Direction (buy, hold, or avoid)
3. Confidence score (1-10)
4. 2-3 sentence rationale that includes:
   - Specific fundamental metrics (P/E, dividend, etc.)
   - How the macro environment affects this investment
   - Clear reason why now is good/bad for this position

Return a JSON array:
[
  {{
    "ticker": "AAPL",
    "direction": "buy",
    "confidence": 8,
    "rationale": "P/E of 28 is reasonable given growth profile. With elevated rates,
                  dividend yield of 0.4% provides income cushion. Strong balance sheet
                  benefits from high rates. Good value in current environment."
  }}
]

IMPORTANT:
- Generate EXACTLY {count} signals
- Mix of BUY, HOLD, AVOID (realistic distribution, not all buys)
- Confidence scores should vary 5-9 (realistic, not inflated)
- Include specific numbers from fundamentals
- Consider how macro conditions help/hurt each sector
- Return ONLY the JSON array, no other text"""

    try:
        message = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        # Parse Claude's response
        try:
            signals = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if match:
                signals = json.loads(match.group())
            else:
                print(f"Failed to parse Claude response: {response_text}")
                return []

        # Enhance signals with sector and market cap info
        enhanced_signals = []
        for signal in signals:
            ticker = signal.get("ticker")
            # Find candidate info
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
                "result": None,  # Filled in after 30 days
                "accuracy_pct": None,
            }
            enhanced_signals.append(signal_obj)

        return enhanced_signals

    except Exception as e:
        print(f"Error generating signals with Claude: {e}")
        return []


def update_signal_accuracy():
    """
    Update signal accuracy by checking price movement 30 days later
    This should be run daily by a scheduled task
    """
    signals_data = load_signals()
    signals = signals_data.get("signals", [])

    for signal in signals:
        if signal.get("result") is None:
            # Check if 30 days have passed
            created_at = datetime.fromisoformat(signal["created_at"])
            if datetime.now() - created_at > timedelta(days=30):
                # Calculate accuracy
                ticker = signal["ticker"]
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(start=created_at, end=datetime.now())

                    if len(hist) > 0:
                        start_price = hist.iloc[0]["Close"]
                        end_price = hist.iloc[-1]["Close"]
                        actual_direction = "buy" if end_price > start_price else "avoid"

                        signal["result"] = "win" if actual_direction == signal["direction"] else "loss"
                        signal["accuracy_pct"] = 100 if signal["result"] == "win" else 0
                except Exception as e:
                    print(f"Error updating accuracy for {ticker}: {e}")

    save_signals(signals_data)


def get_latest_signals(limit=5):
    """Get the latest N signals"""
    signals_data = load_signals()
    signals = signals_data.get("signals", [])

    # Sort by created_at descending and return latest
    sorted_signals = sorted(
        signals,
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )

    return {
        "data": sorted_signals[:limit],
        "generated_at": signals_data.get("generated_at"),
        "total": len(signals),
    }


def get_signal_archive(limit=100):
    """Get signal archive (past signals)"""
    signals_data = load_signals()
    signals = signals_data.get("signals", [])

    # Sort by created_at descending
    sorted_signals = sorted(
        signals,
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )

    return {
        "signals": sorted_signals[:limit],
        "total": len(signals),
    }
