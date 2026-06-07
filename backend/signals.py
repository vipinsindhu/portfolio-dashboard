"""
Signal generation engine
Generates stock/ETF signals using Claude API + yfinance data
"""

import json
import os
from datetime import datetime, timedelta
import yfinance as yf
from anthropic import Anthropic

# Initialize Anthropic client
client = Anthropic()

# Signal candidates pool - stocks/ETFs to consider
SIGNAL_CANDIDATES = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "VTI", "VOO", "VWO", "AGG", "GLD",
    "TSLA", "META", "JPM", "WMT", "JNJ"
]

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
    Generate stock/ETF signals using Claude

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

    # Prepare data for Claude
    candidates_str = json.dumps(candidates[:10], indent=2)  # Top 10

    # Use Claude to generate signals
    print("Generating signals with Claude...")
    prompt = f"""You are a stock analyst. Based on the following fundamentals data,
generate {count} investment signals (buy/hold/avoid recommendations).

Candidates:
{candidates_str}

For each signal, provide:
1. Ticker symbol
2. Direction (buy, hold, or avoid)
3. Confidence score (1-10, where 10 is highest confidence)
4. 1-2 sentence rationale

Return a JSON array with this structure:
[
  {{
    "ticker": "AAPL",
    "direction": "buy",
    "confidence": 8,
    "rationale": "Strong fundamentals and positive market momentum."
  }}
]

Generate exactly {count} signals. Return ONLY the JSON array, no other text."""

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
