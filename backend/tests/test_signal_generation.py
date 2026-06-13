"""Tests for balanced signal generation (mixed slate + honest-mix retry).

Guards against the all-buy regression: the LLM used to see only
pre-vetted quality stocks with a buy-flavored prompt, so hold/avoid
signals were structurally impossible.
"""

import json

from datetime import date

import signals as signals_module
from signals import (
    auto_generate_signals,
    build_candidate_slate,
    build_short_term_slate,
    candidate_prompt_fields,
    clean_signal_text,
    extract_days_until_earnings,
    extract_fundamental_metrics,
    extract_price_metrics,
    fetch_signal_candidates,
    generate_realistic_mock_signals,
    generate_short_term_signals,
    generate_signals,
    get_mock_fundamentals,
    is_single_direction,
    parse_llm_signals,
    resolve_label,
)


def make_candidates(n):
    return [
        {
            "ticker": f"T{i:02d}",
            "current_price": 100.0,
            "pe_ratio": 20 + i,
            "dividend_yield": 0.02,
            "market_cap": 50_000_000_000,
            "sector": "Technology",
            "quality_score": 100 - i,
        }
        for i in range(n)
    ]


class TestBuildCandidateSlate:
    def test_small_list_returned_whole(self):
        candidates = make_candidates(20)
        assert build_candidate_slate(candidates) == candidates

    def test_large_list_mixes_top_and_bottom(self):
        candidates = make_candidates(50)
        slate = build_candidate_slate(candidates)

        assert len(slate) == 25
        tickers = [c["ticker"] for c in slate]
        # Strongest candidates present
        assert "T00" in tickers
        # Weakest candidates present too — the LLM needs avoid material
        assert "T49" in tickers
        # Middle of the pack excluded
        assert "T20" not in tickers


class TestParseLlmSignals:
    def test_plain_json_array(self):
        text = json.dumps([{"ticker": "AAPL", "direction": "buy"}])
        assert parse_llm_signals(text)[0]["ticker"] == "AAPL"

    def test_array_embedded_in_prose(self):
        text = 'Here you go:\n[{"ticker": "AAPL", "direction": "hold"}]\nEnjoy!'
        assert parse_llm_signals(text)[0]["direction"] == "hold"

    def test_garbage_returns_none(self):
        assert parse_llm_signals("sorry, I cannot do that") is None


class TestIsSingleDirection:
    def test_all_buy_flagged(self):
        signals = [{"direction": "buy"} for _ in range(10)]
        assert is_single_direction(signals) is True

    def test_mixed_not_flagged(self):
        signals = [{"direction": "buy"}] * 8 + [{"direction": "avoid"}] * 2
        assert is_single_direction(signals) is False

    def test_small_lists_not_flagged(self):
        signals = [{"direction": "buy"} for _ in range(3)]
        assert is_single_direction(signals) is False


def llm_response(directions):
    return json.dumps(
        [
            {
                "ticker": f"T{i:02d}",
                "direction": d,
                "confidence": 7,
                "rationale": "test",
            }
            for i, d in enumerate(directions)
        ]
    )


