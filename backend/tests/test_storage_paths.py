"""Tests for DATA_DIR-aware data file path resolution."""

import json
import os

from storage_paths import data_path


class TestDataPath:
    def test_no_data_dir_returns_filename_unchanged(self, monkeypatch):
        monkeypatch.delenv("DATA_DIR", raising=False)
        assert data_path("signals.json") == "signals.json"

    def test_resolves_into_data_dir(self, monkeypatch, tmp_path):
        volume = tmp_path / "volume"
        volume.mkdir()
        monkeypatch.setenv("DATA_DIR", str(volume))

        assert data_path("signals.json") == os.path.join(str(volume), "signals.json")

    def test_seeds_empty_volume_from_committed_copy(self, monkeypatch, tmp_path):
        volume = tmp_path / "volume"
        monkeypatch.setenv("DATA_DIR", str(volume))
        # Committed copy in the working directory (conftest chdirs to tmp)
        with open("signals.json", "w") as f:
            json.dump({"signals": [{"ticker": "AAPL"}]}, f)

        target = data_path("signals.json")

        assert target == os.path.join(str(volume), "signals.json")
        with open(target) as f:
            assert json.load(f)["signals"][0]["ticker"] == "AAPL"

    def test_existing_volume_file_not_overwritten(self, monkeypatch, tmp_path):
        volume = tmp_path / "volume"
        volume.mkdir()
        (volume / "signals.json").write_text('{"signals": [{"ticker": "VOLUME"}]}')
        monkeypatch.setenv("DATA_DIR", str(volume))
        with open("signals.json", "w") as f:
            json.dump({"signals": [{"ticker": "COMMITTED"}]}, f)

        target = data_path("signals.json")

        with open(target) as f:
            assert json.load(f)["signals"][0]["ticker"] == "VOLUME"
