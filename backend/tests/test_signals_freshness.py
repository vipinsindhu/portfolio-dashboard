"""Tests for per-timeframe signal-staleness refresh logic."""

from datetime import datetime, timedelta

import signals as signals_module
from signals import generate_signals_if_stale, stale_timeframes


def make_stored(short_age_minutes=None, long_age_minutes=None):
    """Stored signals with one signal per timeframe at the given ages."""
    now = datetime.utcnow()
    signals = []
    if short_age_minutes is not None:
        signals.append({
            "id": "s", "ticker": "BAC", "direction": "buy", "timeframe": "short_term",
            "created_at": (now - timedelta(minutes=short_age_minutes)).isoformat(),
        })
    if long_age_minutes is not None:
        signals.append({
            "id": "l", "ticker": "JNJ", "direction": "buy", "timeframe": "long_term",
            "created_at": (now - timedelta(minutes=long_age_minutes)).isoformat(),
        })
    return {"signals": signals, "generated_at": now.isoformat()}


class TestStaleTimeframes:
    def test_both_fresh(self):
        data = make_stored(short_age_minutes=30, long_age_minutes=30)
        assert stale_timeframes(data) == []

    def test_short_term_goes_stale_after_6h(self):
        data = make_stored(short_age_minutes=400, long_age_minutes=400)
        assert stale_timeframes(data) == ["short_term"]

    def test_long_term_goes_stale_after_24h(self):
        data = make_stored(short_age_minutes=100, long_age_minutes=1500)
        assert stale_timeframes(data) == ["long_term"]

    def test_missing_timeframe_is_stale(self):
        # A failed pass leaves no signals for its timeframe -> retry hourly
        data = make_stored(long_age_minutes=30)
        assert stale_timeframes(data) == ["short_term"]

    def test_empty_store_is_fully_stale(self):
        assert sorted(stale_timeframes({"signals": []})) == ["long_term", "short_term"]

    def test_untagged_legacy_signals_count_as_long_term(self):
        now = datetime.utcnow()
        data = {"signals": [{
            "id": "x", "ticker": "AAPL", "direction": "buy",
            "created_at": now.isoformat(),
        }]}
        assert stale_timeframes(data) == ["short_term"]

    def test_mock_signals_do_not_count_as_fresh(self):
        now = datetime.utcnow()
        data = {"signals": [{
            "id": "m", "ticker": "AAPL", "direction": "buy", "timeframe": "short_term",
            "source": "mock", "created_at": now.isoformat(),
        }]}
        assert sorted(stale_timeframes(data)) == ["long_term", "short_term"]

    def test_unparseable_created_at_ignored(self):
        data = {"signals": [{
            "id": "x", "ticker": "AAPL", "direction": "buy", "timeframe": "long_term",
            "created_at": "not-a-date",
        }]}
        assert sorted(stale_timeframes(data)) == ["long_term", "short_term"]


class TestGenerateSignalsIfStale:
    def test_skips_when_all_fresh(self, monkeypatch):
        monkeypatch.setattr(
            signals_module, "load_signals",
            lambda: make_stored(short_age_minutes=30, long_age_minutes=30),
        )
        called = []
        monkeypatch.setattr(
            signals_module, "auto_generate_signals",
            lambda timeframes: called.append(timeframes) or True,
        )

        assert generate_signals_if_stale() is False
        assert called == []

    def test_regenerates_only_stale_timeframes(self, monkeypatch):
        monkeypatch.setattr(
            signals_module, "load_signals",
            lambda: make_stored(short_age_minutes=400, long_age_minutes=100),
        )
        called = []
        monkeypatch.setattr(
            signals_module, "auto_generate_signals",
            lambda timeframes: called.append(timeframes) or True,
        )

        assert generate_signals_if_stale() is True
        assert called == [["short_term"]]


class TestMockSignalGeneration:
    def test_handles_candidates_without_company_name(self):
        """Regression: bare mock-fundamentals candidates (no company_name)
        crashed signal generation with KeyError, leaving live signals stale."""
        from signals import generate_realistic_mock_signals

        candidates = [
            {"ticker": "ZZZZ", "sector": "Unknown", "current_price": 100},
            {"ticker": "AAPL", "company_name": "Apple Inc", "sector": "Technology",
             "current_price": 205, "pe_ratio": 28.5, "dividend_yield": 0.004,
             "52_week_high": 220},
        ]
        signals = generate_realistic_mock_signals(candidates, count=2)
        assert len(signals) == 2
        assert all(s["rationale"] for s in signals)
        assert "ZZZZ" in signals[0]["rationale"]


