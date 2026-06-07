"""
Macro Analysis Engine - integrates generate_dashboard.py logic with database
"""

import csv
import json
import os
from datetime import datetime
import yfinance as yf
from models import db, MacroSignal, FundImpact, FundForecast, AnalysisMetadata

# ── Config ────────────────────────────────────────────────────────────────────
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOLDINGS_FILE   = os.path.join(BASE_DIR, "holdings.csv")
RETIREMENT_FILE = os.path.join(BASE_DIR, "retirement_holdings.csv")

COST_BASIS = {
    "MSFT":  35788.51,
    "FXAIX": 70255.36,
    "VWO":   38041.75,
    "TMUS":  16401.19,
    "NVDA":  18449.10,
    "FBTC":  20449.96,
    "GLD":    9668.72,
}

# Macro signals (update manually each quarter)
MACRO_SIGNALS = {
    "fed_rate":  {"label": "Fed Funds Rate", "value": "3.5–3.75%", "signal": -1, "context": "Elevated — headwind for growth & valuation"},
    "treasury":  {"label": "10-yr Treasury", "value": "~4.1%",     "signal": -1, "context": "Elevated — pressure on equity multiples"},
    "inflation": {"label": "Core PCE",       "value": "~3.0%",     "signal": -1, "context": "Above 2% target — keeps rates high longer"},
    "pe_ratio":  {"label": "S&P 500 P/E",    "value": "~22x",      "signal": -1, "context": "Stretched vs 17x historical avg"},
    "dollar":    {"label": "DXY",            "value": "~103",      "signal":  0, "context": "Neutral — watch for breakout in either direction"},
    "vix":       {"label": "VIX",            "value": "~18",       "signal": +1, "context": "Below 20 — calm markets, risk appetite intact"},
    "gdp":       {"label": "GDP Growth",     "value": "+2.2%",     "signal": +1, "context": "Healthy — supports corporate earnings"},
    "gold":      {"label": "Gold Spot",      "value": "$3,300+",   "signal": +1, "context": "Strong — hedge demand, inflation premium"},
    "em_trend":  {"label": "EM Trend",       "value": "Neutral",   "signal":  0, "context": "Mixed — China/commodity cycle dependent"},
}

# Per-fund macro impact
INV_FUND_IMPACT = {
    "MSFT":  {"fed_rate": -1, "treasury": -1, "inflation": -1, "pe_ratio": -1, "dollar": -1, "vix":  0, "gdp": +1, "gold":  0, "em_trend":  0},
    "FXAIX": {"fed_rate": -1, "treasury": -1, "inflation": -1, "pe_ratio": -1, "dollar":  0, "vix": +1, "gdp": +1, "gold":  0, "em_trend":  0},
    "VWO":   {"fed_rate": -1, "treasury":  0, "inflation":  0, "pe_ratio":  0, "dollar": -1, "vix":  0, "gdp":  0, "gold": +1, "em_trend":  0},
    "TMUS":  {"fed_rate": -1, "treasury": -1, "inflation":  0, "pe_ratio":  0, "dollar":  0, "vix":  0, "gdp": +1, "gold":  0, "em_trend":  0},
    "NVDA":  {"fed_rate": -1, "treasury": -1, "inflation": -1, "pe_ratio": -1, "dollar": -1, "vix":  0, "gdp": +1, "gold":  0, "em_trend": +1},
    "FBTC":  {"fed_rate": -1, "treasury": -1, "inflation": +1, "pe_ratio":  0, "dollar": -1, "vix":  0, "gdp":  0, "gold": +1, "em_trend":  0},
    "GLD":   {"fed_rate": -1, "treasury": -1, "inflation": +1, "pe_ratio":  0, "dollar": -1, "vix":  0, "gdp":  0, "gold": +1, "em_trend":  0},
}

FUND_FORECAST = {
    "MSFT": {
        "name": "Microsoft",
        "outlook": "Bullish", "color": "#34d399", "horizon": "3–5 yr", "scenario": "+60–90%",
        "driver": "AI/cloud secular tailwind; Azure market share acceleration",
        "risk": "Premium valuation; regulatory scrutiny on AI",
    },
    "FXAIX": {
        "name": "Fidelity US Bond Index",
        "outlook": "Moderate", "color": "#60a5fa", "horizon": "3–5 yr", "scenario": "+35–55%",
        "driver": "Broad US earnings growth ~10% annually; diversified exposure",
        "risk": "Valuation compression if rates remain elevated",
    },
    "VWO": {
        "name": "Vanguard Emerging Markets",
        "outlook": "Neutral", "color": "#9ca3af", "horizon": "3–5 yr", "scenario": "+20–40%",
        "driver": "EM demographic dividend; cheaper valuations vs US equities",
        "risk": "Dollar strength; China slowdown; geopolitical risk",
    },
    "TMUS": {
        "name": "T-Mobile US",
        "outlook": "Moderate", "color": "#60a5fa", "horizon": "3–5 yr", "scenario": "+25–40%",
        "driver": "5G monetization; strong free cash flow generation",
        "risk": "Debt load sensitive to high-rate environment",
    },
    "NVDA": {
        "name": "NVIDIA",
        "outlook": "Very Bullish", "color": "#34d399", "horizon": "3–5 yr", "scenario": "+80–150%",
        "driver": "AI infrastructure supercycle; data center GPU dominance; CUDA moat",
        "risk": "Competition (AMD/custom chips); export restrictions; demand cycles",
    },
    "FBTC": {
        "name": "Fidelity Bitcoin ETF",
        "outlook": "Speculative", "color": "#a78bfa", "horizon": "3–5 yr", "scenario": "+50–200%",
        "driver": "Post-halving supply reduction; institutional ETF adoption growing",
        "risk": "Regulatory risk; no earnings floor; extreme volatility",
    },
    "GLD": {
        "name": "SPDR Gold Shares",
        "outlook": "Bullish", "color": "#fbbf24", "horizon": "3–5 yr", "scenario": "+25–45%",
        "driver": "Central bank buying; geopolitical risk premium; inflation persistence",
        "risk": "Rate normalization; dollar strength if economy re-accelerates",
    },
}

