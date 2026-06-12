# PRD: Smart Stock Ideas — Beginner Investing Education & Signals

**Status:** Active — supersedes [FEATURE_ALIGNMENT.md](FEATURE_ALIGNMENT.md) (kept for history)
**Last updated:** 2026-06-11
**Owner:** Vipin
**Live:** https://portfolio-builder.up.railway.app/

---

## 1. What changed and why this rewrite

The original PRD scoped a **paid signal-subscription product** (weekly email digest, Stripe paywall, B2B API). During build, the product deliberately pivoted to a **free, beginner-friendly investing education tool** that combines AI signals with portfolio risk analysis and lessons. This was option 3 ("Hybrid") in the original alignment doc — chosen in practice, now made explicit.

**Decision (2026-06-11):** Monetization (auth, Stripe, email digest, B2B API) is **out of scope**. The product competes on clarity and trust, not on gated content.

## 2. Product definition

**One-liner:** A free dashboard that shows beginners *what the AI thinks is worth buying, holding, or avoiding* — and teaches them to evaluate their own portfolio like a pro would.

**Target user:** A beginner-to-intermediate retail investor who owns (or is about to buy) individual stocks, doesn't read 10-Ks, and wants guidance in plain language they can act on and learn from.

**Value propositions, in priority order:**
1. **Portfolio honesty** — upload your stocks, get told plainly what's risky (concentration, sector clustering) and why it matters.
2. **Actionable signals** — weekly Buy / Hold / Avoid ideas for two timeframes (this week / build wealth), with confidence scores and rationale.
3. **Learning loop** — every warning links to a lesson; users get smarter with each use.

**Non-goals (explicit):**
- Paid tiers, paywalls, subscriptions, or B2B API
- User accounts *as a monetization mechanism* (see P1: accounts may return as a data-isolation necessity)
- Real-money execution, brokerage integration, or anything resembling regulated financial advice
- Day-trading / intraday signals

## 3. What's shipped (baseline, as of 2026-06-11)

| Area | Status |
|---|---|
| AI signals, 2 timeframes, Buy/Hold/Avoid sections with confidence + rationale | ✅ Live (Groq Llama-3.3) |
| Portfolio upload (CSV/manual) + pitfall detector (concentration, sector, diversification) | ✅ Live |
| Hybrid stock discovery (Alpha Vantage → Finnhub → hardcoded) | ✅ Live |
| Learn tab with lessons tied to detected pitfalls | ✅ Live |
| Demo mode (one-click sample portfolio) | ✅ Live |
| Mobile bottom-nav, WCAG AA | ✅ Live |
| Compliance disclaimers | ✅ Live |
| Test suite (66 backend tests) + CI + smoke test | ✅ Live |
| Hourly signal refresh scheduler | ✅ Live |
| Signal archive | ⚠️ Backend endpoint exists; UI orphaned (not reachable from tabs) |
| Accuracy tracking | ⚠️ `update_signal_accuracy()` exists; no cron, no UI |
| Portfolio recommendations classifier | ⚠️ Buggy: "add" includes owned stocks, "sell_reduce" includes unowned |
| Multi-user portfolios | ❌ One globally shared portfolio |

## 4. North star & metrics

**North star:** Weekly returning users who load or revisit a portfolio (proxy: the product taught them something worth coming back for).

**Supporting metrics:**
- Demo → own-portfolio conversion rate
- Signal accuracy, rolling 4 weeks, by direction (target: published in-app, whatever the number is)
- % of sessions that open at least one lesson
- Mobile share of sessions (bottom-nav investment should move this)

**Guardrail:** Zero days with stale signals (> 2h old) on the live site.

## 5. Roadmap

### P0 — Trust & correctness (next 2–3 weeks)
The product's only moat is being *right and honest*. These close the gap between what we show and what's true.

