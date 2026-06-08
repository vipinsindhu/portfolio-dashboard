"""
Portfolio analysis engine
Detects pitfalls, calculates risk metrics, compares against benchmarks
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from portfolio import Portfolio, Holding, get_sector_weights, get_top_n_concentration
from educational import LESSONS


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

    # Index Funds / Diversified
    "VTI": "Diversified",
    "VOO": "Diversified",
    "SPY": "Diversified",
    "VTSAX": "Diversified",
    "SPLG": "Diversified",
    "IVV": "Diversified",
    "SCHB": "Diversified",
    "VFIAX": "Diversified",
    "FSKAX": "Diversified",

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
}

# Target sector allocation ranges
TARGET_ALLOCATION = {
    "Technology": {"min": 0.20, "max": 0.30, "ideal": 0.25},
    "Financials": {"min": 0.12, "max": 0.20, "ideal": 0.16},
    "Healthcare": {"min": 0.12, "max": 0.20, "ideal": 0.16},
    "Consumer": {"min": 0.08, "max": 0.15, "ideal": 0.12},
    "Diversified": {"min": 0.00, "max": 0.20, "ideal": 0.10},
    "Bonds": {"min": 0.10, "max": 0.25, "ideal": 0.18},
}


def get_enhanced_sector_analysis(portfolio: Portfolio, sector_map: Dict) -> Dict:
    """Get detailed sector allocation analysis with recommendations"""
    sector_weights = get_sector_weights(portfolio, sector_map)
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

    # Get sector allocation
    sector_allocation = get_sector_weights(portfolio, SECTOR_MAP)

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

            # Find holdings in this sector
            affected = [
                h.symbol for h in portfolio.holdings
                if SECTOR_MAP.get(h.symbol) == sector
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