class TestGenerateSignalsRetry:
    def setup_pipeline(self, monkeypatch, groq_responses):
        """Stub everything around the LLM call; returns the list of prompts sent."""
        tickers = [f"T{i:02d}" for i in range(10)]
        candidates = {c["ticker"]: c for c in make_candidates(10)}

        monkeypatch.setattr(signals_module, "discover_stocks", lambda: tickers)
        monkeypatch.setattr(
            signals_module, "fetch_fundamentals", lambda t: dict(candidates[t])
        )
        monkeypatch.setattr(signals_module, "fetch_short_term_metrics", lambda t: {})
        monkeypatch.setattr(signals_module, "fetch_long_term_metrics", lambda t: {})
        monkeypatch.setattr(signals_module, "fetch_macro_context", lambda: {})
        monkeypatch.setattr(
            signals_module, "get_macro_sentiment", lambda macro: "neutral"
        )

        prompts = []

        def fake_call_groq(prompt):
            prompts.append(prompt)
            return groq_responses[min(len(prompts) - 1, len(groq_responses) - 1)]

        monkeypatch.setattr(signals_module, "call_groq", fake_call_groq)
        return prompts

    def test_all_buy_triggers_one_retry_and_uses_mixed_result(self, monkeypatch):
        all_buy = llm_response(["buy"] * 10)
        mixed = llm_response(["buy"] * 6 + ["hold"] * 2 + ["avoid"] * 2)
        prompts = self.setup_pipeline(monkeypatch, [all_buy, mixed])

        result = generate_signals(count=10)

        assert len(prompts) == 2
        assert "every stock the same way" in prompts[1]
        directions = {s["direction"] for s in result}
        assert directions == {"buy", "hold", "avoid"}

    def test_mixed_first_answer_not_retried(self, monkeypatch):
        mixed = llm_response(["buy"] * 7 + ["avoid"] * 3)
        prompts = self.setup_pipeline(monkeypatch, [mixed])

        result = generate_signals(count=10)

        assert len(prompts) == 1
        assert {s["direction"] for s in result} == {"buy", "avoid"}

    def test_failed_retry_keeps_original_answer(self, monkeypatch):
        all_buy = llm_response(["buy"] * 10)
        prompts = self.setup_pipeline(monkeypatch, [all_buy, "garbage response"])

        result = generate_signals(count=10)

        assert len(prompts) == 2
        assert len(result) == 10
        assert all(s["direction"] == "buy" for s in result)

    def test_prompt_includes_weak_candidates_and_honesty_rule(self, monkeypatch):
        mixed = llm_response(["buy"] * 7 + ["avoid"] * 3)
        prompts = self.setup_pipeline(monkeypatch, [mixed])

        generate_signals(count=10)

        prompt = prompts[0]
        # Weakest candidate (T09 with the lowest quality score) made the slate
        assert "T09" in prompt
        assert "do NOT call everything a buy" in prompt


class TestPlaceholderFundamentals:
    def test_mock_fundamentals_are_tagged(self):
        assert get_mock_fundamentals("AAPL")["fundamentals_source"] == "mock"
        assert get_mock_fundamentals("ZZZZ")["fundamentals_source"] == "mock"

    def test_candidates_with_placeholder_data_excluded_when_enough_real(self, monkeypatch):
        real = {f"R{i:02d}": dict(make_candidates(1)[0], ticker=f"R{i:02d}") for i in range(12)}
        tickers = list(real) + ["FAKE1", "FAKE2"]

        def fake_fetch(ticker):
            if ticker in real:
                return dict(real[ticker])
            return {"ticker": ticker, "current_price": 100, "fundamentals_source": "mock"}

        monkeypatch.setattr(signals_module, "discover_stocks", lambda: tickers)
        monkeypatch.setattr(signals_module, "fetch_fundamentals", fake_fetch)

        candidates = fetch_signal_candidates()

        result_tickers = {c["ticker"] for c in candidates}
        assert "FAKE1" not in result_tickers
        assert len(candidates) == 12

    def test_placeholder_candidates_kept_when_apis_degraded(self, monkeypatch):
        # Fewer than 10 real candidates: keep mocks so the app isn't empty
        tickers = ["R00", "FAKE1", "FAKE2"]

        def fake_fetch(ticker):
            if ticker == "R00":
                return dict(make_candidates(1)[0], ticker="R00")
            return {"ticker": ticker, "current_price": 100, "fundamentals_source": "mock"}

        monkeypatch.setattr(signals_module, "discover_stocks", lambda: tickers)
        monkeypatch.setattr(signals_module, "fetch_fundamentals", fake_fetch)

        candidates = fetch_signal_candidates()

        assert {c["ticker"] for c in candidates} == {"R00", "FAKE1", "FAKE2"}

    def test_internal_fields_stripped_from_prompt_payload(self):
        candidate = {
            "ticker": "AAPL",
            "pe_ratio": 28.5,
            "quality_score": 85,
            "fundamentals_source": "mock",
        }
        cleaned = candidate_prompt_fields(candidate)
        assert "quality_score" not in cleaned
        assert "fundamentals_source" not in cleaned
        assert cleaned["pe_ratio"] == 28.5

    def test_prompts_do_not_contain_quality_score(self, monkeypatch):
        mixed = llm_response(["buy"] * 7 + ["avoid"] * 3)
        prompts = TestGenerateSignalsRetry().setup_pipeline(monkeypatch, [mixed])

        generate_signals(count=10)
        generate_short_term_signals(count=10)

        for prompt in prompts:
            assert "quality_score" not in prompt


