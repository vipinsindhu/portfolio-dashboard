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
from storage_paths import data_path
from sector_config import normalize_sector


# Sector cache file for dynamic lookups
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
SECTOR_CACHE_FILE = data_path("sector_cache.json")
SECTOR_MAP_FILE = os.path.join(_BACKEND_DIR, "sector_map.json")
INDEX_DECOMPOSITION_CACHE_FILE = os.path.join(_BACKEND_DIR, "index_decomposition_cache.json")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
FINNHUB_BASE = "https://finnhub.io/api/v1"


def load_sector_map_from_file() -> Dict[str, str]:
    """Load sector map from JSON file, with fallback to hardcoded map"""
    if os.path.exists(SECTOR_MAP_FILE):
        try:
            with open(SECTOR_MAP_FILE, "r") as f:
                sector_map = json.load(f)
                print(f"[Analysis] Loaded {len(sector_map)} sector mappings from file")
                return sector_map
        except Exception as e:
            print(f"[Analysis] Error loading sector map file: {e}, using fallback")

    # Fallback to empty dict - will be populated by lookups
    print("[Analysis] Using dynamic sector lookup (no sector_map.json found)")
    return {}


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
            raw = data.get("finnhubIndustry")
            if raw:
                sector = normalize_sector(raw)
                print(f"[Sector Cache] Found sector for {symbol}: {sector}")
                return sector
    except Exception as e:
        print(f"[Sector Cache] Error fetching {symbol} from Finnhub: {e}")

    return None


def load_index_decomposition_cache() -> Dict:
    """Load cached index fund decompositions"""
    if os.path.exists(INDEX_DECOMPOSITION_CACHE_FILE):
        try:
            with open(INDEX_DECOMPOSITION_CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Index Decomposer] Error loading decomposition cache: {e}")
    return {}


def get_index_decomposition(symbol: str) -> Optional[Dict[str, float]]:
    """
    Get decomposed sector allocation for an index fund
    Returns dict of {sector: allocation_weight} or None if not an index fund
    """
    cache = load_index_decomposition_cache()

    if symbol in cache:
        decomposition = cache[symbol]
        return decomposition.get("sectors")

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
    sector_allocation: Dict
    concentration_metrics: Dict[str, float]
    recommendations: List[str]
    summary: str


# Load sector mapping from JSON file (supports auto-updates every 7 days)
# This will be populated by load_sector_map_from_file() when the module loads
SECTOR_MAP = {}

# Target sector allocation ranges
TARGET_ALLOCATION = {
    "Broad Market Index": {"min": 0.25, "max": 0.50, "ideal": 0.40},  # Core US equity exposure
    "International Equities": {"min": 0.10, "max": 0.25, "ideal": 0.15},  # Diversification globally
    "Real Estate": {"min": 0.05, "max": 0.15, "ideal": 0.10},  # REITs for diversification
    "Technology": {"min": 0.10, "max": 0.20, "ideal": 0.15},  # Sector within equities
    "Financials": {"min": 0.08, "max": 0.15, "ideal": 0.11},
    "Healthcare": {"min": 0.08, "max": 0.15, "ideal": 0.11},
    "Consumer": {"min": 0.05, "max": 0.12, "ideal": 0.08},
    "Industrials": {"min": 0.03, "max": 0.10, "ideal": 0.06},
    "Energy": {"min": 0.02, "max": 0.08, "ideal": 0.04},
    "Utilities": {"min": 0.02, "max": 0.08, "ideal": 0.04},
    "Materials": {"min": 0.01, "max": 0.05, "ideal": 0.02},
    "Bonds": {"min": 0.10, "max": 0.40, "ideal": 0.20},  # Stability, age-dependent
    "Commodities": {"min": 0.00, "max": 0.10, "ideal": 0.03},  # Inflation hedge
    "Cryptocurrencies": {"min": 0.00, "max": 0.05, "ideal": 0.01},  # High risk/speculative
    "Other": {"min": 0.00, "max": 0.05, "ideal": 0.00},  # Should minimize unknown stocks
}


# Load sector map from JSON file at module initialization
def _initialize_sector_map():
    """Initialize sector map from JSON file"""
    global SECTOR_MAP
    SECTOR_MAP = load_sector_map_from_file()


# Initialize sector map when module loads
_initialize_sector_map()


