"""Tests for normalize_sector canonical sector mapping."""

import pytest
from sector_config import normalize_sector, CANONICAL_SECTORS


class TestNormalizeSector:
    def test_canonical_string_passes_through(self):
        for sector in CANONICAL_SECTORS:
            assert normalize_sector(sector) == sector

    def test_none_returns_other(self):
        assert normalize_sector(None) == "Other"

    def test_empty_string_returns_other(self):
        assert normalize_sector("") == "Other"

    def test_unknown_finnhub_string_returns_other(self):
        # Prior behavior was title-cased passthrough; new contract is "Other".
        assert normalize_sector("Specialty Chemicals") == "Other"
        assert normalize_sector("Diversified Industrials") == "Other"

    def test_known_alias_semiconductors_maps_to_technology(self):
        assert normalize_sector("Semiconductors") == "Technology"

    def test_known_alias_financial_services_maps_to_financials(self):
        assert normalize_sector("financial services") == "Financials"

    def test_alias_lookup_is_case_insensitive(self):
        assert normalize_sector("SEMICONDUCTORS") == "Technology"
        assert normalize_sector("Oil & Gas") == "Energy"

    def test_known_alias_oil_and_gas_maps_to_energy(self):
        assert normalize_sector("Oil & Gas") == "Energy"

    def test_known_alias_reits_maps_to_real_estate(self):
        assert normalize_sector("REITs") == "Real Estate"

    def test_whitespace_only_returns_other(self):
        # normalize_sector checks `if not raw`, and whitespace-only is truthy.
        # No alias exists for whitespace, so it falls through to "Other".
        assert normalize_sector("   ") == "Other"
