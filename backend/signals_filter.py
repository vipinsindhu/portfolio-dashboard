"""
Signal filtering and routing for short-term and long-term investment strategies
Filters signals based on timeframe and portfolio context
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from portfolio import Portfolio, Holding


class TimeHorizon(Enum):
    """Investment time horizons"""
    SHORT_TERM = "short_term"  # 1-3 months
    LONG_TERM = "long_term"    # 1+ years


class SignalType(Enum):
    """Types of signals"""
    BUY = "buy"
    HOLD = "hold"
    AVOID = "avoid"


@dataclass
class FilteredSignal:
    """Signal with context and reasoning"""
    ticker: str
    direction: str
    confidence: int
    rationale: str
    original_rationale: str
    portfolio_context: Optional[str] = None
    is_in_portfolio: bool = False
    weight_in_portfolio: float = 0.0
    recommendation_type: str = ""  # "add", "hold", "reduce", "sell"


def filter_signals_by_timeframe(
    signals: List[Dict],
    timeframe: TimeHorizon,
    market_conditions: Optional[Dict] = None
) -> List[FilteredSignal]:
    """
    Filter signals based on investment timeframe
    Applies different logic for short-term vs long-term
    """

    if timeframe == TimeHorizon.SHORT_TERM:
        return filter_short_term_signals(signals, market_conditions)
    else:
        return filter_long_term_signals(signals, market_conditions)


def filter_short_term_signals(
    signals: List[Dict],
    market_conditions: Optional[Dict] = None
) -> List[FilteredSignal]:
    """
    Short-term (1-3 month) signal filtering
    Focuses on: momentum, technical strength, market timing
    """

    filtered = []

    # Get current market conditions
    vix = market_conditions.get("vix", 18.5) if market_conditions else 18.5
    fed_rate = market_conditions.get("fed_rate", 5.25) if market_conditions else 5.25

    for signal in signals:
        # Score for short-term viability
        score = calculate_short_term_score(signal, vix, fed_rate)

        if score >= 6:  # High confidence for short-term
            filtered.append(FilteredSignal(
                ticker=signal.get("ticker"),
                direction=signal.get("direction"),
                confidence=signal.get("confidence", 5),
                rationale=signal.get("rationale", ""),
                original_rationale=signal.get("rationale", ""),
                portfolio_context=f"Market VIX: {vix:.1f} | Fed Rate: {fed_rate:.2f}%",
                recommendation_type=map_direction_to_action(signal.get("direction"), "short")
            ))

    return filtered


def filter_long_term_signals(
    signals: List[Dict],
    market_conditions: Optional[Dict] = None
) -> List[FilteredSignal]:
    """
    Long-term (1+ year) signal filtering
    Focuses on: fundamentals, valuation, dividend yield
    """

    filtered = []

    for signal in signals:
        # Long-term signals prioritize fundamentals
        # Less affected by short-term volatility
        if signal.get("confidence", 5) >= 5:  # Lower bar for long-term

            # Filter for quality/stability
            sector = signal.get("sector")
            if is_quality_sector_long_term(sector):
                filtered.append(FilteredSignal(
                    ticker=signal.get("ticker"),
                    direction=signal.get("direction"),
                    confidence=signal.get("confidence", 5),
                    rationale=signal.get("rationale", ""),
                    original_rationale=signal.get("rationale", ""),
                    portfolio_context="Long-term fundamentals focused",
                    recommendation_type=map_direction_to_action(
                        signal.get("direction"), "long"
                    )
                ))

    return filtered


def filter_signals_with_portfolio(
    signals: List[Dict],
    portfolio: Optional[Portfolio],
    timeframe: TimeHorizon,
    market_conditions: Optional[Dict] = None
) -> Dict:
    """
    Filter and contextualize signals based on user's portfolio
    Returns: {sell_reduce, hold, add}
    """

    if not portfolio or portfolio.holding_count == 0:
        # No portfolio - return general recommendations
        return {
            "sell_reduce": filter_signals_by_direction(signals, "avoid", timeframe, market_conditions),
            "hold": filter_signals_by_direction(signals, "hold", timeframe, market_conditions),
            "add": filter_signals_by_direction(signals, "buy", timeframe, market_conditions),
            "portfolio_value": 0
        }

    # Portfolio exists - create contextualized recommendations
    portfolio_symbols = set(h.symbol for h in portfolio.holdings)

    # Signals for existing holdings
    holdings_signals = [s for s in signals if s.get("ticker") in portfolio_symbols]
    new_recommendations = [s for s in signals if s.get("ticker") not in portfolio_symbols]

    # Contextualize holdings signals
    sell_reduce = []
    hold_list = []

    for signal in holdings_signals:
        holding = portfolio.get_holding(signal.get("ticker"))
        if holding:
            weight = holding.current_value / portfolio.total_current_value

            if signal.get("direction") == "avoid":
                sell_reduce.append(add_portfolio_context(
                    signal, holding, weight, "short-term"
                ))
            elif signal.get("direction") == "hold":
                hold_list.append(add_portfolio_context(
                    signal, holding, weight, "hold"
                ))
            elif signal.get("direction") == "buy":
                # Existing holding with buy signal = hold/accumulate
                hold_list.append(add_portfolio_context(
                    signal, holding, weight, "accumulate"
                ))

    # Filter new recommendations
    add_recommendations = [
        add_portfolio_context(s, None, 0, "add")
        for s in new_recommendations
        if would_improve_portfolio(s, portfolio)
    ]

    return {
        "sell_reduce": sell_reduce,
        "hold": hold_list,
        "add": add_recommendations,
        "portfolio_value": portfolio.total_current_value,
        "portfolio_holdings": portfolio.holding_count
    }


def add_portfolio_context(
    signal: Dict,
    holding: Optional[Holding],
    weight: float,
    action: str
) -> FilteredSignal:
    """Add portfolio context to a signal"""

    context = ""
    if holding:
        context = f"Current position: {weight:.1%} of portfolio (${holding.current_value:.2f})"

    new_rationale = signal.get("rationale", "")

    if action == "short-term":
        new_rationale += f"\n\nPortfolio Action: REDUCE/TRIM - Take profits while market is favorable"

    elif action == "accumulate":
        new_rationale += f"\n\nPortfolio Action: ACCUMULATE - Add to this position at any weakness"

    elif action == "hold":
        new_rationale += f"\n\nPortfolio Action: HOLD - Maintain current position"

    elif action == "add":
        new_rationale += f"\n\nPortfolio Action: ADD - This holding would improve diversification"

    return FilteredSignal(
        ticker=signal.get("ticker"),
        direction=signal.get("direction"),
        confidence=signal.get("confidence", 5),
        rationale=new_rationale,
        original_rationale=signal.get("rationale", ""),
        portfolio_context=context,
        is_in_portfolio=holding is not None,
        weight_in_portfolio=weight,
        recommendation_type=action
    )


def would_improve_portfolio(signal: Dict, portfolio: Portfolio) -> bool:
    """Check if adding this signal's ticker would improve portfolio"""

    ticker = signal.get("ticker")

    # Don't recommend if already in portfolio
    if portfolio.get_holding(ticker):
        return False

    # Recommend if signal is buy AND portfolio is underweight in that sector
    if signal.get("direction") == "buy":
        sector = signal.get("sector")

        # This is simplified - in production, would check sector allocation
        # For now, recommend if portfolio is small or tech-heavy
        if portfolio.holding_count < 10:
            return True

        # Check if sector is underrepresented
        sector_holdings = sum(
            1 for h in portfolio.holdings
            if h.symbol in ["JNJ", "UNH", "PFE"]  # Healthcare examples
        )

        if sector == "Healthcare" and sector_holdings == 0:
            return True

    return False


