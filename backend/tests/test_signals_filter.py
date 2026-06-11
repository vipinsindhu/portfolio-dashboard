"""Tests for the portfolio recommendation classifier (signals_filter.py).

Pins the PRD P0-2 contract:
- "add" must only contain tickers the user does NOT own
- "sell_reduce" must only contain tickers the user DOES own
- ownership matching is case-insensitive
- recommendations never tell the user to accumulate an over-concentrated position
"""

from datetime import datetime

from portfolio import Portfolio, Holding
from signals_filter import (
    TimeHorizon,
    filter_signals_with_portfolio,
)


def make_portfolio(holdings_spec):
    """holdings_spec: list of (symbol, current_value) tuples."""
    now = datetime.now().isoformat()
    holdings = [
        Holding(symbol=sym, quantity=1, purchase_price=value, current_price=value)
        for sym, value in holdings_spec
    ]
    return Portfolio(holdings=holdings, created_at=now, updated_at=now)


def make_signal(ticker, direction, confidence=8, sector="Technology"):
    return {
        "ticker": ticker,
        "direction": direction,
        "confidence": confidence,
        "rationale": f"Test rationale for {ticker}",
        "sector": sector,
    }


class TestOwnershipClassification:
    def test_add_excludes_owned_tickers(self):
        portfolio = make_portfolio([("AAPL", 100), ("MSFT", 100), ("JNJ", 100)])
        signals = [make_signal("AAPL", "buy"), make_signal("WMT", "buy")]

        result = filter_signals_with_portfolio(
            signals, portfolio, TimeHorizon.LONG_TERM
        )

        add_tickers = {s.ticker for s in result["add"]}
        assert "AAPL" not in add_tickers
        assert "WMT" in add_tickers

    def test_sell_reduce_only_contains_owned_tickers(self):
        portfolio = make_portfolio([("AAPL", 100), ("MSFT", 100)])
        signals = [make_signal("AAPL", "avoid"), make_signal("XOM", "avoid")]

        result = filter_signals_with_portfolio(
            signals, portfolio, TimeHorizon.LONG_TERM
        )

        sell_tickers = {s.ticker for s in result["sell_reduce"]}
        assert "AAPL" in sell_tickers
        assert "XOM" not in sell_tickers

    def test_owned_buy_signal_becomes_accumulate_hold(self):
        portfolio = make_portfolio([("AAPL", 100), ("MSFT", 100), ("JNJ", 100)])
        signals = [make_signal("AAPL", "buy")]

        result = filter_signals_with_portfolio(
            signals, portfolio, TimeHorizon.LONG_TERM
        )

        hold_tickers = {s.ticker for s in result["hold"]}
        assert "AAPL" in hold_tickers

    def test_ownership_matching_is_case_insensitive(self):
        # Holdings stored lowercase must still be recognized as owned.
        portfolio = make_portfolio([("aapl", 100), ("msft", 100)])
        signals = [make_signal("AAPL", "avoid"), make_signal("MSFT", "buy")]

        result = filter_signals_with_portfolio(
            signals, portfolio, TimeHorizon.LONG_TERM
        )

        sell_tickers = {s.ticker for s in result["sell_reduce"]}
        hold_tickers = {s.ticker for s in result["hold"]}
        add_tickers = {s.ticker for s in result["add"]}

        # The avoid signal for an owned stock must surface in sell_reduce,
        # not silently disappear.
        assert "AAPL" in sell_tickers
        # The buy signal for an owned stock belongs in hold, never add.
        assert "MSFT" in hold_tickers
        assert "MSFT" not in add_tickers


class TestNoPortfolioBranch:
    def test_short_term_without_portfolio_returns_general_recommendations(self):
        signals = [
            make_signal("AAPL", "buy", confidence=9),
            make_signal("XOM", "avoid", confidence=7),
            make_signal("JNJ", "hold", confidence=6),
        ]

        result = filter_signals_with_portfolio(
            signals, None, TimeHorizon.SHORT_TERM, {"vix": 18.0, "fed_rate": 5.0}
        )

        assert {s.ticker for s in result["add"]} == {"AAPL"}
        assert {s.ticker for s in result["sell_reduce"]} == {"XOM"}
        assert {s.ticker for s in result["hold"]} == {"JNJ"}

    def test_long_term_without_portfolio_returns_general_recommendations(self):
        signals = [
            make_signal("AAPL", "buy", confidence=9),
            make_signal("XOM", "avoid", confidence=7),
        ]

        result = filter_signals_with_portfolio(
            signals, None, TimeHorizon.LONG_TERM
        )

        assert {s.ticker for s in result["add"]} == {"AAPL"}
        assert {s.ticker for s in result["sell_reduce"]} == {"XOM"}

    def test_low_confidence_signals_filtered_out(self):
        signals = [make_signal("AAPL", "buy", confidence=3)]

        result = filter_signals_with_portfolio(
            signals, None, TimeHorizon.LONG_TERM
        )

        assert result["add"] == []


class TestPitfallReconciliation:
    def test_concentrated_position_never_told_to_accumulate(self):
        # AAPL is 50% of the portfolio — over the 20% concentration red flag.
        portfolio = make_portfolio([("AAPL", 500), ("MSFT", 250), ("JNJ", 250)])
        signals = [make_signal("AAPL", "buy")]

        result = filter_signals_with_portfolio(
            signals, portfolio, TimeHorizon.LONG_TERM
        )

        aapl = next(s for s in result["hold"] if s.ticker == "AAPL")
        assert aapl.recommendation_type != "accumulate"
        assert "ACCUMULATE" not in aapl.rationale
        # The rationale should warn about the concentration instead.
        assert "concentrat" in aapl.rationale.lower() or "large" in aapl.rationale.lower()

    def test_normal_weight_position_can_accumulate(self):
        # AAPL is 10% of the portfolio — fine to accumulate.
        portfolio = make_portfolio(
            [("AAPL", 100), ("MSFT", 300), ("JNJ", 300), ("WMT", 300)]
        )
        signals = [make_signal("AAPL", "buy")]

        result = filter_signals_with_portfolio(
            signals, portfolio, TimeHorizon.LONG_TERM
        )

        aapl = next(s for s in result["hold"] if s.ticker == "AAPL")
        assert aapl.recommendation_type == "accumulate"
