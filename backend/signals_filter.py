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


# Minimum confidence for a signal to surface as a general recommendation
MIN_RECOMMENDATION_CONFIDENCE = 5

# Single-position weight above which we stop suggesting "accumulate".
# Mirrors the position_weight red_flag_threshold in lessons.json so
# recommendations never contradict the pitfall detector.
POSITION_CONCENTRATION_THRESHOLD = 0.20


def matches_timeframe(signal: Dict, timeframe: TimeHorizon) -> bool:
    """Untagged (legacy) signals match any timeframe; tagged ones their own."""
    tag = signal.get("timeframe")
    return tag is None or tag == timeframe.value


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

    signals = [s for s in signals if matches_timeframe(s, timeframe)]

    if not portfolio or portfolio.holding_count == 0:
        # No portfolio - return general recommendations
        return {
            "sell_reduce": filter_signals_by_direction(signals, "avoid"),
            "hold": filter_signals_by_direction(signals, "hold"),
            "add": filter_signals_by_direction(signals, "buy"),
            "portfolio_value": 0
        }

    # Portfolio exists - create contextualized recommendations.
    # Ownership matching must be case-insensitive (holdings may be stored
    # in any case depending on how they were entered).
    portfolio_symbols = set(h.symbol.upper() for h in portfolio.holdings)

    # Signals for existing holdings
    holdings_signals = [s for s in signals if s.get("ticker", "").upper() in portfolio_symbols]
    new_recommendations = [s for s in signals if s.get("ticker", "").upper() not in portfolio_symbols]

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
                # Existing holding with buy signal = hold/accumulate,
                # unless the position is already over-concentrated — then
                # never advise adding more (keeps recommendations consistent
                # with the pitfall detector).
                if weight > POSITION_CONCENTRATION_THRESHOLD:
                    hold_list.append(add_portfolio_context(
                        signal, holding, weight, "hold_concentrated"
                    ))
                else:
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

    elif action == "hold_concentrated":
        new_rationale += (
            f"\n\nPortfolio Action: HOLD - This stock looks good, but it is already "
            f"{weight:.0%} of your portfolio (over the "
            f"{POSITION_CONCENTRATION_THRESHOLD:.0%} concentration guideline). "
            f"Don't add more - consider trimming to reduce risk."
        )
        # Surfaces as a plain HOLD in the UI
        action = "hold"

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
) -> List[FilteredSignal]:
    """General (no-portfolio) recommendations: confidence-screened signals of one direction"""

    return [
        FilteredSignal(
            ticker=s.get("ticker"),
            direction=s.get("direction"),
            confidence=s.get("confidence", 5),
            rationale=s.get("rationale", ""),
            original_rationale=s.get("rationale", ""),
            recommendation_type=map_direction_to_action(s.get("direction"), "long"),
        )
        for s in signals
        if s.get("direction") == direction
        and s.get("confidence", 0) >= MIN_RECOMMENDATION_CONFIDENCE
    ]