class TestShortTermMetricsExtraction:
    def test_extract_price_metrics_maps_and_rounds(self):
        payload = {"metric": {
            "5DayPriceReturnDaily": 2.345,
            "13WeekPriceReturnDaily": -11.87,
            "26WeekPriceReturnDaily": 4.0,
            "beta": 1.234,
            "52WeekHigh": 211.553,
            "52WeekLow": 142.1,
        }}
        out = extract_price_metrics(payload)
        assert out == {
            "return_5d_pct": 2.3,
            "return_13w_pct": -11.9,
            "return_26w_pct": 4.0,
            "beta": 1.23,
            "52_week_high": 211.55,
            "52_week_low": 142.1,
        }

    def test_extract_price_metrics_ignores_missing_and_non_numeric(self):
        assert extract_price_metrics({"metric": {"beta": "N/A"}}) == {}
        assert extract_price_metrics({}) == {}
        assert extract_price_metrics(None) == {}

    def test_days_until_earnings_nearest_future_date(self):
        today = date(2026, 6, 11)
        payload = {"earningsCalendar": [
            {"date": "2026-07-20"},
            {"date": "2026-06-25"},
            {"date": "2026-06-01"},  # past — ignored
            {"date": "bogus"},
        ]}
        assert extract_days_until_earnings(payload, today) == 14

    def test_days_until_earnings_none_when_no_upcoming(self):
        today = date(2026, 6, 11)
        assert extract_days_until_earnings({"earningsCalendar": []}, today) is None
        assert extract_days_until_earnings(None, today) is None


class TestBuildShortTermSlate:
    def test_selects_dips_movers_and_quality_anchors(self):
        candidates = make_candidates(40)
        # Give each a 13-week return: T00 best (+40) down to T39 worst (-38)
        for i, c in enumerate(candidates):
            c["return_13w_pct"] = 40 - i * 2

        slate = build_short_term_slate(candidates)
        tickers = {c["ticker"] for c in slate}

        assert "T39" in tickers  # biggest loser (dip/avoid material)
        assert "T00" in tickers  # strongest mover and quality anchor
        assert "T08" in tickers  # quality anchor
        assert "T20" not in tickers  # middle of the pack excluded
        assert len(slate) <= 25
        assert len(tickers) == len(slate)  # deduplicated

    def test_falls_back_to_quality_slate_without_momentum_data(self):
        candidates = make_candidates(40)  # no return_13w_pct fields
        assert build_short_term_slate(candidates) == build_candidate_slate(candidates)


class TestTimeframeTagging:
    def test_long_term_signals_tagged(self, monkeypatch):
        mixed = llm_response(["buy"] * 7 + ["avoid"] * 3)
        TestGenerateSignalsRetry().setup_pipeline(monkeypatch, [mixed])

        result = generate_signals(count=10)

        assert all(s["timeframe"] == "long_term" for s in result)

    def test_short_term_signals_tagged_and_prompt_is_short_term(self, monkeypatch):
        mixed = llm_response(["buy"] * 6 + ["hold"] * 2 + ["avoid"] * 2)
        prompts = TestGenerateSignalsRetry().setup_pipeline(monkeypatch, [mixed])

        result = generate_short_term_signals(count=10)

        assert all(s["timeframe"] == "short_term" for s in result)
        assert "1-3 MONTHS" in prompts[0]
        assert "pct_of_52_week_range" in prompts[0]

    def test_short_term_prompt_carries_momentum_and_earnings_cues(self, monkeypatch):
        mixed = llm_response(["buy"] * 6 + ["hold"] * 2 + ["avoid"] * 2)
        prompts = TestGenerateSignalsRetry().setup_pipeline(monkeypatch, [mixed])
        monkeypatch.setattr(
            signals_module, "fetch_short_term_metrics",
            lambda t: {"return_13w_pct": -12.5, "return_5d_pct": 1.2, "beta": 1.4, "days_until_earnings": 9},
        )

        generate_short_term_signals(count=10)

        prompt = prompts[0]
        assert '"return_13w_pct": -12.5' in prompt
        assert '"days_until_earnings": 9' in prompt
        assert "beta" in prompt

    def test_long_term_prompt_carries_fundamental_cues(self, monkeypatch):
        mixed = llm_response(["buy"] * 7 + ["avoid"] * 3)
        prompts = TestGenerateSignalsRetry().setup_pipeline(monkeypatch, [mixed])
        monkeypatch.setattr(
            signals_module, "fetch_long_term_metrics",
            lambda t: {"revenue_growth_5y_pct": 9.5, "net_margin_pct": 18.2, "roe_pct": 22.0, "debt_to_equity": 0.45},
        )

        generate_signals(count=10)

        prompt = prompts[0]
        assert '"revenue_growth_5y_pct": 9.5' in prompt
        assert '"net_margin_pct": 18.2' in prompt
        assert "debt_to_equity" in prompt

    def test_auto_generate_saves_both_timeframes(self, monkeypatch):
        monkeypatch.setattr(
            signals_module, "fetch_signal_candidates", lambda: make_candidates(10)
        )
        monkeypatch.setattr(
            signals_module, "generate_signals",
            lambda count, candidates=None: [
                {"ticker": "AAPL", "direction": "buy", "timeframe": "long_term"}
            ],
        )
        monkeypatch.setattr(
            signals_module, "generate_short_term_signals",
            lambda count, candidates=None: [
                {"ticker": "BAC", "direction": "buy", "timeframe": "short_term"}
            ],
        )
        saved = {}
        monkeypatch.setattr(signals_module, "save_signals", saved.update)

        assert auto_generate_signals() is True
        timeframes = {s["timeframe"] for s in saved["signals"]}
        assert timeframes == {"long_term", "short_term"}


