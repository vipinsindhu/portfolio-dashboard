"""Unit tests for the pitfall detector and risk metrics."""

import pytest

from portfolio import Holding, create_portfolio
import analysis
from analysis import (
    analyze_portfolio,
    calculate_herfindahl_index,
    create_summary,
    detect_all_pitfalls,
    severity_rank,
)


def make_portfolio(*holdings):
    return create_portfolio([Holding(*h) for h in holdings])


def pitfalls_by_metric(pitfalls, metric):
    return [p for p in pitfalls if p.metric_name == metric]


# A balanced portfolio: 8 holdings, no position over 20%, sectors spread
BALANCED = [
    ("AAPL", 10, 100),   # Tech 12.5%
    ("JPM", 10, 100),    # Financials 12.5%
    ("XOM", 10, 100),    # Energy 12.5%
    ("BND", 10, 100),    # Bonds 12.5%
    ("JNJ", 10, 100),    # Healthcare 12.5%
    ("WMT", 10, 100),    # Consumer 12.5%
    ("MSFT", 5, 100),    # Tech 6.25%
    ("NVDA", 15, 100),   # Tech 18.75%... adjusted below
]


class TestOverconcentration:
    def test_position_over_25pct_is_critical(self, sector_map):
        # NVDA 27% of a 6-stock portfolio (the demo portfolio)
        p = make_portfolio(
            ("AAPL", 10, 180), ("MSFT", 6, 410), ("NVDA", 30, 120),
            ("JPM", 12, 195), ("XOM", 15, 110), ("BND", 20, 73),
        )
        hits = pitfalls_by_metric(detect_all_pitfalls(p), "position_weight")
        nvda = [h for h in hits if "NVDA" in h.affected_holdings]
        assert len(nvda) == 1
        assert nvda[0].severity == "critical"

    def test_position_between_20_and_25pct_is_warning(self, sector_map):
        # AAPL 22%
        p = make_portfolio(("AAPL", 22, 10), ("JPM", 39, 10), ("XOM", 39, 10))
        hits = pitfalls_by_metric(detect_all_pitfalls(p), "position_weight")
        aapl = [h for h in hits if "AAPL" in h.affected_holdings]
        assert len(aapl) == 1
        assert aapl[0].severity == "warning"

    def test_no_flag_under_20pct(self, sector_map):
        p = make_portfolio(
            ("AAPL", 1, 100), ("JPM", 1, 100), ("XOM", 1, 100),
            ("BND", 1, 100), ("JNJ", 1, 100), ("WMT", 1, 100),
        )
        assert pitfalls_by_metric(detect_all_pitfalls(p), "position_weight") == []


class TestSectorClustering:
    def test_sector_over_50pct_is_critical(self, sector_map):
        # Technology = 60%
        p = make_portfolio(
            ("AAPL", 1, 200), ("MSFT", 1, 200), ("NVDA", 1, 200),
            ("JPM", 1, 200), ("XOM", 1, 100), ("BND", 1, 100),
        )
        hits = pitfalls_by_metric(detect_all_pitfalls(p), "sector_concentration")
        assert len(hits) == 1
        assert hits[0].severity == "critical"
        assert set(hits[0].affected_holdings) == {"AAPL", "MSFT", "NVDA"}

    def test_sector_between_40_and_50pct_is_warning(self, sector_map):
        # Technology = 45%
        p = make_portfolio(
            ("AAPL", 1, 250), ("MSFT", 1, 200),
            ("JPM", 1, 150), ("XOM", 1, 150), ("BND", 1, 150), ("JNJ", 1, 100),
        )
        hits = pitfalls_by_metric(detect_all_pitfalls(p), "sector_concentration")
        assert len(hits) == 1
        assert hits[0].severity == "warning"

    def test_no_flag_when_sectors_balanced(self, sector_map):
        p = make_portfolio(
            ("AAPL", 1, 100), ("JPM", 1, 100), ("XOM", 1, 100),
            ("BND", 1, 100), ("JNJ", 1, 100), ("WMT", 1, 100),
        )
        assert pitfalls_by_metric(detect_all_pitfalls(p), "sector_concentration") == []


