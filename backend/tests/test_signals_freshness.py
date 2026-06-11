"""Tests for startup signal-staleness refresh logic."""

from datetime import datetime, timedelta

import signals as signals_module
from signals import generate_signals_if_stale


def set_stored_signals(monkeypatch, generated_at):
    monkeypatch.setattr(
        signals_module, "load_signals",
        lambda: {"signals": [], "generated_at": generated_at},
    )


class TestGenerateSignalsIfStale:
    def test_skips_when_fresh(self, monkeypatch):
        set_stored_signals(monkeypatch, datetime.utcnow().isoformat())
        called = []
        monkeypatch.setattr(signals_module, "auto_generate_signals", lambda: called.append(1) or True)

        assert generate_signals_if_stale(max_age_minutes=60) is False
        assert called == []

    def test_regenerates_when_stale(self, monkeypatch):
        stale = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        set_stored_signals(monkeypatch, stale)
        called = []
        monkeypatch.setattr(signals_module, "auto_generate_signals", lambda: called.append(1) or True)

        assert generate_signals_if_stale(max_age_minutes=60) is True
        assert called == [1]

    def test_regenerates_when_no_timestamp(self, monkeypatch):
        set_stored_signals(monkeypatch, None)
        called = []
        monkeypatch.setattr(signals_module, "auto_generate_signals", lambda: called.append(1) or True)

        generate_signals_if_stale()
        assert called == [1]

    def test_regenerates_when_timestamp_unparseable(self, monkeypatch):
        set_stored_signals(monkeypatch, "not-a-date")
        called = []
        monkeypatch.setattr(signals_module, "auto_generate_signals", lambda: called.append(1) or True)

        generate_signals_if_stale()
        assert called == [1]

    def test_respects_custom_max_age(self, monkeypatch):
        thirty_min_old = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
        set_stored_signals(monkeypatch, thirty_min_old)
        called = []
        monkeypatch.setattr(signals_module, "auto_generate_signals", lambda: called.append(1) or True)

        assert generate_signals_if_stale(max_age_minutes=15) is True
        assert called == [1]


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
        monkeypatch.setattr(
            signals_module, "generate_signals", lambda count=10, candidates=None: generated
        )
        monkeypatch.setattr(
            signals_module, "generate_short_term_signals", lambda count=10, candidates=None: []
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