class TestResolveLabel:
    def test_valid_label_returns_canonical_spelling(self):
        assert resolve_label("dip buy", "buy", "short_term") == "Dip Buy"
        assert resolve_label("  CORE HOLDING ", "hold", "long_term") == "Core Holding"

    def test_invented_label_falls_back_to_direction_default(self):
        assert resolve_label("Strong Buy", "buy", "short_term") == "Momentum Buy"
        assert resolve_label("YOLO", "buy", "long_term") == "Accumulate"

    def test_missing_label_falls_back(self):
        assert resolve_label(None, "hold", "short_term") == "Wait"
        assert resolve_label(None, "avoid", "long_term") == "Avoid"

    def test_label_from_wrong_timeframe_vocabulary_rejected(self):
        # "Dip Buy" is short-term vocabulary; the long-term pass must not use it
        assert resolve_label("Dip Buy", "buy", "long_term") == "Accumulate"

    def test_unknown_direction_or_timeframe_returns_none(self):
        assert resolve_label("Buy", "moon", "short_term") is None
        assert resolve_label("Buy", "buy", "weird_timeframe") is None


class TestCleanSignalText:
    def test_normalizes_whitespace(self):
        assert clean_signal_text("  Earnings   in\n12 days  ") == "Earnings in 12 days"

    def test_caps_length(self):
        assert clean_signal_text("x" * 500) == "x" * 220
        assert clean_signal_text("x" * 500, max_len=40) == "x" * 40

    def test_empty_or_non_string_returns_none(self):
        assert clean_signal_text("   ") is None
        assert clean_signal_text(None) is None
        assert clean_signal_text(42) is None


class TestFundamentalMetricsExtraction:
    def test_maps_and_rounds(self):
        payload = {"metric": {
            "revenueGrowth5Y": 9.512,
            "epsGrowth5Y": 12.04,
            "netProfitMarginTTM": 18.267,
            "roeTTM": 22.91,
            "totalDebt/totalEquityQuarterly": 0.453,
            "dividendGrowthRate5Y": 6.0,
        }}
        out = extract_fundamental_metrics(payload)
        assert out == {
            "revenue_growth_5y_pct": 9.5,
            "eps_growth_5y_pct": 12.0,
            "net_margin_pct": 18.3,
            "roe_pct": 22.9,
            "debt_to_equity": 0.45,
            "dividend_growth_5y_pct": 6.0,
        }

    def test_ignores_missing_and_non_numeric(self):
        assert extract_fundamental_metrics({"metric": {"roeTTM": "N/A"}}) == {}
        assert extract_fundamental_metrics({}) == {}
        assert extract_fundamental_metrics(None) == {}