def calculate_short_term_score(signal: Dict, vix: float, fed_rate: float) -> float:
    """Calculate score for short-term viability"""

    score = 0

    # Base confidence
    score += signal.get("confidence", 5) / 10

    # Adjust for market conditions
    if signal.get("direction") == "buy":
        # Prefer buys when VIX is rising (uncertain market = opportunities)
        if vix > 20:
            score += 1
        # Avoid buys when rates are very high
        if fed_rate > 5.5:
            score -= 0.5

    elif signal.get("direction") == "avoid":
        # Avoid signals matter more when VIX is low (complacency)
        if vix < 15:
            score += 1

    return score


def map_direction_to_action(direction: str, strategy: str) -> str:
    """Map signal direction to portfolio action"""

    if direction == "buy":
        return "add" if strategy == "short" else "accumulate"
    elif direction == "hold":
        return "hold"
    else:  # avoid
        return "reduce" if strategy == "short" else "sell"


def is_quality_sector_long_term(sector: Optional[str]) -> bool:
    """Check if sector is suitable for long-term hold"""

    quality_sectors = {
        "Healthcare",
        "Financials",
        "Consumer",
        "Utilities",
        "Diversified"
    }

    return sector in quality_sectors


def filter_signals_by_direction(
    signals: List[Dict],
    direction: str,
    timeframe: TimeHorizon,
    market_conditions: Optional[Dict] = None
) -> List[FilteredSignal]:
    """Filter signals by direction and timeframe"""

    filtered_signals = [s for s in signals if s.get("direction") == direction]

    if timeframe == TimeHorizon.SHORT_TERM:
        return filter_short_term_signals(filtered_signals, market_conditions)
    else:
        return filter_long_term_signals(filtered_signals, market_conditions)