def get_hybrid_sector_weights(portfolio: Portfolio, static_sector_map: Dict[str, str]) -> Dict[str, float]:
    """
    Calculate sector weights using hybrid lookup with index fund decomposition:
    1. Check if holding is an index fund - if yes, decompose into constituent sectors
    2. Otherwise use standard sector lookup:
       a. Static map for known stocks
       b. Cache for previously looked up stocks
       c. Finnhub for new unknown stocks
       d. "Other" as fallback
    """
    sector_values = {}

    for holding in portfolio.holdings:
        # Check if this is an index fund with decomposed sectors
        decomposition = get_index_decomposition(holding.symbol)

        if decomposition:
            # This is an index fund - allocate its value across decomposed sectors
            print(f"[Analysis] Decomposing index fund {holding.symbol} into {len(decomposition)} sectors")
            for sector, sector_weight in decomposition.items():
                if sector not in sector_values:
                    sector_values[sector] = 0
                # Multiply holding's value by the sector's weight within the index
                sector_values[sector] += holding.current_value * sector_weight
        else:
            # Regular stock - use standard sector lookup
            sector = get_sector_for_stock(holding.symbol, static_sector_map)

            if sector not in sector_values:
                sector_values[sector] = 0
            sector_values[sector] += holding.current_value

    total = sum(sector_values.values())
    return {
        sector: (value / total) if total > 0 else 0
        for sector, value in sector_values.items()
    }