def llm_response_with_extras(entries):
    """LLM response from full signal dicts (ticker auto-assigned)."""
    return json.dumps(
        [
            {"ticker": f"T{i:02d}", "confidence": 7, "rationale": "test", **entry}
            for i, entry in enumerate(entries)
        ]
    )


class TestTimeframeSchemas:
    def test_long_term_signals_carry_validated_label_and_schema_fields(self, monkeypatch):
        response = llm_response_with_extras(
            [{"direction": "buy", "label": "Accumulate",
              "moat": "  Biggest  store network ", "what_to_watch": "Revenue growth above 4%"}] * 7
            + [{"direction": "hold", "label": "Bogus Label"}] * 3
        )
        TestGenerateSignalsRetry().setup_pipeline(monkeypatch, [response])

        result = generate_signals(count=10)

        buys = [s for s in result if s["direction"] == "buy"]
        holds = [s for s in result if s["direction"] == "hold"]
        assert all(s["label"] == "Accumulate" for s in buys)
        assert all(s["moat"] == "Biggest store network" for s in buys)
        assert all(s["what_to_watch"] == "Revenue growth above 4%" for s in buys)
        # Invented label falls back to the long-term hold default
        assert all(s["label"] == "Core Holding" for s in holds)
        assert all(s["moat"] is None for s in holds)

    def test_long_term_signals_carry_fundamentals_for_display(self, monkeypatch):
        response = llm_response_with_extras(
            [{"direction": "buy"}] * 7 + [{"direction": "avoid"}] * 3
        )
        TestGenerateSignalsRetry().setup_pipeline(monkeypatch, [response])
        monkeypatch.setattr(
            signals_module, "fetch_long_term_metrics",
            lambda t: {"revenue_growth_5y_pct": 9.5, "net_margin_pct": 18.2},
        )

        result = generate_signals(count=10)

        assert all(s["revenue_growth_5y_pct"] == 9.5 for s in result)
        assert all(s["net_margin_pct"] == 18.2 for s in result)

    def test_short_term_signals_carry_validated_label_and_schema_fields(self, monkeypatch):
        response = llm_response_with_extras(
            [{"direction": "buy", "label": "dip buy",
              "catalyst": "Down 12% in 3 months",
              "expected_window": "1-3 months",
              "invalidation": "If it falls past its yearly low."}] * 6
            + [{"direction": "avoid", "label": "Avoid Pre-Earnings"}] * 4
        )
        TestGenerateSignalsRetry().setup_pipeline(monkeypatch, [response])

        result = generate_short_term_signals(count=10)

        buys = [s for s in result if s["direction"] == "buy"]
        avoids = [s for s in result if s["direction"] == "avoid"]
        assert all(s["label"] == "Dip Buy" for s in buys)
        assert all(s["catalyst"] == "Down 12% in 3 months" for s in buys)
        assert all(s["expected_window"] == "1-3 months" for s in buys)
        assert all(s["invalidation"] == "If it falls past its yearly low." for s in buys)
        assert all(s["label"] == "Avoid Pre-Earnings" for s in avoids)
        assert all(s["catalyst"] is None for s in avoids)

    def test_prompts_define_their_own_vocabulary(self, monkeypatch):
        mixed = llm_response(["buy"] * 7 + ["avoid"] * 3)
        prompts = TestGenerateSignalsRetry().setup_pipeline(monkeypatch, [mixed])

        generate_signals(count=10)
        generate_short_term_signals(count=10)

        long_prompt, short_prompt = prompts[0], prompts[1]
        assert "Accumulate, Core Holding, Hold, Trim, Avoid" in long_prompt
        assert "Momentum Buy" not in long_prompt
        assert "Momentum Buy, Dip Buy, Wait, Avoid Pre-Earnings, Avoid" in short_prompt
        assert "Accumulate" not in short_prompt
        assert "invalidation" in short_prompt
        assert "moat" in long_prompt

    def test_mock_signals_use_timeframe_vocabulary(self):
        candidates = make_candidates(10)
        long_mocks = generate_realistic_mock_signals(candidates, count=10)
        short_mocks = generate_realistic_mock_signals(candidates, count=10, timeframe="short_term")

        long_labels = {s["label"] for s in long_mocks}
        short_labels = {s["label"] for s in short_mocks}
        assert long_labels <= {"Accumulate", "Core Holding", "Avoid"}
        assert short_labels <= {"Momentum Buy", "Wait", "Avoid"}
