"""Tests for the shared Finnhub profile cache in finnhub_client.py."""

from unittest.mock import Mock

import pytest


@pytest.fixture(autouse=True)
def clear_cache():
    import finnhub_client
    finnhub_client._PROFILE_CACHE.clear()
    yield
    finnhub_client._PROFILE_CACHE.clear()


class TestFetchProfile:
    def test_network_exception_does_not_cache(self, monkeypatch):
        import finnhub_client
        monkeypatch.setattr(finnhub_client, "FINNHUB_API_KEY", "fake-key")
        monkeypatch.setattr(
            finnhub_client.requests,
            "get",
            Mock(side_effect=RuntimeError("network down")),
        )
        finnhub_client.fetch_profile("AAPL")
        assert "AAPL" not in finnhub_client._PROFILE_CACHE

    def test_200_response_caches_with_canonical_sector(self, monkeypatch):
        import finnhub_client
        monkeypatch.setattr(finnhub_client, "FINNHUB_API_KEY", "fake-key")
        mock_resp = Mock(status_code=200)
        mock_resp.json.return_value = {
            "finnhubIndustry": "Semiconductors",
            "marketCapitalization": 3_000_000,
            "name": "Apple Inc",
        }
        monkeypatch.setattr(finnhub_client.requests, "get", Mock(return_value=mock_resp))
        result = finnhub_client.fetch_profile("AAPL")
        assert "AAPL" in finnhub_client._PROFILE_CACHE
        assert result["sector"] == "Technology"  # alias resolved
        assert result["market_cap"] == 3_000_000_000_000
        assert result["company_name"] == "Apple Inc"

    def test_non_200_response_does_not_cache(self, monkeypatch):
        import finnhub_client
        monkeypatch.setattr(finnhub_client, "FINNHUB_API_KEY", "fake-key")
        mock_resp = Mock(status_code=429)
        monkeypatch.setattr(finnhub_client.requests, "get", Mock(return_value=mock_resp))
        result = finnhub_client.fetch_profile("AAPL")
        assert "AAPL" not in finnhub_client._PROFILE_CACHE
        assert result == {"sector": "", "market_cap": 0, "company_name": ""}

    def test_no_api_key_skips_network_and_returns_empty(self, monkeypatch):
        import finnhub_client
        monkeypatch.setattr(finnhub_client, "FINNHUB_API_KEY", "")
        network_calls = []
        monkeypatch.setattr(
            finnhub_client.requests,
            "get",
            lambda *a, **kw: network_calls.append(1),
        )
        result = finnhub_client.fetch_profile("AAPL")
        assert network_calls == []
        assert result == {"sector": "", "market_cap": 0, "company_name": ""}

    def test_cached_result_skips_network_on_second_call(self, monkeypatch):
        import finnhub_client
        monkeypatch.setattr(finnhub_client, "FINNHUB_API_KEY", "fake-key")
        mock_resp = Mock(status_code=200)
        mock_resp.json.return_value = {
            "finnhubIndustry": "Technology",
            "marketCapitalization": 1_000,
            "name": "FakeCo",
        }
        get_mock = Mock(return_value=mock_resp)
        monkeypatch.setattr(finnhub_client.requests, "get", get_mock)
        finnhub_client.fetch_profile("AAPL")
        finnhub_client.fetch_profile("AAPL")
        assert get_mock.call_count == 1  # second call served from cache
