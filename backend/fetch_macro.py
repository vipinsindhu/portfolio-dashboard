"""
Fetch live macro data from yfinance and update macro_config.json
Runs daily to keep indicators current. Manual overrides supported via config file.
"""

import json
import os
from datetime import datetime
import yfinance as yf

CONFIG_FILE = "macro_config.json"

def fetch_vix():
    try:
        vix = yf.Ticker("^VIX").history(period="1d")["Close"].iloc[-1]
        return round(vix, 1)
    except Exception as e:
        print(f"Warning: could not fetch VIX: {e}")
        return None

def fetch_gold():
    try:
        gold = yf.Ticker("GC=F").history(period="1d")["Close"].iloc[-1]
        return round(gold, 2)
    except Exception as e:
        print(f"Warning: could not fetch gold: {e}")
        return None

def fetch_dollar_index():
    try:
        dxy = yf.Ticker("DXY").history(period="1d")["Close"].iloc[-1]
        return round(dxy, 2)
    except Exception as e:
        print(f"Warning: could not fetch DXY: {e}")
        return None

def fetch_treasury_yield():
    try:
        tnx = yf.Ticker("^TNX").history(period="1d")["Close"].iloc[-1]
        return round(tnx, 2)
    except Exception as e:
        print(f"Warning: could not fetch 10-yr Treasury: {e}")
        return None

def fetch_sp500_pe():
    try:
        spy = yf.Ticker("SPY")
        hist = spy.history(period="1d")
        info = spy.info
        pe = info.get("forwardPE", info.get("trailingPE"))
        if pe:
            return round(pe, 1)
        return None
    except Exception as e:
        print(f"Warning: could not fetch S&P 500 P/E: {e}")
        return None

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def main():
    config = load_config()

    print("Fetching live macro data...")

    # Fetch live values
    vix = fetch_vix()
    gold = fetch_gold()
    dxy = fetch_dollar_index()
    tnx = fetch_treasury_yield()
    pe = fetch_sp500_pe()

    # Update config with live data (keep manual overrides for Fed rate and inflation)
    if "macro_signals" not in config:
        config["macro_signals"] = {}

    signals = config["macro_signals"]

    # Update values from live data
    if vix is not None:
        signals["vix"] = {"value": f"~{vix}", "signal": 1 if vix < 20 else (-1 if vix > 30 else 0)}
        print(f"VIX: {vix}")

    if gold is not None:
        signals["gold"] = {"value": f"${gold:,.0f}", "signal": 1}  # Gold is always a hedge
        print(f"Gold: ${gold:,.2f}")

    if dxy is not None:
        signals["dollar"] = {"value": f"~{dxy}", "signal": 0}  # Neutral by default
        print(f"Dollar (DXY): {dxy}")

    if tnx is not None:
        signals["treasury"] = {"value": f"~{tnx}%", "signal": -1 if tnx > 4.0 else 0}
        print(f"10-yr Treasury: {tnx}%")

    if pe is not None:
        signals["pe_ratio"] = {"value": f"~{pe}x", "signal": -1 if pe > 20 else 0}
        print(f"S&P 500 P/E: {pe}x")

    # Keep Fed rate and inflation manual (they change on FOMC schedule, not daily)
    # If not already set, use defaults
    if "fed_rate" not in signals:
        signals["fed_rate"] = {
            "value": "3.5–3.75%",
            "signal": -1,
            "label": "Fed Funds Rate",
            "context": "Elevated — headwind for growth & valuation",
            "manual": True
        }

    if "inflation" not in signals:
        signals["inflation"] = {
            "value": "~3.0%",
            "signal": -1,
            "label": "Core PCE",
            "context": "Above 2% target — keeps rates high longer",
            "manual": True
        }

    if "gdp" not in signals:
        signals["gdp"] = {
            "value": "+2.2%",
            "signal": 1,
            "label": "GDP Growth",
            "context": "Healthy — supports corporate earnings"
        }

    if "em_trend" not in signals:
        signals["em_trend"] = {
            "value": "Neutral",
            "signal": 0,
            "label": "EM Trend",
            "context": "Mixed — China/commodity cycle dependent"
        }

    # Add labels and context to fetched data if missing
    if "vix" in signals and "label" not in signals["vix"]:
        signals["vix"]["label"] = "VIX"
        signals["vix"]["context"] = "Below 20 = calm markets, risk appetite intact"

    if "gold" in signals and "label" not in signals["gold"]:
        signals["gold"]["label"] = "Gold Spot"
        signals["gold"]["context"] = "Strong — hedge demand, inflation premium"

    if "dollar" in signals and "label" not in signals["dollar"]:
        signals["dollar"]["label"] = "DXY"
        signals["dollar"]["context"] = "Neutral — watch for breakout in either direction"

    if "treasury" in signals and "label" not in signals["treasury"]:
        signals["treasury"]["label"] = "10-yr Treasury"
        signals["treasury"]["context"] = "Elevated — pressure on equity multiples"

    if "pe_ratio" in signals and "label" not in signals["pe_ratio"]:
        signals["pe_ratio"]["label"] = "S&P 500 P/E"
        signals["pe_ratio"]["context"] = "Stretched vs 17x historical avg"

    config["macro_signals"] = signals
    config["last_updated"] = datetime.now().isoformat()

    save_config(config)
    print(f"\nConfig updated: {CONFIG_FILE}")
    print(f"Last updated: {config['last_updated']}")

if __name__ == "__main__":
    main()