def get_sector_weights_with_holdings(portfolio: Portfolio, static_sector_map: Dict) -> Tuple[Dict[str, float], Dict[str, List[Dict]]]:
    """
    Calculate sector weights AND track contributing holdings
    Returns: (sector_weights, sector_holdings)
    """
    sector_values = {}
    sector_holdings = {}
    total_portfolio_value = sum(h.current_value for h in portfolio.holdings)

    for holding in portfolio.holdings:
        # Check if this is an index fund with decomposed sectors
        decomposition = get_index_decomposition(holding.symbol)

        if decomposition:
            # Index fund - allocate across decomposed sectors
            for sector, sector_weight in decomposition.items():
                if sector not in sector_values:
                    sector_values[sector] = 0
                    sector_holdings[sector] = []

                contribution = holding.current_value * sector_weight
                sector_values[sector] += contribution

                # Track this holding's contribution to the sector
                sector_holdings[sector].append({
                    "symbol": holding.symbol,
                    "contribution": contribution,
                    "percentage": (contribution / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
                })
        else:
            # Regular stock - use standard sector lookup
            sector = get_sector_for_stock(holding.symbol, static_sector_map)

            if sector not in sector_values:
                sector_values[sector] = 0
                sector_holdings[sector] = []

            sector_values[sector] += holding.current_value
            sector_holdings[sector].append({
                "symbol": holding.symbol,
                "contribution": holding.current_value,
                "percentage": (holding.current_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
            })

    # Convert to percentages
    total = sum(sector_values.values())
    sector_weights = {
        sector: (value / total) if total > 0 else 0
        for sector, value in sector_values.items()
    }

    # Sort holdings by contribution within each sector
    for sector in sector_holdings:
        sector_holdings[sector].sort(key=lambda x: x["contribution"], reverse=True)

    return sector_weights, sector_holdings


def get_enhanced_sector_analysis(portfolio: Portfolio, sector_map: Dict) -> Dict:
    """Get detailed sector allocation analysis with recommendations and contributing holdings"""
    # Get sector weights and contributing holdings
    sector_weights, sector_holdings = get_sector_weights_with_holdings(portfolio, sector_map)
    enhanced_data = {}

    for sector, weight in sector_weights.items():
        target = TARGET_ALLOCATION.get(sector, {"min": 0, "max": 1, "ideal": 0.5})
        min_target = target["min"]
        max_target = target["max"]
        ideal = target["ideal"]

        # Determine health status
        if weight < min_target * 0.8:  # Significantly underweight
            status = "underweight"
            recommendation = f"You have very little in {sector} ({weight:.0%}). Consider adding more to balance your portfolio."
        elif weight > max_target * 1.2:  # Significantly overweight
            status = "overweight"
            recommendation = f"Too much in {sector} ({weight:.0%}). Try to reduce this and add other types of investments."
        elif min_target <= weight <= max_target:  # Within range
            status = "optimal"
            recommendation = f"Your {sector} amount looks good ({weight:.0%})."
        else:
            status = "caution"
            recommendation = f"Your {sector} is close to being out of balance ({weight:.0%}). Keep an eye on it."

        gap = ideal - weight

        enhanced_data[sector] = {
            "current": weight,
            "target": ideal,
            "min": min_target,
            "max": max_target,
            "gap": gap,
            "status": status,
            "recommendation": recommendation,
            "holdings": sector_holdings.get(sector, [])
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

    # Compute sector weights + holdings once; reuse in detect_sector_clustering
    sector_allocation, sector_holdings = get_sector_weights_with_holdings(portfolio, SECTOR_MAP)

    # Check each pitfall lesson
    for lesson in LESSONS:
        metric = lesson.get("metric")

        if metric == "position_weight":
            pitfalls.extend(detect_overconcentration(portfolio, lesson))

        elif metric == "sector_concentration":
            pitfalls.extend(detect_sector_clustering(portfolio, lesson, sector_allocation, sector_holdings))

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
                message=f"{holding.symbol} is {weight:.1%} of your portfolio. That's a lot of eggs in one basket!",
                recommendation=f"Try to reduce {holding.symbol} to {int(threshold * 100)}% or less of your portfolio. This will reduce your risk.",
                affected_holdings=[holding.symbol]
            ))

    return pitfalls


def detect_sector_clustering(
    portfolio: Portfolio,
    lesson: Dict,
    sector_allocation: Dict[str, float],
    sector_holdings: Dict = None,
) -> List[Pitfall]:
    """Check for sector overconcentration"""
    pitfalls = []
    threshold = lesson["red_flag_threshold"]

    for sector, weight in sector_allocation.items():
        if weight > threshold:
            severity = "critical" if weight > 0.50 else "warning"

            if sector_holdings is not None:
                affected = [h["symbol"] for h in sector_holdings.get(sector, [])]
            else:
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
                message=f"{sector} makes up {weight:.0%} of your portfolio. You need more variety.",
                recommendation=f"Reduce your {sector} stocks and add other industries like Healthcare or Financials.",
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
            message=f"Your top 3 stocks are {concentration:.0%} of your portfolio. That's too much risk.",
            recommendation="Make your biggest stocks smaller and buy more different stocks.",
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
            message=f"You only own {portfolio.holding_count} different stocks. You need more variety.",
            recommendation=f"Add {threshold - portfolio.holding_count} more stocks, or use ETFs like VTI or VOO to spread your money across many companies at once.",
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
            message=f"You have {stock_pct:.0%} in stocks and {1-stock_pct:.0%} in bonds or cash.",
            recommendation="Think about balancing your mix. Younger? Focus on stocks. Older? Add more bonds for safety.",
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
        recommendations.append(f"⚠️ IMPORTANT: You have {len(critical)} big issue(s) to fix right away:")
        for pitfall in critical[:3]:  # Top 3 critical
            recommendations.append(f"• {pitfall.recommendation}")

    # Warning recommendations
    if warnings:
        recommendations.append(f"📌 GOOD TO FIX: {len(warnings)} thing(s) you could improve:")
        for pitfall in warnings[:2]:  # Top 2 warnings
            recommendations.append(f"• {pitfall.recommendation}")

    # If no pitfalls
    if not pitfalls:
        recommendations.append("Great! Your portfolio looks well-balanced. Check it once a year and rebalance if needed.")

    return recommendations


def create_summary(pitfalls: List[Pitfall], risk_metrics: Dict) -> str:
    """Create text summary of portfolio health"""
    critical_count = len([p for p in pitfalls if p.severity == "critical"])
    warning_count = len([p for p in pitfalls if p.severity == "warning"])

    if critical_count > 0:
        return f"🔴 Fix {critical_count} big problem(s) and {warning_count} smaller issue(s)"
    elif warning_count > 0:
        return f"🟡 Pretty good! You could improve {warning_count} thing(s)"
    else:
        return "🟢 Excellent! Your portfolio is well-balanced"


def severity_rank(severity: str) -> int:
    """Rank severity for sorting"""
    ranks = {"critical": 0, "warning": 1, "info": 2}
    return ranks.get(severity, 3)
