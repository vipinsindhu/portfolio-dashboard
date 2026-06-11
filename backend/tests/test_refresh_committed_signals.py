"""Tests for the daily committed-signals refresh decision logic."""

from refresh_committed_signals import should_refresh


REAL = [{"ticker": "AAPL", "direction": "buy"}]


class TestShouldRefresh:
    def test_refreshes_with_newer_real_signals(self):
        existing = {"generated_at": "2026-06-09T03:20:00"}
        refresh, _ = should_refresh(REAL, "2026-06-11T18:00:00", existing)
        assert refresh is True

    def test_skips_empty_response(self):
        refresh, reason = should_refresh([], "2026-06-11T18:00:00", None)
        assert refresh is False
        assert "no signals" in reason

    def test_skips_missing_timestamp(self):
        refresh, _ = should_refresh(REAL, None, None)
        assert refresh is False

    def test_never_commits_mock_signals(self):
        mock = [{"ticker": "AAPL", "direction": "buy", "source": "mock"}]
        refresh, reason = should_refresh(mock, "2026-06-11T18:00:00", None)
        assert refresh is False
        assert "mock" in reason

    def test_never_regresses_to_older_data(self):
        existing = {"generated_at": "2026-06-12T00:00:00"}
        refresh, _ = should_refresh(REAL, "2026-06-11T18:00:00", existing)
        assert refresh is False

    def test_refreshes_when_no_committed_copy(self):
        refresh, _ = should_refresh(REAL, "2026-06-11T18:00:00", None)
        assert refresh is True
