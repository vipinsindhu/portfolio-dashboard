"""Tests for in-process caching contracts in signals.py.

Guards against cache-poisoning regressions: non-200 HTTP responses must
not write a None entry into _EARNINGS_CACHE or _METRIC_PAYLOAD_CACHE,
which would suppress the real value for the full TTL window.
"""

from unittest.mock import Mock

import pytest
import signals as signals_module


@pytest.fixture(autouse=True)
def clear_signals_caches():
    signals_module._EARNINGS_CACHE.clear()
    signals_module._METRIC_PAYLOAD_CACHE.clear()
    yield
    signals_module._EARNINGS_CACHE.clear()
    signals_module._METRIC_PAYLOAD_CACHE.clear()


class TestEarningsCacheContract:
    def test_non_200_earnings_response_does_not_cache(self, monkeypatch):
        monkeypatch.setattr(signals_module, "FINNHUB_API_KEY", "fake-key")
        metric_resp = Mock(status_code=200)
        metric_resp.json.return_value = {"metric": {}}
        earnings_resp = Mock(status_code=429)

        def fake_get(url, **kwargs):
            if "calendar/earnings" in url:
                return earnings_resp
            return metric_resp

        monkeypatch.setattr(signals_module.requests, "get", fake_get)
        signals_module.fetch_short_term_metrics("AAPL")
        assert "AAPL" not in signals_module._EARNINGS_CACHE

    def test_200_earnings_response_caches(self, monkeypatch):
        monkeypatch.setattr(signals_module, "FINNHUB_API_KEY", "fake-key")
        metric_resp = Mock(status_code=200)
        metric_resp.json.return_value = {"metric": {}}
        earnings_resp = Mock(status_code=200)
        earnings_resp.json.return_value = {"earningsCalendar": []}

        def fake_get(url, **kwargs):
            if "calendar/earnings" in url:
                return earnings_resp
            return metric_resp

        monkeypatch.setattr(signals_module.requests, "get", fake_get)
        signals_module.fetch_short_term_metrics("AAPL")
        assert "AAPL" in signals_module._EARNINGS_CACHE

    def test_no_api_key_skips_all_cache_writes(self, monkeypatch):
        monkeypatch.setattr(signals_module, "FINNHUB_API_KEY", "")
        signals_module.fetch_short_term_metrics("AAPL")
        assert "AAPL" not in signals_module._EARNINGS_CACHE
        assert "AAPL" not in signals_module._METRIC_PAYLOAD_CACHE


class TestMetricPayloadCacheContract:
    def test_non_200_metric_response_does_not_cache(self, monkeypatch):
        monkeypatch.setattr(signals_module, "FINNHUB_API_KEY", "fake-key")
        mock_resp = Mock(status_code=503)
        monkeypatch.setattr(signals_module.requests, "get", Mock(return_value=mock_resp))
        result = signals_module.fetch_metric_payload("AAPL")
        assert result is None
        assert "AAPL" not in signals_module._METRIC_PAYLOAD_CACHE

    def test_200_metric_response_caches(self, monkeypatch):
        monkeypatch.setattr(signals_module, "FINNHUB_API_KEY", "fake-key")
        mock_resp = Mock(status_code=200)
        mock_resp.json.return_value = {"metric": {"peBasicExclExtraTTM": 25.0}}
        monkeypatch.setattr(signals_module.requests, "get", Mock(return_value=mock_resp))
        signals_module.fetch_metric_payload("AAPL")
        assert "AAPL" in signals_module._METRIC_PAYLOAD_CACHE