def load_holdings():
    """Load main holdings from CSV"""
    holdings = []
    try:
        with open(HOLDINGS_FILE) as f:
            for row in csv.DictReader(f):
                holdings.append({
                    "ticker": row["ticker"].strip(),
                    "shares": float(row["shares"]),
                    "asset_class": row["asset_class"].strip(),
                    "name": row["name"].strip(),
                })
    except FileNotFoundError:
        print(f"Warning: {HOLDINGS_FILE} not found")
    return holdings

def fetch_prices(holdings):
    """Fetch live prices for holdings"""
    if not holdings:
        return {}

    tickers = [h["ticker"] for h in holdings]
    results = {}
    try:
        raw = yf.download(tickers, period="2d", auto_adjust=True, progress=False)
        for h in holdings:
            t = h["ticker"]
            try:
                closes = raw["Close"][t].dropna() if len(tickers) > 1 else raw["Close"].dropna()
                p_today = float(closes.iloc[-1])
                p_prev = float(closes.iloc[-2]) if len(closes) >= 2 else p_today
                results[t] = {
                    "price": round(p_today, 2),
                    "day_change": round(p_today - p_prev, 2),
                    "day_change_pct": round((p_today - p_prev) / p_prev * 100, 2) if p_prev else 0,
                }
            except Exception as e:
                print(f"Warning: could not fetch {t}: {e}")
                results[t] = {"price": 0, "day_change": 0, "day_change_pct": 0}
    except Exception as e:
        print(f"Warning: price fetch failed: {e}")

    return results

def calculate_fund_impact(ticker, impact_map):
    """Calculate net macro impact score for a fund"""
    if ticker not in impact_map:
        return 0

    fund_impacts = impact_map[ticker]
    return sum(fund_impacts.values())

def run_analysis():
    """Run full macro analysis and store in database"""
    try:
        # Update metadata
        metadata = AnalysisMetadata.query.first()
        if not metadata:
            metadata = AnalysisMetadata()
            db.session.add(metadata)

        metadata.status = "running"
        metadata.last_updated = datetime.utcnow()
        db.session.commit()

        # Store macro signals
        MacroSignal.query.delete()
        for key, signal in MACRO_SIGNALS.items():
            ms = MacroSignal(
                signal_key=key,
                label=signal["label"],
                value=signal["value"],
                signal=signal["signal"],
                context=signal["context"]
            )
            db.session.add(ms)

        # Load holdings and fetch prices
        holdings = load_holdings()
        prices = fetch_prices(holdings)

        # Store fund impact scores
        FundImpact.query.delete()
        for ticker, impact_map in INV_FUND_IMPACT.items():
            net_score = calculate_fund_impact(ticker, INV_FUND_IMPACT)
            fi = FundImpact(
                ticker=ticker,
                impact_data=impact_map,
                net_score=net_score
            )
            db.session.add(fi)

        # Store fund forecasts with current prices
        FundForecast.query.delete()
        for ticker, forecast in FUND_FORECAST.items():
            price_data = prices.get(ticker, {})
            holding = next((h for h in holdings if h["ticker"] == ticker), None)

            ff = FundForecast(
                ticker=ticker,
                name=forecast["name"],
                outlook=forecast["outlook"],
                color=forecast["color"],
                horizon=forecast["horizon"],
                scenario=forecast["scenario"],
                driver=forecast["driver"],
                risk=forecast["risk"],
                current_price=price_data.get("price"),
                shares=holding["shares"] if holding else None,
                cost_basis=COST_BASIS.get(ticker)
            )
            db.session.add(ff)

        db.session.commit()

        metadata.status = "success"
        metadata.error_message = None
        db.session.commit()

        return True, "Analysis completed successfully"

    except Exception as e:
        print(f"Error running analysis: {e}")
        metadata = AnalysisMetadata.query.first()
        if metadata:
            metadata.status = "error"
            metadata.error_message = str(e)
            db.session.commit()
        return False, str(e)
