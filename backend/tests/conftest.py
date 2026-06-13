"""
Shared test fixtures.

Backend modules use flat imports (e.g. `from portfolio import ...`) and
read/write data files relative to the working directory, so:
- the backend directory is added to sys.path for imports
- each test runs in a temp working directory to avoid touching real
  portfolio.json / sector_cache.json files
"""

import os
import sys

import pytest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)


@pytest.fixture(autouse=True)
def isolate_workdir(tmp_path, monkeypatch):
    """Run every test in an empty temp directory."""
    monkeypatch.chdir(tmp_path)
    yield tmp_path


@pytest.fixture
def sector_map(monkeypatch):
    """Small deterministic sector map, independent of sector_map.json."""
    import analysis

    test_map = {
        "AAPL": "Technology",
        "MSFT": "Technology",
        "NVDA": "Technology",
        "JPM": "Financials",
        "XOM": "Energy",
        "BND": "Bonds",
        "JNJ": "Healthcare",
        "WMT": "Consumer",
    }
    monkeypatch.setattr(analysis, "SECTOR_MAP", test_map)
    return test_map


@pytest.fixture
def client():
    """Flask test client."""
    from api import app

    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_module_caches():
    """Reset all module-level in-process caches between tests.

    analysis._sector_cache_mem / _index_decomp_cache_mem bypass the temp
    workdir that isolate_workdir sets up — without this reset a value written
    in test A leaks into test B even though B runs in a different tmp_path.
    """
    yield
    import sys
    mods = sys.modules
    if "analysis" in mods:
        mods["analysis"]._sector_cache_mem = None
        mods["analysis"]._index_decomp_cache_mem = None
    if "finnhub_client" in mods:
        mods["finnhub_client"]._PROFILE_CACHE.clear()
    if "signals" in mods:
        mods["signals"]._EARNINGS_CACHE.clear()
        mods["signals"]._METRIC_PAYLOAD_CACHE.clear()
