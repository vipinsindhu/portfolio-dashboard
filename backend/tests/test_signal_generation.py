"""Tests for balanced signal generation (mixed slate + honest-mix retry).

Guards against the all-buy regression: the LLM used to see only
pre-vetted quality stocks with a buy-flavored prompt, so hold/avoid
signals were structurally impossible.
"""

import json

import signals as signals_module
from signals import (
    build_candidate_slate,
    generate_signals,
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
