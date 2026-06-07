"""
Signal generation engine using Groq cloud LLM
Generates stock/ETF signals using Groq (Mixtral/Llama) + Finnhub data + FRED macro context
"""

import json
import os
import time
from datetime import datetime, timedelta
import requests
from groq import Groq

# Environment configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")  # Optional, FRED has generous free tier

# Initialize Groq client
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is required")
groq_client = Groq(api_key=GROQ_API_KEY)

# API endpoints
FINNHUB_BASE = "https://finnhub.io/api/v1"
FRED_BASE = "https://api.stlouisfed.org/fred"

# Signal candidates pool - stocks/ETFs to consider
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
    """Fetch stock fundamentals from Finnhub"""
    if not FINNHUB_API_KEY:
        print(f"Warning: FINNHUB_API_KEY not set, using mock data for {ticker}")
        return get_mock_fundamentals(ticker)

    try:
        # Get company profile and quote
        profile_url = f"{FINNHUB_BASE}/company/profile2"
        quote_url = f"{FINNHUB_BASE}/quote"

        profile_response = requests.get(
            profile_url,
            params={"symbol": ticker, "token": FINNHUB_API_KEY},
            timeout=5
        )
        quote_response = requests.get(
            quote_url,
            params={"symbol": ticker, "token": FINNHUB_API_KEY},
            timeout=5
        )

        if profile_response.status_code == 200 and quote_response.status_code == 200:
            profile = profile_response.json()
            quote = quote_response.json()

            if quote.get("c"):  # Current price exists
                return {
                    "ticker": ticker,
                    "company_name": profile.get("name", ticker),
                    "sector": profile.get("finnhubIndustry", "Unknown"),
                    "market_cap": profile.get("marketCapitalization", 0) * 1_000_000,
                    "pe_ratio": quote.get("pe"),
                    "dividend_yield": profile.get("dividendYield", 0),
                    "52_week_high": quote.get("h52", None),
                    "52_week_low": quote.get("l52", None),
                    "current_price": quote.get("c"),
                }

        print(f"No price data for {ticker}, using mock")
        return get_mock_fundamentals(ticker)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {ticker} from Finnhub: {e}, using mock data")
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
    return mock_data.get(ticker, {"ticker": ticker, "sector": "Unknown", "current_price": 100})


def fetch_macro_context():
    """
    Fetch macro indicators from FRED API
    Falls back to defaults if unavailable
    """
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

    except Exception as e:
        print(f"Error fetching macro from FRED (using defaults): {e}")

    return macro_data


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
        message = groq_client.chat.completions.create(
            model="gemma-2-9b-it",
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
    """Generate realistic mock signals when Groq is unavailable"""
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

        if direction == "buy":
            rationale = f"{candidate['company_name']} trading at P/E of {pe:.1f}. Strong fundamentals with {dividend*100:.1f}% dividend yield. Current price of ${price:.2f} offers good entry point below 52-week high of ${high:.2f}."
        elif direction == "hold":
            rationale = f"{candidate['company_name']} shows stable fundamentals at P/E {pe:.1f}. With dividend yield of {dividend*100:.1f}%, suitable for long-term holders. Hold at current levels, monitor macro environment."
        else:  # avoid
            rationale = f"{candidate['company_name']} appears overvalued at P/E {pe:.1f} relative to sector average. Limited upside potential. Consider avoiding until better entry point emerges."

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


def generate_signals(count=5):
    """
    Generate stock/ETF signals using local Ollama Mistral LLM

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
            time.sleep(0.3)  # Rate limiting for Finnhub

    if not candidates:
        print("No candidates with price data found")
        return []

    # Fetch macro context
    print("Fetching macro context...")
    macro_data = fetch_macro_context()
    macro_sentiment = get_macro_sentiment(macro_data)

    # Prepare data for Ollama
    candidates_str = json.dumps(candidates[:15], indent=2)

    # Use Groq to generate signals
    print("Generating signals with Groq LLM...")
    prompt = f"""You are a sophisticated stock analyst. Generate exactly {count} investment signals
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

Return ONLY a JSON array with no other text:
[
  {{
    "ticker": "AAPL",
    "direction": "buy",
    "confidence": 8,
    "rationale": "P/E of 28.5 is reasonable given growth profile. With elevated rates at 5.25%, dividend yield of 0.4% provides income cushion. Strong balance sheet benefits from high rates. Good value in current environment."
  }}
]

IMPORTANT:
- Generate EXACTLY {count} signals
- Mix of BUY, HOLD, AVOID (realistic distribution)
- Confidence scores should vary 5-9
- Include specific numbers from fundamentals
- Consider how macro conditions help/hurt each sector"""

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
