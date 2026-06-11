"""Tests for balanced signal generation (mixed slate + honest-mix retry).

Guards against the all-buy regression: the LLM used to see only
pre-vetted quality stocks with a buy-flavored prompt, so hold/avoid
signals were structurally impossible.
"""

import json

import signals as signals_module
from signals import (
    auto_generate_signals,
    build_candidate_slate,
    candidate_prompt_fields,
    fetch_signal_candidates,
    generate_short_term_signals,
    generate_signals,
    get_mock_fundamentals,
    is_single_direction,
    parse_llm_signals,
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