class TestTopConcentration:
    def test_top3_over_60pct_flagged(self, sector_map):
        p = make_portfolio(
            ("AAPL", 1, 300), ("JPM", 1, 250), ("XOM", 1, 200),
            ("BND", 1, 100), ("JNJ", 1, 100), ("WMT", 1, 50),
        )
        hits = pitfalls_by_metric(detect_all_pitfalls(p), "top3_concentration")
        assert len(hits) == 1
        assert set(hits[0].affected_holdings) == {"AAPL", "JPM", "XOM"}


class TestInsufficientDiversification:
    def test_under_5_holdings_warns(self, sector_map):
        p = make_portfolio(("AAPL", 1, 100), ("JPM", 1, 100), ("XOM", 1, 100))
        hits = pitfalls_by_metric(detect_all_pitfalls(p), "holding_count")
        assert len(hits) == 1
        assert hits[0].severity == "warning"

    def test_6_holdings_ok(self, sector_map):
        p = make_portfolio(
            ("AAPL", 1, 100), ("JPM", 1, 100), ("XOM", 1, 100),
            ("BND", 1, 100), ("JNJ", 1, 100), ("WMT", 1, 100),
        )
        assert pitfalls_by_metric(detect_all_pitfalls(p), "holding_count") == []


class TestMetrics:
    def test_herfindahl_equal_weights(self, sector_map):
        p = make_portfolio(
            ("AAPL", 1, 100), ("JPM", 1, 100), ("XOM", 1, 100), ("BND", 1, 100)
        )
        assert calculate_herfindahl_index(p) == pytest.approx(0.25)

    def test_herfindahl_single_holding(self, sector_map):
        assert calculate_herfindahl_index(make_portfolio(("AAPL", 1, 100))) == 1.0

    def test_herfindahl_empty(self, sector_map):
        assert calculate_herfindahl_index(create_portfolio([])) == 0


class TestSummaryAndRanking:
    def test_summary_critical(self):
        pitfall = analysis.Pitfall("x", "t", "critical", "m", 1, 0, "", "", [])
        assert create_summary([pitfall], {}).startswith("🔴")

    def test_summary_warning_only(self):
        pitfall = analysis.Pitfall("x", "t", "warning", "m", 1, 0, "", "", [])
        assert create_summary([pitfall], {}).startswith("🟡")

    def test_summary_clean(self):
        assert create_summary([], {}).startswith("🟢")

    def test_severity_rank_ordering(self):
        assert severity_rank("critical") < severity_rank("warning") < severity_rank("info")


class TestFullAnalysis:
    def test_demo_portfolio_produces_critical_findings(self, sector_map):
        """The demo sample portfolio must keep producing visible findings."""
        p = make_portfolio(
            ("AAPL", 10, 180), ("MSFT", 6, 410), ("NVDA", 30, 120),
            ("JPM", 12, 195), ("XOM", 15, 110), ("BND", 20, 73),
        )
        result = analyze_portfolio(p)
        assert result.summary.startswith("🔴")
        assert any(pf.severity == "critical" for pf in result.pitfalls)
        assert result.concentration_metrics["largest_position"] == pytest.approx(0.27, abs=0.01)
        # pitfalls sorted most severe first
        ranks = [severity_rank(pf.severity) for pf in result.pitfalls]
        assert ranks == sorted(ranks)

    def test_balanced_portfolio_is_clean(self, sector_map):
        p = make_portfolio(
            ("AAPL", 1, 100), ("JPM", 1, 100), ("XOM", 1, 100),
            ("BND", 1, 100), ("JNJ", 1, 100), ("WMT", 1, 100),
        )
        result = analyze_portfolio(p)
        assert result.pitfalls == []
        assert result.summary.startswith("🟢")