class TestAutoGenerateSaves:
    def _run(self, monkeypatch, generated, existing):
        saved = {}
        monkeypatch.setattr(signals_module, "fetch_signal_candidates", lambda: [{"ticker": "AAPL"}])
        monkeypatch.setattr(signals_module, "fetch_macro_context", lambda: {})
        monkeypatch.setattr(
            signals_module, "generate_signals", lambda count=10, candidates=None, macro_data=None: generated
        )
        monkeypatch.setattr(
            signals_module, "generate_short_term_signals", lambda count=10, candidates=None, macro_data=None: []
        )
        monkeypatch.setattr(signals_module, "load_signals", lambda: existing)
        monkeypatch.setattr(signals_module, "save_signals", lambda data: saved.update(data))
        result = signals_module.auto_generate_signals()
        return result, saved

    def test_saves_real_signals(self, monkeypatch):
        real = [{"id": "a", "ticker": "AAPL", "direction": "buy"}]
        result, saved = self._run(monkeypatch, real, {"signals": []})
        assert result is True
        assert saved["signals"] == real
        assert saved["generated_at"]

    def test_mock_signals_do_not_overwrite_real_ones(self, monkeypatch):
        mock = [{"id": "m", "ticker": "AAPL", "direction": "buy", "source": "mock"}]
        existing = {"signals": [{"id": "real", "ticker": "MSFT", "direction": "hold"}]}
        result, saved = self._run(monkeypatch, mock, existing)
        assert result is False
        assert saved == {}

    def test_mock_signals_saved_when_store_empty(self, monkeypatch):
        mock = [{"id": "m", "ticker": "AAPL", "direction": "buy", "source": "mock"}]
        result, saved = self._run(monkeypatch, mock, {"signals": []})
        assert result is True
        assert saved["signals"] == mock

    def test_generation_failure_returns_false(self, monkeypatch):
        result, saved = self._run(monkeypatch, [], {"signals": []})
        assert result is False
        assert saved == {}

    def test_failed_short_term_pass_keeps_existing_and_saves_real_long_term(self, monkeypatch):
        """A rate-limited pass must not discard the other pass's success."""
        new_long = [{"id": "L2", "ticker": "AAPL", "direction": "buy", "timeframe": "long_term"}]
        mock_short = [{"id": "S2", "ticker": "BAC", "direction": "buy", "timeframe": "short_term", "source": "mock"}]
        existing = {"signals": [
            {"id": "L1", "ticker": "MSFT", "direction": "hold", "timeframe": "long_term"},
            {"id": "S1", "ticker": "JPM", "direction": "buy", "timeframe": "short_term"},
        ]}

        saved = {}
        monkeypatch.setattr(signals_module, "fetch_signal_candidates", lambda: [{"ticker": "AAPL"}])
        monkeypatch.setattr(signals_module, "fetch_macro_context", lambda: {})
        monkeypatch.setattr(
            signals_module, "generate_signals", lambda count=10, candidates=None, macro_data=None: new_long
        )
        monkeypatch.setattr(
            signals_module, "generate_short_term_signals", lambda count=10, candidates=None, macro_data=None: mock_short
        )
        monkeypatch.setattr(signals_module, "load_signals", lambda: existing)
        monkeypatch.setattr(signals_module, "save_signals", lambda data: saved.update(data))

        assert signals_module.auto_generate_signals() is True
        ids = [s["id"] for s in saved["signals"]]
        assert ids == ["L2", "S1"]  # fresh long-term, kept short-term, no mocks


class TestAccuracySkipsMockSignals:
    def test_mock_signals_not_captured(self):
        from accuracy import merge_signals_into_history

        history = {"signals": []}
        added = merge_signals_into_history(history, [
            {"id": "r1", "ticker": "AAPL", "direction": "buy"},
            {"id": "m1", "ticker": "MSFT", "direction": "buy", "source": "mock"},
        ], "t")
        assert added == 1
        assert history["signals"][0]["id"] == "r1"
