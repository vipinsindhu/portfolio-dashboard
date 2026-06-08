"""
Portfolio analysis engine
Detects pitfalls, calculates risk metrics, compares against benchmarks
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
import os
import requests
from portfolio import Portfolio, Holding, get_sector_weights, get_top_n_concentration
from educational import LESSONS


# Sector cache file for dynamic lookups
SECTOR_CACHE_FILE = "sector_cache.json"
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
FINNHUB_BASE = "https://finnhub.io/api/v1"


def load_sector_cache() -> Dict[str, str]:
    """Load cached sector mappings from file"""
    if os.path.exists(SECTOR_CACHE_FILE):
        try:
            with open(SECTOR_CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sector cache: {e}")
    return {}


def save_sector_cache(cache: Dict[str, str]):
    """Save sector cache to file"""
    try:
        with open(SECTOR_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"Error saving sector cache: {e}")


def fetch_sector_from_finnhub(symbol: str) -> Optional[str]:
    """Fetch sector from Finnhub API for unknown stocks"""
    if not FINNHUB_API_KEY:
        return None

    try:
        # Try company profile endpoint
        profile_url = f"{FINNHUB_BASE}/stock/profile2"
        response = requests.get(
            profile_url,
            params={"symbol": symbol, "token": FINNHUB_API_KEY},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            sector = data.get("finnhubIndustry")
            if sector:
                # Normalize sector name
                sector = sector.title() if isinstance(sector, str) else None
                print(f"[Sector Cache] Found sector for {symbol}: {sector}")
                return sector
    except Exception as e:
        print(f"[Sector Cache] Error fetching {symbol} from Finnhub: {e}")

    return None


def get_sector_for_stock(symbol: str, static_map: Dict[str, str]) -> str:
    """
    Hybrid sector lookup:
    1. Check static map (fast, zero cost)
    2. Check cache (fast, no API call)
    3. Fetch from Finnhub (slow, API call, cached for future)
    4. Default to "Other"
    """
    # Step 1: Check static map
    if symbol in static_map:
        return static_map[symbol]

    # Step 2: Load and check cache
    cache = load_sector_cache()
    if symbol in cache:
        return cache[symbol]

    # Step 3: Try Finnhub (only for new stocks)
    print(f"[Sector Cache] Looking up {symbol} from Finnhub...")
    sector = fetch_sector_from_finnhub(symbol)

    if sector:
        # Cache the result
        cache[symbol] = sector
        save_sector_cache(cache)
        return sector

    # Step 4: Default to "Other"
    print(f"[Sector Cache] No sector found for {symbol}, defaulting to 'Other'")
    return "Other"


@dataclass
class Pitfall:
    """Detected portfolio pitfall"""
    lesson_id: str
    lesson_title: str
    severity: str  # "critical", "warning", "info"
    metric_name: str
    current_value: float
    threshold: float
    message: str
    recommendation: str
    affected_holdings: List[str]


@dataclass
class PortfolioAnalysis:
    """Complete portfolio analysis"""
    portfolio: Portfolio
    pitfalls: List[Pitfall]
    risk_metrics: Dict[str, float]
    sector_allocation: Dict[str, float]
    concentration_metrics: Dict[str, float]
    recommendations: List[str]
    summary: str


# Sector mapping for analysis
SECTOR_MAP = {
    # Technology
    "AAPL": "Technology",
    "MSFT": "Technology",
    "GOOGL": "Technology",
    "GOOG": "Technology",
    "NVDA": "Technology",
    "META": "Technology",
    "TSLA": "Technology",
    "AMD": "Technology",
    "INTC": "Technology",
    "QCOM": "Technology",
    "CSCO": "Technology",
    "CRM": "Technology",
    "ADBE": "Technology",
    "NFLX": "Technology",
    "AVGO": "Technology",
    "PYPL": "Technology",
    "ASML": "Technology",
    "UBER": "Technology",
    "SNOW": "Technology",
    "COIN": "Technology",

    # Financials
    "JPM": "Financials",
    "BAC": "Financials",
    "WFC": "Financials",
    "GS": "Financials",
    "MS": "Financials",
    "BLK": "Financials",
    "AXP": "Financials",
    "C": "Financials",
    "USB": "Financials",
    "PNC": "Financials",
    "TD": "Financials",
    "BK": "Financials",
    "ICE": "Financials",
    "CME": "Financials",

    # Healthcare
    "JNJ": "Healthcare",
    "UNH": "Healthcare",
    "PFE": "Healthcare",
    "ABBV": "Healthcare",
    "MRK": "Healthcare",
    "LLY": "Healthcare",
    "AMGN": "Healthcare",
    "GILD": "Healthcare",
    "REGN": "Healthcare",
    "BIIB": "Healthcare",
    "CVS": "Healthcare",
    "TMO": "Healthcare",
    "DHR": "Healthcare",
    "EW": "Healthcare",
    "VRTX": "Healthcare",

    # Consumer / Retail
    "AMZN": "Consumer",
    "WMT": "Consumer",
    "MCD": "Consumer",
    "COST": "Consumer",
    "TJX": "Consumer",
    "HD": "Consumer",
    "LOW": "Consumer",
    "NKE": "Consumer",
    "SBUX": "Consumer",
    "KO": "Consumer",
    "PEP": "Consumer",
    "MO": "Consumer",
    "PM": "Consumer",
    "GE": "Consumer",
    "DIS": "Consumer",
    "NCLH": "Consumer",
    "CCL": "Consumer",

    # Industrials
    "BA": "Industrials",
    "CAT": "Industrials",
    "HON": "Industrials",
    "MMM": "Industrials",
    "UTX": "Industrials",
    "RTX": "Industrials",
    "LMT": "Industrials",
    "NOC": "Industrials",
    "WM": "Industrials",
    "CSX": "Industrials",
    "NSC": "Industrials",
    "UNP": "Industrials",
    "KSU": "Industrials",

    # Energy
    "XOM": "Energy",
    "CVX": "Energy",
    "COP": "Energy",
    "SLB": "Energy",
    "EOG": "Energy",
    "MPC": "Energy",
    "PSX": "Energy",
    "OXY": "Energy",
    "MUR": "Energy",

    # Utilities
    "NEE": "Utilities",
    "DUK": "Utilities",
    "SO": "Utilities",
    "EXC": "Utilities",
    "D": "Utilities",
    "AEP": "Utilities",
    "XEL": "Utilities",
    "PEG": "Utilities",
    "ED": "Utilities",
    "WEC": "Utilities",

    # Materials
    "LIN": "Materials",
    "APD": "Materials",
    "FCX": "Materials",
    "NEM": "Materials",
    "SCCO": "Materials",

    # Real Estate / REIT
    "PSA": "Diversified",
    "PLD": "Diversified",
    "EQIX": "Diversified",
    "DLR": "Diversified",
    "ARE": "Diversified",

    # Index Funds / Diversified / ETFs
    "VTI": "Diversified",
    "VOO": "Diversified",
    "SPY": "Diversified",
    "VTSAX": "Diversified",
    "SPLG": "Diversified",
    "IVV": "Diversified",
    "SCHB": "Diversified",
    "VFIAX": "Diversified",
    "FSKAX": "Diversified",
    "FXAIX": "Diversified",
    "SCHX": "Diversified",
    "SCHF": "Diversified",
    "SWTSX": "Diversified",
    "VTSXF": "Diversified",
    "IJH": "Diversified",
    "IJR": "Diversified",
    "SCHD": "Diversified",
    "VXUS": "Diversified",
    "VTIAX": "Diversified",
    "VWO": "Diversified",
    "VTIAX": "Diversified",
    "IEMG": "Diversified",
    "EEM": "Diversified",

    # Bonds / Fixed Income
    "AGG": "Bonds",
    "BND": "Bonds",
    "VBTLX": "Bonds",
    "BLV": "Bonds",
    "VCIT": "Bonds",
    "VGIT": "Bonds",
    "VWOB": "Bonds",
    "LQD": "Bonds",
    "HYG": "Bonds",
    "TLT": "Bonds",
    "FBNDX": "Bonds",
    "VBTIX": "Bonds",
    "SBTIX": "Bonds",
    "VBTX": "Bonds",

    # Commodities / Precious Metals
    "GLD": "Commodities",
    "SLV": "Commodities",
    "DBC": "Commodities",
    "USO": "Commodities",
    "DBB": "Commodities",

    # Cryptocurrency / Digital Assets
    "FBTC": "Cryptocurrencies",
    "IBIT": "Cryptocurrencies",
    "GBTC": "Cryptocurrencies",
    "ETHE": "Cryptocurrencies",
}

# Target sector allocation ranges
TARGET_ALLOCATION = {
    "Technology": {"min": 0.20, "max": 0.30, "ideal": 0.25},
    "Financials": {"min": 0.12, "max": 0.20, "ideal": 0.16},
    "Healthcare": {"min": 0.12, "max": 0.20, "ideal": 0.16},
    "Consumer": {"min": 0.08, "max": 0.15, "ideal": 0.12},
    "Industrials": {"min": 0.05, "max": 0.12, "ideal": 0.08},
    "Energy": {"min": 0.03, "max": 0.10, "ideal": 0.05},
    "Utilities": {"min": 0.03, "max": 0.10, "ideal": 0.05},
    "Materials": {"min": 0.02, "max": 0.08, "ideal": 0.04},
    "Diversified": {"min": 0.05, "max": 0.30, "ideal": 0.15},
    "Bonds": {"min": 0.10, "max": 0.30, "ideal": 0.20},
    "Commodities": {"min": 0.00, "max": 0.10, "ideal": 0.05},
    "Cryptocurrencies": {"min": 0.00, "max": 0.05, "ideal": 0.02},
    "Other": {"min": 0.00, "max": 0.05, "ideal": 0.00},  # Should minimize unknown stocks
}


def get_hybrid_sector_weights(portfolio: Portfolio, static_sector_map: Dict[str, str]) -> Dict[str, float]:
    """
    Calculate sector weights using hybrid lookup:
    1. Static map for known stocks
    2. Cache for previously looked up stocks
    3. Finnhub for new unknown stocks
    4. "Other" as fallback
    """
    sector_values = {}

    for holding in portfolio.holdings:
        # Use hybrid lookup for each stock
        sector = get_sector_for_stock(holding.symbol, static_sector_map)

        if sector not in sector_values:
            sector_values[sector] = 0
        sector_values[sector] += holding.current_value

    total = sum(sector_values.values())
    return {
        sector: (value / total) if total > 0 else 0
        for sector, value in sector_values.items()
    }


def get_enhanced_sector_analysis(portfolio: Portfolio, sector_map: Dict) -> Dict:
    """Get detailed sector allocation analysis with recommendations"""
    # Use hybrid sector weights instead of static-only
    sector_weights = get_hybrid_sector_weights(portfolio, sector_map)
    enhanced_data = {}

    for sector, weight in sector_weights.items():
        target = TARGET_ALLOCATION.get(sector, {"min": 0, "max": 1, "ideal": 0.5})
        min_target = target["min"]
        max_target = target["max"]
        ideal = target["ideal"]

        # Determine health status
        if weight < min_target * 0.8:  # Significantly underweight
            status = "underweight"
            recommendation = f"Consider adding {sector} holdings (current: {weight:.1%}, target: {ideal:.0%})"
        elif weight > max_target * 1.2:  # Significantly overweight
            status = "overweight"
            recommendation = f"Reduce {sector} concentration (current: {weight:.1%}, target: {ideal:.0%})"
        elif min_target <= weight <= max_target:  # Within range
            status = "optimal"
            recommendation = f"{sector} allocation is well-balanced"
        else:
            status = "caution"
            recommendation = f"Monitor {sector} allocation (current: {weight:.1%}, target: {ideal:.0%})"

        gap = ideal - weight

        enhanced_data[sector] = {
            "current": weight,
            "target": ideal,
            "min": min_target,
            "max": max_target,
            "gap": gap,
            "status": status,
            "recommendation": recommendation
        }

    return enhanced_data


def analyze_portfolio(portfolio: Portfolio) -> PortfolioAnalysis:
    """Run complete portfolio analysis"""

    # Detect pitfalls
    pitfalls = detect_all_pitfalls(portfolio)

    # Calculate metrics
    risk_metrics = calculate_risk_metrics(portfolio)
    sector_allocation = get_enhanced_sector_analysis(portfolio, SECTOR_MAP)
    concentration_metrics = calculate_concentration_metrics(portfolio)

    # Generate recommendations
    recommendations = generate_recommendations(pitfalls, portfolio)

    # Create summary
    summary = create_summary(pitfalls, risk_metrics)

    return PortfolioAnalysis(
        portfolio=portfolio,
        pitfalls=pitfalls,
        risk_metrics=risk_metrics,
        sector_allocation=sector_allocation,
        concentration_metrics=concentration_metrics,
        recommendations=recommendations,
        summary=summary
    )


def detect_all_pitfalls(portfolio: Portfolio) -> List[Pitfall]:
    """Detect all pitfalls in portfolio"""
    pitfalls = []

    # Get sector allocation using hybrid lookup
    sector_allocation = get_hybrid_sector_weights(portfolio, SECTOR_MAP)

    # Check each pitfall lesson
    for lesson in LESSONS:
        metric = lesson.get("metric")

        if metric == "position_weight":
            pitfalls.extend(detect_overconcentration(portfolio, lesson))

        elif metric == "sector_concentration":
            pitfalls.extend(detect_sector_clustering(portfolio, lesson, sector_allocation))

        elif metric == "top3_concentration":
            pitfalls.extend(detect_top_concentration(portfolio, lesson))

        elif metric == "holding_count":
            pitfalls.extend(detect_insufficient_diversification(portfolio, lesson))

        elif metric == "stock_percentage":
            pitfalls.extend(detect_asset_allocation_imbalance(portfolio, lesson))

    return sorted(pitfalls, key=lambda p: severity_rank(p.severity))


def detect_overconcentration(portfolio: Portfolio, lesson: Dict) -> List[Pitfall]:
    """Check for single-stock overconcentration"""
    pitfalls = []
    threshold = lesson["red_flag_threshold"]

    for holding in portfolio.holdings:
        weight = holding.current_value / portfolio.total_current_value
        if weight > threshold:
            severity = "critical" if weight > 0.25 else "warning"
            pitfalls.append(Pitfall(
                lesson_id=lesson["id"],
                lesson_title=lesson["title"],
                severity=severity,
                metric_name="position_weight",
                current_value=weight,
                threshold=threshold,
                message=f"{holding.symbol} is {weight:.1%} of portfolio (max: {threshold:.0%})",
                recommendation=f"Reduce {holding.symbol} to {int(threshold * 100)}% or less. Current excess: ${holding.current_value - (portfolio.total_current_value * threshold):.2f}",
                affected_holdings=[holding.symbol]
            ))

    return pitfalls


def detect_sector_clustering(
    portfolio: Portfolio,
    lesson: Dict,
    sector_allocation: Dict[str, float]
) -> List[Pitfall]:
    """Check for sector overconcentration"""
    pitfalls = []
    threshold = lesson["red_flag_threshold"]

    for sector, weight in sector_allocation.items():
        if weight > threshold:
            severity = "critical" if weight > 0.50 else "warning"

            # Find holdings in this sector using hybrid lookup
            affected = [
                h.symbol for h in portfolio.holdings
                if get_sector_for_stock(h.symbol, SECTOR_MAP) == sector
            ]

            pitfalls.append(Pitfall(
                lesson_id=lesson["id"],
                lesson_title=lesson["title"],
                severity=severity,
                metric_name="sector_concentration",
                current_value=weight,
                threshold=threshold,
                message=f"{sector} sector is {weight:.1%} of portfolio (max: {threshold:.0%})",
                recommendation=f"Reduce {sector} holdings or add holdings from underrepresented sectors. Consider adding Healthcare or Financials.",
                affected_holdings=affected
            ))

    return pitfalls


def detect_top_concentration(portfolio: Portfolio, lesson: Dict) -> List[Pitfall]:
    """Check top 3 holdings concentration"""
    pitfalls = []
    threshold = lesson["red_flag_threshold"]

    concentration = get_top_n_concentration(portfolio, n=3)

    if concentration > threshold:
        severity = "critical" if concentration > 0.60 else "warning"

        top_3 = sorted(
            portfolio.holdings,
            key=lambda h: h.current_value,
            reverse=True
        )[:3]

        pitfalls.append(Pitfall(
            lesson_id=lesson["id"],
            lesson_title=lesson["title"],
            severity=severity,
            metric_name="top3_concentration",
            current_value=concentration,
            threshold=threshold,
            message=f"Top 3 holdings are {concentration:.1%} of portfolio (max: {threshold:.0%})",
            recommendation="Trim largest positions and reinvest in other holdings to reduce concentration risk.",
            affected_holdings=[h.symbol for h in top_3]
        ))

    return pitfalls


def detect_insufficient_diversification(portfolio: Portfolio, lesson: Dict) -> List[Pitfall]:
    """Check if portfolio has enough holdings"""
    pitfalls = []
    threshold = lesson["red_flag_threshold"]

    if portfolio.holding_count < threshold:
        pitfalls.append(Pitfall(
            lesson_id=lesson["id"],
            lesson_title=lesson["title"],
            severity="warning",
            metric_name="holding_count",
            current_value=portfolio.holding_count,
            threshold=threshold,
            message=f"Portfolio has only {portfolio.holding_count} holdings (recommended: {threshold}+)",
            recommendation=f"Add {threshold - portfolio.holding_count} more holdings, or use diversified ETFs (VTI, VOO) to fill gaps",
            affected_holdings=[]
        ))

    return pitfalls


def detect_asset_allocation_imbalance(portfolio: Portfolio, lesson: Dict) -> List[Pitfall]:
    """Check stock/bond allocation"""
    pitfalls = []

    # Calculate stock vs bond allocation
    stock_value = sum(
        h.current_value for h in portfolio.holdings
        if SECTOR_MAP.get(h.symbol) != "Bonds"
    )
    stock_pct = stock_value / portfolio.total_current_value if portfolio.total_current_value > 0 else 0

    # This is simplified - in production, would need more sophisticated logic
    if stock_pct > 0.95 or stock_pct < 0.10:
        pitfalls.append(Pitfall(
            lesson_id=lesson["id"],
            lesson_title=lesson["title"],
            severity="warning",
            metric_name="stock_percentage",
            current_value=stock_pct,
            threshold=0.70,
            message=f"Portfolio is {stock_pct:.0%} stocks, {100-stock_pct:.0%} bonds/cash",
            recommendation="Consider adding bonds for stability or stocks for growth depending on your age and goals",
            affected_holdings=[]
        ))

    return pitfalls


def calculate_risk_metrics(portfolio: Portfolio) -> Dict[str, float]:
    """Calculate key risk metrics"""
    return {
        "largest_position_pct": portfolio.largest_position_weight,
        "top_3_concentration": get_top_n_concentration(portfolio, 3),
        "top_5_concentration": get_top_n_concentration(portfolio, 5),
        "holding_count": portfolio.holding_count,
        "total_value": portfolio.total_current_value,
        "total_gain_loss_pct": portfolio.total_gain_loss_pct,
        "cash_position_pct": 0  # Would calculate from portfolio
    }


def calculate_concentration_metrics(portfolio: Portfolio) -> Dict[str, float]:
    """Calculate concentration metrics"""
    return {
        "largest_position": portfolio.largest_position_weight,
        "top_3": get_top_n_concentration(portfolio, 3),
        "herfindahl": calculate_herfindahl_index(portfolio),
        "diversification_ratio": calculate_diversification_ratio(portfolio)
    }


def calculate_herfindahl_index(portfolio: Portfolio) -> float:
    """
    Herfindahl index (0-1): Higher = more concentrated
    HHI = sum of (weight^2) for all holdings
    """
    if portfolio.total_current_value == 0:
        return 0

    hhi = 0
    for holding in portfolio.holdings:
        weight = holding.current_value / portfolio.total_current_value
        hhi += weight ** 2

    return hhi


def calculate_diversification_ratio(portfolio: Portfolio) -> float:
    """
    Diversification Ratio: (sum of weights) / portfolio weight
    Higher = better diversified
    Max = number of holdings (perfect equal weight)
    """
    if len(portfolio.holdings) == 0 or portfolio.total_current_value == 0:
        return 0

    # Simplified: just return holding count as proxy
    return len(portfolio.holdings)


def generate_recommendations(pitfalls: List[Pitfall], portfolio: Portfolio) -> List[str]:
    """Generate actionable recommendations from pitfalls"""
    recommendations = []

    # Group by severity
    critical = [p for p in pitfalls if p.severity == "critical"]
    warnings = [p for p in pitfalls if p.severity == "warning"]

    # Critical recommendations
    if critical:
        recommendations.append(f"⚠️ ADDRESS CRITICAL ISSUES: {len(critical)} pitfall(s) need immediate attention")
        for pitfall in critical[:3]:  # Top 3 critical
            recommendations.append(f"• {pitfall.recommendation}")

    # Warning recommendations
    if warnings:
        recommendations.append(f"📌 ADDRESS WARNINGS: {len(warnings)} area(s) to improve")
        for pitfall in warnings[:2]:  # Top 2 warnings
            recommendations.append(f"• {pitfall.recommendation}")

    # If no pitfalls
    if not pitfalls:
        recommendations.append("✅ Portfolio looks well-diversified! Consider annual rebalancing.")

    return recommendations


def create_summary(pitfalls: List[Pitfall], risk_metrics: Dict) -> str:
    """Create text summary of portfolio health"""
    critical_count = len([p for p in pitfalls if p.severity == "critical"])
    warning_count = len([p for p in pitfalls if p.severity == "warning"])

    if critical_count > 0:
        return f"🔴 Portfolio needs attention: {critical_count} critical issue(s), {warning_count} warning(s)"
    elif warning_count > 0:
        return f"🟡 Portfolio is acceptable but could be improved: {warning_count} warning(s)"
    else:
        return "🟢 Portfolio is well-structured and diversified"


def severity_rank(severity: str) -> int:
    """Rank severity for sorting"""
    ranks = {"critical": 0, "warning": 1, "info": 2}
    return ranks.get(severity, 3)
