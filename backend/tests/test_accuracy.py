"""Unit tests for signal accuracy tracking (pure logic, no network)."""

from datetime import datetime, timedelta

import pytest

from accuracy import (
    EVALUATION_RETRY_DAYS,
    EVALUATION_WINDOW_DAYS,
    classify_outcome,
    compute_accuracy_stats,
    evaluate_pending,
    merge_signals_into_history,
)

NOW = datetime(2026, 6, 11, 12, 0, 0)


def make_signal(sid="NVDA_1", ticker="NVDA", direction="buy", **extra):
    return {"id": sid, "ticker": ticker, "direction": direction,
            "confidence": 8, "sector": "Technology",
            "created_at": "2026-06-01T00:00:00", **extra}


def make_entry(days_old, direction="buy", result=None, sid=None, **extra):
    created = NOW - timedelta(days=days_old)
    return {
        "id": sid or f"{direction}_{days_old}",
        "ticker": "NVDA",
        "direction": direction,
        "confidence": 8,
        "sector": "Technology",
        "created_at": created.isoformat(),
        "captured_at": created.isoformat(),
        "result": result,
        "return_pct": None,
        "evaluated_at": None,
        **extra,
    }


class TestClassifyOutcome:
    @pytest.mark.parametrize("direction,return_pct,expected", [
        ("buy", 5.0, "win"),
        ("buy", -3.0, "loss"),
        ("buy", 0.0, "loss"),
        ("avoid", -5.0, "win"),
        ("avoid", 3.0, "loss"),
        ("hold", 2.0, "win"),
        ("hold", -4.9, "win"),
        ("hold", 5.1, "loss"),
        ("hold", -8.0, "loss"),
    ])
    def test_rules(self, direction, return_pct, expected):
        assert classify_outcome(direction, return_pct) == expected

    def test_unknown_direction(self):
        assert classify_outcome("short", 5.0) is None


class TestMerge:
    def test_adds_new_signals(self):
        history = {"signals": []}
        added = merge_signals_into_history(history, [make_signal()], "2026-06-11T00:00:00")
        assert added == 1
        entry = history["signals"][0]
        assert entry["result"] is None
        assert entry["captured_at"] == "2026-06-11T00:00:00"

    def test_dedupes_by_id(self):
        history = {"signals": []}
        merge_signals_into_history(history, [make_signal()], "t1")
        added = merge_signals_into_history(
            history, [make_signal(), make_signal(sid="AAPL_1", ticker="AAPL")], "t2"
        )
        assert added == 1
        assert len(history["signals"]) == 2

    def test_skips_malformed(self):
        history = {"signals": []}
        added = merge_signals_into_history(
            history,
            [{"id": None, "ticker": "X", "direction": "buy"},
             {"id": "ok", "ticker": "", "direction": "buy"},
             {"id": "ok2", "ticker": "X", "direction": None}],
            "t",
        )
        assert added == 0


class TestEvaluatePending:
    def test_evaluates_due_entry(self):
        history = {"signals": [make_entry(days_old=35, direction="buy")]}
        count = evaluate_pending(history, lambda t, s, e: (100.0, 110.0), now=NOW)
        assert count == 1
        entry = history["signals"][0]
        assert entry["result"] == "win"
        assert entry["return_pct"] == 10.0
        assert entry["evaluated_at"] == NOW.isoformat()

    def test_skips_not_yet_due(self):
        history = {"signals": [make_entry(days_old=EVALUATION_WINDOW_DAYS - 1)]}
        count = evaluate_pending(history, lambda t, s, e: (100.0, 110.0), now=NOW)
        assert count == 0
        assert history["signals"][0]["result"] is None

    def test_skips_already_evaluated(self):
        history = {"signals": [make_entry(days_old=40, result="win")]}
        calls = []
        evaluate_pending(history, lambda t, s, e: calls.append(t), now=NOW)
        assert calls == []

    def test_fetch_failure_leaves_pending_for_retry(self):
        history = {"signals": [make_entry(days_old=35)]}
        count = evaluate_pending(history, lambda t, s, e: None, now=NOW)
        assert count == 0
        assert history["signals"][0]["result"] is None

    def test_fetch_failure_gives_up_eventually(self):
        days_old = EVALUATION_WINDOW_DAYS + EVALUATION_RETRY_DAYS + 5
        history = {"signals": [make_entry(days_old=days_old)]}
        evaluate_pending(history, lambda t, s, e: None, now=NOW)
        assert history["signals"][0]["result"] == "unavailable"

    def test_fetcher_exception_handled(self):
        def boom(t, s, e):
            raise RuntimeError("api down")
        history = {"signals": [make_entry(days_old=35)]}
        count = evaluate_pending(history, boom, now=NOW)
        assert count == 0
        assert history["signals"][0]["result"] is None

    def test_avoid_win_on_price_drop(self):
        history = {"signals": [make_entry(days_old=35, direction="avoid")]}
        evaluate_pending(history, lambda t, s, e: (100.0, 90.0), now=NOW)
        assert history["signals"][0]["result"] == "win"
        assert history["signals"][0]["return_pct"] == -10.0


class TestStats:
    def test_empty_history(self):
        stats = compute_accuracy_stats({"signals": []}, now=NOW)
        assert stats["overall"]["win_rate"] is None
        assert stats["pending"] == 0
        assert stats["tracking_since"] is None

    def test_overall_and_by_direction(self):
        history = {"signals": [
            make_entry(40, "buy", result="win", sid="a", evaluated_at=NOW.isoformat()),
            make_entry(41, "buy", result="loss", sid="b", evaluated_at=NOW.isoformat()),
            make_entry(42, "avoid", result="win", sid="c", evaluated_at=NOW.isoformat()),
            make_entry(5, "buy", sid="d"),  # pending
        ]}
        stats = compute_accuracy_stats(history, now=NOW)
        assert stats["overall"] == {"evaluated": 3, "wins": 2, "win_rate": 66.7}
        assert stats["by_direction"]["buy"]["win_rate"] == 50.0
        assert stats["by_direction"]["avoid"]["win_rate"] == 100.0
        assert stats["pending"] == 1
        assert stats["tracked_total"] == 4

    def test_recent_window_excludes_old_evaluations(self):
        old_eval = (NOW - timedelta(weeks=6)).isoformat()
        history = {"signals": [
            make_entry(80, "buy", result="loss", sid="old", evaluated_at=old_eval),
            make_entry(35, "buy", result="win", sid="new", evaluated_at=NOW.isoformat()),
        ]}
        stats = compute_accuracy_stats(history, now=NOW, window_weeks=4)
        assert stats["recent"] == {"evaluated": 1, "wins": 1, "win_rate": 100.0}
        assert stats["overall"]["evaluated"] == 2

    def test_unavailable_not_counted(self):
        history = {"signals": [
            make_entry(70, "buy", result="unavailable", sid="x"),
            make_entry(40, "buy", result="win", sid="y", evaluated_at=NOW.isoformat()),
        ]}
        stats = compute_accuracy_stats(history, now=NOW)
        assert stats["overall"]["evaluated"] == 1
        assert stats["overall"]["win_rate"] == 100.0
