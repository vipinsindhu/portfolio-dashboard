"""API endpoint tests using the Flask test client (no network calls)."""

import io
import json

SAMPLE_CSV = (
    "Symbol,Quantity,PurchasePrice\n"
    "AAPL,10,180\nMSFT,6,410\nNVDA,30,120\n"
    "JPM,12,195\nXOM,15,110\nBND,20,73\n"
)


def upload_sample(client):
    return client.post(
        "/api/portfolio/upload",
        data={"file": (io.BytesIO(SAMPLE_CSV.encode()), "sample.csv")},
        content_type="multipart/form-data",
    )


class TestHealth:
    def test_health_endpoint(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200


class TestFrontendCaching:
    def test_index_html_always_revalidates(self, client):
        response = client.get("/")
        if response.status_code == 200:  # dist present in this checkout
            assert response.headers.get("Cache-Control") == "no-cache"


class TestPortfolioUpload:
    def test_valid_csv_returns_201_with_holdings(self, client):
        response = upload_sample(client)
        assert response.status_code == 201
        data = response.get_json()
        assert data["holdings"] == 6
        symbols = [h["symbol"] for h in data["holdings_list"]]
        assert "NVDA" in symbols

    def test_upload_replaces_existing_portfolio(self, client):
        upload_sample(client)
        response = client.post(
            "/api/portfolio/upload",
            data={"file": (io.BytesIO(b"Symbol,Quantity,Price\nVTI,5,250\n"), "p.csv")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 201
        data = client.get("/api/portfolio").get_json()
        symbols = [h["symbol"] for h in data["portfolio"]["holdings"]]
        assert symbols == ["VTI"]

    def test_missing_file_returns_400(self, client):
        response = client.post("/api/portfolio/upload", data={})
        assert response.status_code == 400

    def test_invalid_csv_returns_error(self, client):
        response = client.post(
            "/api/portfolio/upload",
            data={"file": (io.BytesIO(b"Ticker,Amount\nAAPL,10\n"), "bad.csv")},
            content_type="multipart/form-data",
        )
        assert response.status_code in (400, 500)
        assert "error" in response.get_json()


class TestAddHolding:
    def test_add_holding_creates_portfolio(self, client):
        response = client.post(
            "/api/portfolio/add-holding",
            json={"symbol": "aapl", "quantity": 10, "purchase_price": 150},
        )
        assert response.status_code == 201
        assert response.get_json()["holding"]["symbol"] == "AAPL"

    def test_missing_fields_returns_400(self, client):
        response = client.post(
            "/api/portfolio/add-holding", json={"symbol": "AAPL"}
        )
        assert response.status_code == 400


class TestPortfolioAnalysis:
    def test_analysis_without_portfolio_returns_400(self, client):
        response = client.get("/api/portfolio/analysis")
        assert response.status_code == 400

    def test_analysis_of_demo_portfolio(self, client):
        upload_sample(client)
        response = client.get("/api/portfolio/analysis")
        assert response.status_code == 200
        data = response.get_json()

        assert data["status"] == "success"
        assert data["holding_count"] == 6
        # demo portfolio must keep producing findings (NVDA ~27%)
        assert any(p["severity"] == "critical" for p in data["pitfalls"])
        assert data["concentration_metrics"]["largest_position"] > 0.20
        assert data["summary"].startswith("🔴")

    def test_analysis_response_shape(self, client):
        upload_sample(client)
        data = client.get("/api/portfolio/analysis").get_json()
        for key in (
            "pitfalls", "risk_metrics", "sector_allocation",
            "concentration_metrics", "recommendations", "summary",
        ):
            assert key in data, f"missing key: {key}"


def write_signals_file(tmp_path, signals):
    (tmp_path / "signals.json").write_text(
        json.dumps({"signals": signals, "generated_at": "2026-06-11T00:00:00"})
    )


SAMPLE_SIGNALS = [
    {
        "id": "AAPL_1", "ticker": "AAPL", "direction": "buy", "confidence": 9,
        "rationale": "test", "sector": "Technology",
    },
    {
        "id": "WMT_1", "ticker": "WMT", "direction": "buy", "confidence": 8,
        "rationale": "test", "sector": "Consumer",
    },
    {
        "id": "XOM_1", "ticker": "XOM", "direction": "avoid", "confidence": 7,
        "rationale": "test", "sector": "Energy",
    },
]


class TestSignalEndpointRecommendations:
    def test_short_term_includes_recommendations_with_portfolio(
        self, client, isolate_workdir
    ):
        write_signals_file(isolate_workdir, SAMPLE_SIGNALS)
        upload_sample(client)

        data = client.get("/api/signals/short-term").get_json()

        assert "recommendations" in data
        recs = data["recommendations"]
        # AAPL and XOM are owned (sample portfolio); WMT is not.
        add_tickers = {s["ticker"] for s in recs["add"]}
        sell_tickers = {s["ticker"] for s in recs["sell_reduce"]}
        hold_tickers = {s["ticker"] for s in recs["hold"]}
        assert "WMT" in add_tickers
        assert add_tickers.isdisjoint({"AAPL", "XOM"})
        assert sell_tickers == {"XOM"}
        assert "AAPL" in hold_tickers

    def test_long_term_includes_recommendations_with_portfolio(
        self, client, isolate_workdir
    ):
        write_signals_file(isolate_workdir, SAMPLE_SIGNALS)
        upload_sample(client)

        data = client.get("/api/signals/long-term").get_json()

        assert "recommendations" in data
        assert {s["ticker"] for s in data["recommendations"]["sell_reduce"]} == {"XOM"}


TAGGED_SIGNALS = [
    {
        "id": "AAPL_lt", "ticker": "AAPL", "direction": "buy", "confidence": 9,
        "rationale": "test", "sector": "Technology", "timeframe": "long_term",
    },
    {
        "id": "BAC_st", "ticker": "BAC", "direction": "buy", "confidence": 8,
        "rationale": "test", "sector": "Financials", "timeframe": "short_term",
    },
    {
        "id": "NVDA_st", "ticker": "NVDA", "direction": "avoid", "confidence": 7,
        "rationale": "test", "sector": "Technology", "timeframe": "short_term",
    },
]


SAMPLE_HISTORY = {
    "signals": [
        {
            "id": "AAPL_old", "ticker": "AAPL", "direction": "buy", "confidence": 8,
            "sector": "Technology", "timeframe": "short_term",
            "created_at": "2026-05-01T00:00:00", "captured_at": "2026-05-01T00:00:00",
            "result": "win", "return_pct": 6.2, "evaluated_at": "2026-06-01T00:00:00",
        },
        {
            "id": "XOM_old", "ticker": "XOM", "direction": "avoid", "confidence": 7,
            "sector": "Energy", "timeframe": "long_term",
            "created_at": "2026-03-01T00:00:00", "captured_at": "2026-03-01T00:00:00",
            "result": "loss", "return_pct": 4.0, "benchmark_return_pct": 2.0,
            "evaluated_at": "2026-06-01T00:00:00",
        },
        {
            "id": "JNJ_new", "ticker": "JNJ", "direction": "hold", "confidence": 6,
            "sector": "Healthcare", "timeframe": "short_term",
            "created_at": "2026-06-10T00:00:00", "captured_at": "2026-06-10T00:00:00",
            "result": None, "return_pct": None, "evaluated_at": None,
        },
    ],
    "updated_at": "2026-06-11T00:00:00",
}


class TestSignalHistory:
    def write_history(self, tmp_path):
        (tmp_path / "signal_history.json").write_text(json.dumps(SAMPLE_HISTORY))

    def test_returns_entries_newest_first_with_stats(self, client, isolate_workdir):
        self.write_history(isolate_workdir)

        data = client.get("/api/signals/history").get_json()

        assert [e["id"] for e in data["entries"]] == ["JNJ_new", "AAPL_old", "XOM_old"]
        assert data["total"] == 3
        assert data["stats"]["overall"]["evaluated"] == 2

    def test_filters_by_result_pending(self, client, isolate_workdir):
        self.write_history(isolate_workdir)

        data = client.get("/api/signals/history?result=pending").get_json()

        assert [e["id"] for e in data["entries"]] == ["JNJ_new"]

    def test_filters_by_timeframe_and_direction(self, client, isolate_workdir):
        self.write_history(isolate_workdir)

        data = client.get("/api/signals/history?timeframe=long_term").get_json()
        assert [e["id"] for e in data["entries"]] == ["XOM_old"]

        data = client.get("/api/signals/history?direction=buy").get_json()
        assert [e["id"] for e in data["entries"]] == ["AAPL_old"]

    def test_empty_history_is_not_an_error(self, client, isolate_workdir):
        response = client.get("/api/signals/history")
        assert response.status_code == 200
        assert response.get_json()["entries"] == []


class TestTimeframeSeparation:
    def test_short_term_endpoint_serves_only_short_term_signals(self, client, isolate_workdir):
        write_signals_file(isolate_workdir, TAGGED_SIGNALS)

        data = client.get("/api/signals/short-term").get_json()

        tickers = {s["ticker"] for s in data["signals"]}
        assert tickers == {"BAC", "NVDA"}

    def test_long_term_endpoint_excludes_short_term_signals(self, client, isolate_workdir):
        write_signals_file(isolate_workdir, TAGGED_SIGNALS)

        data = client.get("/api/signals/long-term").get_json()

        tickers = {s["ticker"] for s in data["signals"]}
        assert tickers == {"AAPL"}

    def test_short_term_endpoint_falls_back_to_untagged_pool(self, client, isolate_workdir):
        # Legacy stores have no timeframe tags; the tab must not go empty
        write_signals_file(isolate_workdir, SAMPLE_SIGNALS)

        data = client.get("/api/signals/short-term").get_json()

        assert {s["ticker"] for s in data["signals"]} == {"AAPL", "WMT", "XOM"}


class TestSignalDetail:
    def test_returns_signal_by_id(self, client, isolate_workdir):
        write_signals_file(isolate_workdir, SAMPLE_SIGNALS)

        response = client.get("/api/signals/AAPL_1")

        assert response.status_code == 200
        assert response.get_json()["ticker"] == "AAPL"

    def test_id_with_timestamp_colons_resolves(self, client, isolate_workdir):
        # Real ids look like "AAPL_2026-06-12T10:00:00.123456"
        signal = dict(SAMPLE_SIGNALS[0], id="AAPL_2026-06-12T10:00:00.123456")
        write_signals_file(isolate_workdir, [signal])

        response = client.get("/api/signals/AAPL_2026-06-12T10:00:00.123456")

        assert response.status_code == 200
        assert response.get_json()["ticker"] == "AAPL"

    def test_unknown_id_and_reserved_names_return_404(self, client, isolate_workdir):
        write_signals_file(isolate_workdir, SAMPLE_SIGNALS)

        assert client.get("/api/signals/NOPE_1").status_code == 404
        assert client.get("/api/signals/generate").status_code == 404


class TestTimeframeSchemaFields:
    def test_new_display_fields_pass_through_endpoints(self, client, isolate_workdir):
        # Vocabulary labels and timeframe-specific fields must reach the UI
        write_signals_file(isolate_workdir, [
            dict(TAGGED_SIGNALS[0], label="Accumulate",
                 moat="Brand", what_to_watch="Revenue growth",
                 revenue_growth_5y_pct=9.5, net_margin_pct=18.2),
            dict(TAGGED_SIGNALS[1], label="Dip Buy",
                 catalyst="Down 12% in 3 months", expected_window="1-3 months",
                 invalidation="If it keeps falling."),
        ])

        long_signal = client.get("/api/signals/long-term").get_json()["signals"][0]
        assert long_signal["label"] == "Accumulate"
        assert long_signal["moat"] == "Brand"
        assert long_signal["what_to_watch"] == "Revenue growth"
        assert long_signal["revenue_growth_5y_pct"] == 9.5

        short_signal = client.get("/api/signals/short-term").get_json()["signals"][0]
        assert short_signal["label"] == "Dip Buy"
        assert short_signal["catalyst"] == "Down 12% in 3 months"
        assert short_signal["expected_window"] == "1-3 months"
        assert short_signal["invalidation"] == "If it keeps falling."


class TestStats:
    def test_returns_ticker_and_sector_counts(self, client, isolate_workdir):
        write_signals_file(isolate_workdir, SAMPLE_SIGNALS)

        data = client.get("/api/stats").get_json()

        assert data["ticker_count"] == 3
        assert data["sector_count"] == 3  # Technology, Consumer, Energy

    def test_other_sector_excluded_from_count(self, client, isolate_workdir):
        signals = SAMPLE_SIGNALS + [{
            "id": "FOO_1", "ticker": "FOO", "direction": "hold", "confidence": 7,
            "rationale": "test", "sector": "Other",
        }]
        write_signals_file(isolate_workdir, signals)

        data = client.get("/api/stats").get_json()

        assert data["ticker_count"] == 4   # FOO counted as a ticker
        assert data["sector_count"] == 3   # Other not counted as a sector

    def test_deduplicates_tickers_and_sectors(self, client, isolate_workdir):
        signals = SAMPLE_SIGNALS + [{
            "id": "AAPL_2", "ticker": "AAPL", "direction": "hold", "confidence": 6,
            "rationale": "test", "sector": "Technology",
        }]
        write_signals_file(isolate_workdir, signals)

        data = client.get("/api/stats").get_json()

        assert data["ticker_count"] == 3   # AAPL still counted once
        assert data["sector_count"] == 3

    def test_empty_store_returns_zeros(self, client, isolate_workdir):
        data = client.get("/api/stats").get_json()

        assert data["ticker_count"] == 0
        assert data["sector_count"] == 0


class TestGenerateEndpoint:
    def test_returns_202_and_runs_generation_in_background(self, client, monkeypatch):
        # Generation takes minutes; the endpoint must not run it in-request
        # (the worker's 30s timeout used to 500 every call)
        import threading

        import api as api_module

        done = threading.Event()
        monkeypatch.setattr(api_module, "auto_generate_signals", lambda: done.set())

        response = client.post("/api/signals/generate")

        assert response.status_code == 202
        assert response.get_json()["status"] == "started"
        assert done.wait(timeout=5), "background generation never ran"

    def test_concurrent_generation_rejected(self, client, monkeypatch):
        import threading

        import api as api_module

        started = threading.Event()
        release = threading.Event()

        def slow_generation():
            started.set()
            release.wait(timeout=5)

        monkeypatch.setattr(api_module, "auto_generate_signals", slow_generation)

        first = client.post("/api/signals/generate")
        assert first.status_code == 202
        assert started.wait(timeout=5)

        second = client.post("/api/signals/generate")
        release.set()
        assert second.status_code == 409
        assert second.get_json()["status"] == "already_running"
