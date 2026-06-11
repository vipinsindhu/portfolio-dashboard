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
