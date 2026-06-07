"""
Signal generation engine
Generates stock/ETF signals using Claude API + yfinance data + macro context
"""

import json
import os
from datetime import datetime, timedelta
import yfinance as yf
from anthropic import Anthropic
import requests

# Initialize Anthropic client
client = Anthropic()

# Signal candidates pool - stocks/ETFs to consider (expanded)
SIGNAL_CANDIDATES = [
    # Technology
    "AAPL", "MSFT", "GOOGL", "NVDA", "META",
    # Financial Services
    "JPM", "BAC", "GS", "BLK",
    # Healthcare
    "JNJ", "UNH", "PFE",
    # Consumer
    "AMZN", "WMT", "HD", "MCD",
    # Energy
    "XOM", "CVX",
    # Real Estate
    "SPG", "PLD",
    # ETFs
    "VTI", "VOO", "VWO", "AGG", "BND", "GLD"
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
    """
    macro_data = {
        "fed_rate": None,
        "treasury_10y": None,
        "vix": None,
        "dxy": None,
        "inflation": None,
        "timestamp": datetime.now().isoformat()
    }

    try:
        # Fetch VIX
        vix = yf.Ticker("^VIX")
        vix_info = vix.info or {}
        macro_data["vix"] = vix_info.get("currentPrice", None)

        # Fetch DXY (USD Index)
        dxy = yf.Ticker("^DXY")
        dxy_info = dxy.info or {}
        macro_data["dxy"] = dxy_info.get("currentPrice", None)

        # Fetch 10-Year Treasury Yield
        tnx = yf.Ticker("^TNX")
        tnx_info = tnx.info or {}
        macro_data["treasury_10y"] = tnx_info.get("currentPrice", None)

        # Note: Fed Rate and Inflation would normally come from FRED API
        # For now, use reasonable estimates based on recent data
        macro_data["fed_rate"] = 5.25  # As of June 2026
        macro_data["inflation"] = 3.2  # Core PCE estimate

    except Exception as e:
        print(f"Error fetching macro context: {e}")

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


def fetch_fundamentals(ticker):
    """Fetch basic fundamentals for a ticker"""
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
    except Exception as e:
        print(f"Error fetching fundamentals for {ticker}: {e}")
        return {"ticker": ticker, "sector": "Unknown"}


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
    for ticker in SIGNAL_CANDIDATES:
        data = fetch_fundamentals(ticker)
        if data.get("current_price"):
            candidates.append(data)

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
