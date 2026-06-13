"""Tests for sector_updater.fetch_sector_from_finnhub canonical output."""

from unittest.mock import Mock

import sector_updater


class TestFetchSectorFromFinnhub:
    def test_no_api_key_returns_none_false(self, monkeypatch):
        monkeypatch.setattr(sector_updater, "FINNHUB_API_KEY", "")
        sector, success = sector_updater.fetch_sector_from_finnhub("AAPL")
        assert sector is None
        assert success is False

    def test_unknown_finnhub_industry_returns_other(self, monkeypatch):
        monkeypatch.setattr(sector_updater, "FINNHUB_API_KEY", "fake-key")
        mock_resp = Mock(status_code=200)
        mock_resp.json.return_value = {"finnhubIndustry": "Specialty Chemicals"}
        monkeypatch.setattr(
            sector_updater.requests, "get", Mock(return_value=mock_resp)
        )
        sector, success = sector_updater.fetch_sector_from_finnhub("XYZ")
        assert success is True
        assert sector == "Other"  # not "Specialty Chemicals" (old .title() behavior)

    def test_known_alias_maps_to_canonical(self, monkeypatch):
        monkeypatch.setattr(sector_updater, "FINNHUB_API_KEY", "fake-key")
        mock_resp = Mock(status_code=200)
        mock_resp.json.return_value = {"finnhubIndustry": "Semiconductors"}
        monkeypatch.setattr(
            sector_updater.requests, "get", Mock(return_value=mock_resp)
        )
        sector, success = sector_updater.fetch_sector_from_finnhub("NVDA")
        assert sector == "Technology"
        assert success is True

    def test_canonical_industry_passes_through(self, monkeypatch):
        monkeypatch.setattr(sector_updater, "FINNHUB_API_KEY", "fake-key")
        mock_resp = Mock(status_code=200)
        mock_resp.json.return_value = {"finnhubIndustry": "Healthcare"}
        monkeypatch.setattr(
            sector_updater.requests, "get", Mock(return_value=mock_resp)
        )
        sector, success = sector_updater.fetch_sector_from_finnhub("JNJ")
        assert sector == "Healthcare"
        assert success is True

    def test_non_200_response_returns_none_false(self, monkeypatch):
        monkeypatch.setattr(sector_updater, "FINNHUB_API_KEY", "fake-key")
        mock_resp = Mock(status_code=429)
        monkeypatch.setattr(
            sector_updater.requests, "get", Mock(return_value=mock_resp)
        )
        sector, success = sector_updater.fetch_sector_from_finnhub("AAPL")
        assert sector is None
        assert success is False

    def test_network_exception_returns_none_false(self, monkeypatch):
        monkeypatch.setattr(sector_updater, "FINNHUB_API_KEY", "fake-key")
        monkeypatch.setattr(
            sector_updater.requests,
            "get",
            Mock(side_effect=RuntimeError("timeout")),
        )
        sector, success = sector_updater.fetch_sector_from_finnhub("AAPL")
        assert sector is None
        assert success is False
