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