1. ~~**Accuracy tracking, end to end.**~~ ✅ **Shipped 2026-06-11.** Daily GitHub Actions job captures signals into committed `signal_history.json` and scores 30-day outcomes via yfinance; `/api/signals/accuracy` + "Track Record" card in-app. First scored cohort matures ~2026-07-11.
2. ~~**Fix the recommendation classifier.**~~ ✅ **Shipped 2026-06-11.** Ownership matching is now case-insensitive (lowercase holdings no longer leak owned stocks into "add" or drop avoid signals); buy signals on positions >20% weight say HOLD with a concentration warning instead of ACCUMULATE, reconciling with the pitfall detector; contract pinned by `backend/tests/test_signals_filter.py`.
3. **Re-wire the Signal Archive.** Backend exists; surface past weeks' signals (and, once #1 lands, their outcomes) — likely as a section within This Week rather than a sixth tab.

### P1 — Per-user portfolios (3–4 weeks after P0)
The shared-portfolio model is fine for demo, broken for real use (two simultaneous users overwrite each other).
- Lightweight, **free** accounts (or anonymous browser-keyed storage as an interim) purely for data isolation.
- Portfolio persistence per user; demo mode becomes session-scoped instead of clobbering global state.
- This is infrastructure, not monetization — keep signup friction near zero.

### P2 — Learning loop depth (opportunistic)
- Lesson completion state; "what changed since last visit" diff on portfolio health
- Signal explanation upgrades (richer macro context per card)
- Email *opt-in* weekly summary — notification, not product gating (revisit only after P1 accounts exist)

## 6. Risks & constraints

- **Free-tier API limits** (Finnhub, Groq, Alpha Vantage): a traffic spike degrades signals. Mitigation: cached responses, demo mode serves cached analysis, rate-limit monitoring.
- **Signal quality ceiling:** confidence currently self-assessed at 7/10; accuracy tracking (P0-1) converts this from a vibe into a number — and we publish it either way.
- **Quality screen suppresses "Avoid" signals** (only pre-screened quality stocks reach the LLM). Acceptable for now; revisit if the empty Avoid section confuses users. Option: grade 3–5 rejected candidates per cycle so Avoid has content.
- **Single maintainer, side project:** roadmap sized for nights-and-weekends; CI + test conventions (CLAUDE.md) exist to keep velocity safe.

## 7. Decision log

| Date | Decision |
|---|---|
| 2026-06-06 | Azure → Railway migration (same-day, Azure fought back) |
| 2026-06-08 | Skip fallback quality filters; cap candidates at 30 (timeout fix) |
| 2026-06-10 | Azure fully retired; secrets removed from repo; tests + CI added |
| 2026-06-11 | **PRD re-scoped: free educational hybrid; monetization dropped** |
| 2026-06-11 | Buy/Hold/Avoid unified sections; stats box counts displayed cards |
| 2026-06-11 | **P0-1 shipped:** 30-day accuracy tracking (history committed daily via GitHub Actions; win rules: buy=up, avoid=down, hold=±5%; first results ~2026-07-11) |
| 2026-06-11 | Stale-signal fix: startup job regenerates signals when stored ones are >60m old (deploys were resetting the hourly timer + data) |
| 2026-06-11 | **P0-2 shipped:** classifier fixed (case-insensitive ownership; no ACCUMULATE on >20% positions; dead short-term scorer that returned empty recommendations removed; recommendations now actually embedded in signals responses — `dict(dataclass)` bug) |
| 2026-06-11 | **Balanced generation:** LLM now sees a mixed slate (top 15 + bottom 10 by quality) with an honesty-first prompt and a one-shot retry when it rates everything the same — hold/avoid signals were structurally impossible before (quality screen + buy-only example) |
| 2026-06-11 | **Real short-term signals:** dedicated 1–3 month LLM pass (price vs 52-week range, valuation, macro — only data we actually have) tagged `timeframe: short_term`; long/short tabs now serve genuinely different pools (previously the same long-term signals with different confidence bars); untagged legacy signals still render |
| 2026-06-11 | **Short-term differentiation deepened:** Finnhub free-tier momentum cues (5d/13w/26w returns, beta) + upcoming-earnings countdown feed the short-term prompt; slate now selected on momentum grounds (biggest dips + strongest movers + quality anchors) so short/long rate different stocks, not the same list twice; degrades gracefully to the quality slate when metrics are unavailable |
