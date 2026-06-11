"""Unit tests for portfolio parsing, models, and validation."""

import pytest

from portfolio import (
    Holding,
    create_portfolio,
    get_top_n_concentration,
    parse_csv,
    validate_portfolio,
)


def make_portfolio(*holdings):
    return create_portfolio([Holding(*h) for h in holdings])


# ---------- parse_csv ----------

class TestParseCSV:
    def test_standard_header(self):
        holdings = parse_csv("Symbol,Quantity,PurchasePrice\nAAPL,10,150\nMSFT,5,350\n")
        assert len(holdings) == 2
        assert holdings[0].symbol == "AAPL"
        assert holdings[0].quantity == 10
        assert holdings[0].purchase_price == 150

    @pytest.mark.parametrize("price_header", [
        "PurchasePrice", "Purchase Price", "purchase_price",
        "Cost Basis", "CostBasis", "Price", "Unit Cost",
    ])
    def test_accepts_price_header_variations(self, price_header):
        holdings = parse_csv(f"Symbol,Quantity,{price_header}\nAAPL,10,150\n")
        assert holdings[0].purchase_price == 150

    def test_lowercase_headers(self):
        holdings = parse_csv("symbol,quantity,price\nAAPL,10,150\n")
        assert holdings[0].symbol == "AAPL"

    def test_strips_currency_symbols_and_commas(self):
        holdings = parse_csv('Symbol,Quantity,Price\nAAPL,"1,000",$1500.50\n')
        assert holdings[0].quantity == 1000
        assert holdings[0].purchase_price == 1500.50

    def test_symbol_uppercased(self):
        holdings = parse_csv("Symbol,Quantity,Price\naapl,10,150\n")
        assert holdings[0].symbol == "AAPL"

    def test_utf8_bom_handled(self):
        holdings = parse_csv("﻿Symbol,Quantity,Price\nAAPL,10,150\n")
        assert holdings[0].symbol == "AAPL"

    def test_empty_rows_skipped(self):
        holdings = parse_csv("Symbol,Quantity,Price\nAAPL,10,150\n,,\nMSFT,5,350\n")
        assert [h.symbol for h in holdings] == ["AAPL", "MSFT"]

    def test_missing_symbol_column_raises(self):
        with pytest.raises(ValueError, match="Symbol"):
            parse_csv("Ticker,Quantity,Price\nAAPL,10,150\n")

    def test_missing_quantity_column_raises(self):
        with pytest.raises(ValueError, match="Quantity"):
            parse_csv("Symbol,Price\nAAPL,150\n")

    def test_missing_price_column_raises(self):
        with pytest.raises(ValueError, match="Price"):
            parse_csv("Symbol,Quantity\nAAPL,10\n")

    def test_non_numeric_quantity_raises(self):
        with pytest.raises(ValueError, match="Invalid CSV row"):
            parse_csv("Symbol,Quantity,Price\nAAPL,ten,150\n")

    def test_empty_csv_raises(self):
        with pytest.raises(ValueError):
            parse_csv("")

    def test_header_only_raises(self):
        with pytest.raises(ValueError, match="no valid holdings"):
            parse_csv("Symbol,Quantity,Price\n")


# ---------- Holding ----------

class TestHolding:
    def test_cost_basis(self):
        assert Holding("AAPL", 10, 150).cost_basis == 1500

    def test_current_value_falls_back_to_cost_basis(self):
        assert Holding("AAPL", 10, 150).current_value == 1500

    def test_current_value_uses_current_price(self):
        assert Holding("AAPL", 10, 150, current_price=200).current_value == 2000

    def test_gain_loss(self):
        h = Holding("AAPL", 10, 150, current_price=200)
        assert h.gain_loss == 500
        assert h.gain_loss_pct == pytest.approx(33.333, rel=1e-3)

    def test_gain_loss_pct_zero_cost_basis(self):
        assert Holding("FREE", 10, 0).gain_loss_pct == 0


# ---------- Portfolio ----------

class TestPortfolio:
    def test_totals(self):
        p = make_portfolio(("AAPL", 10, 100), ("MSFT", 10, 300))
        assert p.total_cost_basis == 4000
        assert p.total_current_value == 4000
        assert p.holding_count == 2

    def test_largest_position_weight(self):
        p = make_portfolio(("AAPL", 10, 300), ("MSFT", 10, 100))
        assert p.largest_position_weight == pytest.approx(0.75)

    def test_largest_position_weight_empty(self):
        assert create_portfolio([]).largest_position_weight == 0

    def test_add_holding_updates_existing_symbol(self):
        p = make_portfolio(("AAPL", 10, 100))
        p.add_holding(Holding("AAPL", 20, 110))
        assert p.holding_count == 1
        assert p.get_holding("AAPL").quantity == 20

    def test_add_holding_appends_new_symbol(self):
        p = make_portfolio(("AAPL", 10, 100))
        p.add_holding(Holding("MSFT", 5, 300))
        assert p.holding_count == 2

    def test_get_holding_case_insensitive(self):
        p = make_portfolio(("AAPL", 10, 100))
        assert p.get_holding("aapl") is not None

    def test_remove_holding(self):
        p = make_portfolio(("AAPL", 10, 100))
        assert p.remove_holding("AAPL") is True
        assert p.holding_count == 0
        assert p.remove_holding("AAPL") is False

    def test_top_n_concentration(self):
        p = make_portfolio(
            ("A", 1, 400), ("B", 1, 300), ("C", 1, 200), ("D", 1, 100)
        )
        assert get_top_n_concentration(p, n=3) == pytest.approx(0.9)

    def test_top_n_concentration_empty(self):
        assert get_top_n_concentration(create_portfolio([]), n=3) == 0


# ---------- validate_portfolio ----------

class TestValidatePortfolio:
    def test_valid_portfolio(self):
        result = validate_portfolio(make_portfolio(("AAPL", 10, 100)))
        assert result["valid"] is True
        assert result["errors"] == []

    def test_empty_portfolio_invalid(self):
        result = validate_portfolio(create_portfolio([]))
        assert result["valid"] is False
        assert "Portfolio is empty" in result["errors"]

    def test_duplicate_symbols_invalid(self):
        result = validate_portfolio(
            make_portfolio(("AAPL", 10, 100), ("AAPL", 5, 110))
        )
        assert result["valid"] is False
        assert "Duplicate holdings detected" in result["errors"]

    def test_negative_quantity_invalid(self):
        result = validate_portfolio(make_portfolio(("AAPL", -5, 100)))
        assert result["valid"] is False
        assert any("Quantity must be positive" in e for e in result["errors"])

    def test_zero_price_invalid(self):
        result = validate_portfolio(make_portfolio(("AAPL", 10, 0), ("MSFT", 5, 300)))
        assert result["valid"] is False
        assert any("Price must be positive" in e for e in result["errors"])
