# Smart Stock Ideas — Product Requirements Document
### Persona-Sequenced MVPs (decreasing priority)

**Status:** Draft v0.1
**Owner:** Vipin
**Last updated:** June 2026
**Related docs:** `smart-stock-ideas-personas.md`

---

## 1. Product Vision & Core Thesis

Smart Stock Ideas is an AI-native stock *ideas* product — not a brokerage and not a robo-advisor. It surfaces a small set of high-quality, data-backed stock ideas and, critically, **explains the reasoning behind each one in plain language**.

The wedge is the explanation. The incumbent beginner apps split three ways — Acorns automates everything and removes decision-making, Stash guides themed picks, Robinhood hands over raw data and walks away — and none of them is built to answer the one question a younger investor actually has: *"why is this a good idea, and should I act on it?"* That gap is the product.

**Why now:** Younger investors are entering the market in record numbers but report low confidence and high information overload; user research consistently shows that too much undifferentiated data causes people to withdraw from decisions rather than act. UI quality — not fees — is the single most important factor for this cohort. An AI layer that compresses noise into a few explained ideas is both the simplification strategy and the hardest-to-copy differentiator.

---

## 2. Problem Statement

Younger self-directed investors (Gen Z through young millennials) want to make smart individual-stock decisions but are blocked at two extremes: beginners are overwhelmed by jargon and conflicting opinions and freeze, while more active users chase social-media hype and get burned. Existing tools either remove all agency or dump raw data with no judgment. The cost of not solving this is a generation that either stays out of the market or learns expensive lessons reacting to noise — and a missed window for a trust-first product as trillions transfer to younger investors.

---

## 3. Target Personas (priority order)

| # | Persona | Archetype | Primary job-to-be-done | MVP role |
|---|---------|-----------|------------------------|----------|
| 1 | **Maya** | Curious First-Timer | "Explain it simply so I'm confident enough to act" | Acquisition + activation |
| 2 | **Alex** | Busy Optimizer | "Filter the noise — give me 3 vetted ideas a week" | Retention + monetization |
| 3 | **Devon** | FOMO Trader | "Give me an edge with guardrails, keep my agency" | Engagement + responsible design |
| 4 | **Priya** | Values-Driven Builder | "Ideas that fit my values and cross-border reality" | Premium + expansion |

Full persona detail lives in the companion personas doc.

---

## 4. MVP Sequencing Rationale

The order is deliberate and dependency-driven, not just preference:

- **MVP 1 (Maya) is the foundation.** The "explain why" capability is reused by every later persona. You cannot build retention or guardrails on top of unexplained signals. Ship the wedge first.
- **MVP 2 (Alex) turns usage into retention and revenue.** Once ideas are explained, the next lever is *recurring* value — a weekly filtered digest — which is also the natural Stripe paywall.
- **MVP 3 (Devon) broadens the active base and hardens trust.** Confidence levels + anti-FOMO guardrails extend the product to higher-engagement users while differentiating on responsibility.
- **MVP 4 (Priya) is premium expansion.** Values-based filtering and cross-border / NRI support monetize a distinct, underserved segment once the core loop is proven.

Each MVP is independently shippable and learnable. Do not start a later MVP before the prior one's success threshold is met.

---

## 5. Shared Non-Goals (apply across all MVPs)

1. **Not a brokerage / no trade execution.** Ideas and reasoning only; execution stays with the user's existing broker. Removes regulatory and custody complexity from scope.
2. **No auto-trading or copy-trading.** Copy-trading drives herd behavior and overconfidence — the exact failure mode the product exists to counter. Explicitly out of scope, by design, not by timeline.
3. **No personalized financial advice / no "advisor" claims.** Educational ideas with disclaimers; avoids fiduciary and compliance obligations.
4. **No social feed / influencer content in v1.** Resist the engagement-bait pattern; revisit only if it can be done without amplifying hype.
5. **No full portfolio management or tax tooling in v1.** Adjacent and large; separate initiative (ties to the existing Portfolio Dashboard work).

---

## 6. Shared Success-Metrics Framework

Every MVP is measured on **leading indicators** (days–weeks) and **lagging indicators** (weeks–months), each with a *success* threshold and a *stretch* target. Instrumentation assumed via product analytics on the React/Vite frontend and event logging in the Flask backend. Targets below are per-MVP.

---

## 7. Monetization Model

**Recommendation: subscription-first freemium, with a B2B API as the second revenue line.** This is partly forced by what the product is — an *ideas* product, not a brokerage. The dominant fintech revenue models (payment for order flow, net interest on cash and margin, AUM management fees) all require custody or execution, which the non-goals explicitly exclude. Recurring software subscriptions plus API licensing are the natural fit — and they are higher-margin and more defensible.

### Consumer tiers (mapped to personas)

| Tier | Persona(s) | Included | Role | Price anchor |
|------|-----------|----------|------|--------------|
| **Free** | Maya | A few explained ideas/week, inline glossary, watchlist, anti-FOMO guardrails | Acquisition + activation (not revenue) | $0 |
| **Plus** | Alex + Devon | Weekly ranked digest, "what changed," confidence scores, full rationale, watchlist alerts | Monetization workhorse | ~$7/mo (~$70/yr) |
| **Premium** | Priya | Everything in Plus + values/theme filters, cross-border / NRI coverage | Highest ARPU, expansion | ~$18/mo (annual option) |

**Design choices baked into the tiering:**
- **Free must be generous, and the "explain why" wedge lives in it.** Maya is cost-conscious and won't pay before seeing value; gating the core hook kills the funnel. Monetize the *recurring* value (the weekly digest), not the first taste.
- **Plus deliberately collapses Alex and Devon.** Devon's "edge" buyer is the direct analog of the Robinhood Gold subscriber ($5/mo or $50/yr), a familiar anchor. Alex's curated digest and Devon's confidence signals are both "serious self-directed" features — one tier serves both and keeps the lineup simple.
- **Anti-FOMO guardrails stay in Free, never paywalled.** They're tied to the responsible-design positioning; charging for protection undercuts the brand promise.
- **Premium prices up because the segment is underserved**, not because it costs more to run.
- **Three consumer tiers is the ceiling.** More creates decision paralysis, especially for Maya.

### Second revenue line — B2B API
The structured JSON signal layer is already built to expose this. Usage-based or tiered API pricing to other fintechs, advisor tools, and apps is high-margin, doesn't cannibalize the consumer product, and leverages infrastructure being built regardless. Start it as early as the MVP 2 timeframe rather than treating it as a distant P2. Note: in the conservative scenario the API line is actually *larger* than consumer subscription revenue, because per-customer API value dwarfs low-priced consumer subs early on — a reason to prioritize it.

### What to avoid
- **No affiliate/referral revenue that influences which ideas surface.** An ideas product lives or dies on trust; pay-to-play recommendations are exactly what these personas are skeptical of. If referral revenue is pursued, keep it strictly separated from the recommendation engine and disclose it.
- **No balance/AUM-relative pricing.** Not applicable (no custody), and flat fees look punitive at small balances. Frame price against *value delivered* (research hours saved), never portfolio size.
- **Frictionless cancellation** (reinforces the MVP 2 requirement) — competitors draw complaints for dark-pattern cancellation.

### Rough revenue scenarios (Year 1)
Driver-based model across the three tiers + API. Full, adjustable model in the companion file `smart-stock-ideas-revenue-model.xlsx` (change the blue input cells to flex). Headline outputs:

| Metric (end of Year 1) | Conservative | Base | Optimistic |
|------------------------|-------------:|-----:|-----------:|
| Paying subscribers (M12) | ~40 | ~230 | ~1,530 |
| Total MRR (M12, exit run-rate) | ~$1.5K | ~$9.0K | ~$44K |
| Exit ARR (M12 × 12) | ~$18K | ~$107K | ~$530K |
| Year-1 revenue (booked) | ~$11K | ~$54K | ~$227K |

**Key assumptions driving the spread:** Month-1 signups (300 / 600 / 1,200), monthly signup growth (8% / 12% / 18%), activation (40% / 50% / 60%), free→paid conversion of activated users (2.5% / 4% / 7%), monthly churn (8% / 6% / 4%), Premium mix (10% / 15% / 22%), and a B2B API line starting at $400 / $1,500 / $4,000 MRR growing 10% / 15% / 20% per month. Prices are held constant across scenarios on purpose — the scenarios flex demand and funnel, not price. These are rough planning figures, not forecasts; the model is built so you can replace any input with real data as it arrives.

---

# MVP 1 — "Explain Why"
### Persona: Maya, the Curious First-Timer · **Priority: P0 (ship first)**

**Why first:** This is the wedge and the shared foundation. It converts curiosity into a first action and produces the explanation layer every other MVP depends on.

### Problem
Maya wants to start but freezes at a blank brokerage screen full of jargon. She doesn't trust influencers and doesn't know what to trust instead. She needs ideas presented as a knowledgeable friend would — short, plain, and reasoned — plus a tiny first action so she doesn't bounce.

### Goals
- **User:** Reduce a first-time user's time-to-first-understood-idea to under 2 minutes from open.
- **User:** Make every recommendation self-explanatory — no external research required to grasp the thesis.
- **Business:** Achieve a strong activation rate (defined: user views ≥1 idea *and* expands its rationale) as the core funnel metric.

### User Stories (priority order)
- As a first-time investor, I want each idea explained in one or two plain sentences so that I understand *why* it's recommended without a finance background.
- As a first-time investor, I want unfamiliar terms defined inline so that I'm never blocked by jargon.
- As a first-time investor, I want the app to open with 1–3 ready ideas so that I have an immediate starting point instead of a blank search.
- As a first-time investor, I want to save an idea to a watchlist so that I can come back without committing money yet.
- *(Edge)* As a first-time investor, when no high-confidence ideas exist, I want to see an honest "nothing compelling today" state so that I'm not pushed into a weak pick.

### Requirements

**Must-Have (P0)**
- **Plain-language rationale on every idea.** A 1–2 sentence "why this" generated from the structured JSON signal via the Groq LLM layer.
  - *Given* an idea is surfaced, *when* the user opens it, *then* a plain-language rationale (≤2 sentences, no undefined jargon) is shown.
  - [ ] Rationale is generated from the underlying signal, not free-floating
  - [ ] Rationale renders in <2s p95
- **Inline term definitions.** Tappable glossary on key terms (P/E, ETF, market cap, etc.).
- **Curated home feed of 1–3 ideas** on open (no empty state for a new user with no input).
- **Watchlist (save without buying).**
- **Honest empty/low-confidence state.**
- **Educational disclaimer** ("not financial advice") visible and non-intrusive.

**Nice-to-Have (P1)**
- "Explain like I'm new" toggle that simplifies rationale further.
- One-line "what could go wrong" caveat alongside the thesis.
- Progress nudge after first saved idea (light, non-childish).

**Future Considerations (P2)**
- Personalized feed based on declared interests (architect the signal schema to carry persona/interest tags now).
- Push of a daily idea (defer notification infra to MVP 2).

### Success Metrics
- **Leading — Activation rate** (view + expand rationale): success **45%**, stretch **60%** of new users in first session.
- **Leading — Time-to-first-understood-idea:** success **<2 min**, stretch **<60s**.
- **Leading — Jargon-block rate** (taps on undefined terms / sessions): trend toward zero.
- **Lagging — Week-1 retention:** success **25%**, stretch **35%**.
- **Lagging — Qualitative confidence lift** (in-app micro-survey "I understood why"): success **70%** agree.

---

# MVP 2 — "Signal, Not Noise"
### Persona: Alex, the Busy Optimizer · **Priority: P1 (retention + monetization)**

**Why second:** Once ideas are explained, recurring filtered value drives retention and is the natural Stripe paywall.

### Problem
Alex is literate and time-poor. Researching individual stocks is a time sink, and most tools generate *more* work. Alex wants a short ranked set of vetted ideas and to see only what changed since last time — 10 minutes a week, no noise.

### Goals
- **User:** Deliver a weekly ranked shortlist that requires no further research to act on.
- **User:** Surface only deltas since last visit (new ideas, changed conviction).
- **Business:** Establish the monetization tier — weekly curated digest behind Stripe — and a recurring-engagement habit.

### User Stories (priority order)
- As a time-poor investor, I want a short ranked list of vetted ideas each week so that I can decide quickly and move on.
- As a returning user, I want a "what changed since last time" view so that I don't re-read ideas I've already seen.
- As a returning user, I want a weekly email/digest so that the product reaches me without my having to remember to open it.
- As a paying user, I want to manage my subscription easily so that I trust the billing relationship.
- *(Edge)* As a returning user, when nothing material changed, I want a brief "no major changes" digest so that the product respects my time.

### Requirements

**Must-Have (P0)**
- **Ranked weekly shortlist** (e.g., top 3–5 ideas) generated from the signal layer with conviction-based ordering.
- **"What changed" view** that diffs current signals against the user's last session.
- **Weekly digest delivery** (email to start; reuse the existing GitHub Actions / alerting pattern as a fast path before building in-app push).
- **Stripe subscription paywall** gating the weekly curated digest (free tier sees limited/delayed ideas).
  - *Given* a free user, *when* they hit the weekly-digest gate, *then* they see a clear upgrade path and a preview of value.
  - [ ] Stripe checkout completes and unlocks digest
  - [ ] Subscription state is enforced server-side in Flask
  - [ ] Cancel/downgrade is self-serve and frictionless (avoid the dark-pattern cancellation complaints competitors get)

**Nice-to-Have (P1)**
- User-set cadence (daily vs weekly).
- "Mute" an idea or sector to refine the shortlist.
- Digest personalization by interest tags from MVP 1's P2 schema.

**Future Considerations (P2)**
- B2B API tier exposing the same structured JSON signals (the architecture already supports this — keep the schema clean and versioned).
- Smart "just-in-time" nudges at moments of likely surplus/attention.

### Success Metrics
- **Leading — Free→paid conversion:** success **4%**, stretch **8%** within 30 days of hitting the gate.
- **Leading — Digest open rate:** success **35%**, stretch **50%**.
- **Leading — Weekly active return rate:** success **40%**, stretch **55%** of activated users.
- **Lagging — Month-2 retention of payers:** success **80%**, stretch **90%**.
- **Lagging — Subscription MRR:** set baseline post-launch; review at 1 quarter.

---

# MVP 3 — "Confident Moves, Fewer Regrets"
### Persona: Devon, the FOMO Trader · **Priority: P2 (engagement + responsible design)**

**Why third:** Extends the product to higher-engagement, higher-risk users while making responsible design a visible differentiator. Depends on the rationale + signal layers from MVPs 1–2.

### Problem
Devon is active and overconfident, chasing momentum and getting burned. He doesn't want a robot to trade for him — he wants an *edge* with agency. The opportunity is to give him fast, opinionated, confidence-scored signals *and* gentle guardrails that flag hype-chasing without killing his sense of control.

### Goals
- **User:** Give every idea an explicit confidence level and an honest downside.
- **User:** Flag likely hype-driven decisions before he acts, without blocking him.
- **Business:** Increase engagement among active users and establish "responsible by design" as a brand differentiator (a contrarian, defensible position with this cohort).

### User Stories (priority order)
- As an active trader, I want each idea to show a confidence level so that I can size my conviction appropriately.
- As an active trader, I want to see what could go wrong with an idea so that I'm not only seeing the bull case.
- As an active trader, when I'm acting on a spiking/hyped name, I want a gentle flag so that I pause before chasing momentum.
- As an active trader, I want fast, opinionated signals so that the tool feels like an edge, not a lecture.
- *(Edge)* As an active trader, when I dismiss a guardrail, I want it to respect my choice and not nag repeatedly so that I keep my agency.

### Requirements

**Must-Have (P0)**
- **Confidence score** on every idea (derived from the signal model), shown prominently.
- **"What could go wrong" downside** paired with each thesis (promote MVP 1's P1 caveat to required here).
- **Anti-FOMO / hype flag**: a non-blocking, dismissible signal when an idea or user-searched name shows hype characteristics (e.g., rapid social/price spike).
  - *Given* a name with hype characteristics, *when* the user views/searches it, *then* a gentle, dismissible flag explains the risk
  - [ ] Flag is informational, never blocking
  - [ ] Dismissal is remembered; no repeat nagging in the same session
- **Opinionated, fast signal cards** (low-latency rendering; the "edge" feel).

**Nice-to-Have (P1)**
- Confidence-change alerts on watchlist names.
- "Cooling-off" micro-interaction on high-risk actions (optional, opt-in).
- Track-record transparency: show how prior high-confidence ideas performed.

**Future Considerations (P2)**
- Backtested confidence calibration surfaced to users.
- Risk-profile personalization of guardrail sensitivity.

### Success Metrics
- **Leading — Rationale/downside view rate on active users:** success **60%**, stretch **75%**.
- **Leading — Guardrail engagement** (flag viewed, not blindly dismissed): success **30%** pause/read.
- **Leading — Session frequency (active cohort):** success **3×/week**, stretch **5×/week**.
- **Lagging — Self-reported "fewer impulsive trades":** success **50%** agree (micro-survey).
- **Lagging — Active-cohort retention (M2):** success **45%**, stretch **60%**.

---

# MVP 4 — "Invest Like You Mean It"
### Persona: Priya, the Values-Driven Builder · **Priority: P3 (premium expansion)**

**Why last:** A distinct, underserved segment best monetized once the core loop is proven. Depends on all prior layers and a mature, well-tagged signal schema.

### Problem
Priya is deliberate, earns well, and wants her portfolio to reflect her values — and she invests across markets (US + home-country / NRI). Mainstream apps treat values-based investing as an afterthought and serve cross-border investors poorly. She'll pay for something genuinely good that respects her time and is honest about trade-offs.

### Goals
- **User:** Let users filter ideas through value-aligned themes with honest substance (not greenwashing).
- **User:** Treat cross-border / NRI investing as a first-class use case.
- **Business:** Open a premium tier and a distinct expansion segment with higher willingness to pay.

### User Stories (priority order)
- As a values-driven investor, I want to filter ideas by themes I care about so that my shortlist reflects my values.
- As a values-driven investor, I want honest detail on *why* an idea fits a theme so that I can tell substance from marketing.
- As an NRI investor, I want ideas relevant to the markets I actually invest in so that I'm not limited to a single geography.
- As a premium user, I want clear premium value so that the upgrade feels worth it.
- *(Edge)* As a values-driven investor, when an idea conflicts with a selected value, I want it transparently flagged so that I trust the filter.

### Requirements

**Must-Have (P0)**
- **Theme/value filters** applied to the idea engine (e.g., sustainability, sector preferences, exclusions).
- **Theme-fit explanation** per idea, with honest trade-offs (extends the rationale layer).
- **Multi-market / cross-border idea coverage** for priority NRI markets (scope to 1–2 markets first).
  - *Given* a user selects a values theme, *when* ideas are surfaced, *then* each shows a transparent theme-fit rationale and any conflicts are flagged
- **Premium tier in Stripe** gating values + cross-border features.

**Nice-to-Have (P1)**
- Custom user-defined exclusion lists.
- Currency/market context on cross-border ideas.

**Future Considerations (P2)**
- Deeper regional data partnerships.
- Values-alignment scoring across a full watchlist/portfolio.

### Success Metrics
- **Leading — Premium adoption among eligible users:** success **5%**, stretch **10%**.
- **Leading — Theme-filter usage:** success **40%** of premium users.
- **Lagging — Premium retention (M3):** success **80%**.
- **Lagging — Premium ARPU vs base tier:** target a clear multiple; review at 1 quarter.

---

## Cross-Cutting Open Questions

- **[Legal/Compliance — blocking]** What disclaimers and registrations are required to publish stock *ideas* without being classified as an investment adviser? Confirm before MVP 1 launch.
- **[Legal/Compliance — blocking, MVP 4]** What are the regulatory implications of cross-border / NRI idea coverage per target market?
- **[Data — blocking]** Are the current financial data APIs licensed for redistribution of derived signals to end users (and later, B2B)?
- **[Data — non-blocking]** How is signal/confidence quality validated and back-tested? Needed for MVP 3 credibility.
- **[Engineering — non-blocking]** Does Railway meet latency needs for the "fast signal" feel in MVP 3, or does SSE-heavy streaming push toward Azure Container Apps (per ongoing Portfolio Dashboard evaluation)?
- **[Design — non-blocking]** What's the visual system that feels modern and trustworthy to Gen Z without reading as childish gamification?
- **[Data/Stakeholder — non-blocking]** What analytics stack instruments the activation and conversion funnels?

---

## Timeline & Phasing

No external hard deadline assumed. Suggested phasing follows the MVP order, gated on success thresholds:

1. **MVP 1 — Explain Why:** ship, then hold until activation ≥ success threshold.
2. **MVP 2 — Signal, Not Noise:** begin once MVP 1 activation is met; introduces Stripe.
3. **MVP 3 — Confident Moves:** begin once MVP 2 conversion + retention are met.
4. **MVP 4 — Invest Like You Mean It:** begin once core loop and monetization are proven.

**Key dependencies:** legal/compliance sign-off blocks MVP 1; data-licensing confirmation blocks user-facing signal display; clean, versioned JSON signal schema is the architectural backbone for the MVP 2 B2B tier and MVP 4 theming — design it for extensibility now.

---

## Appendix — Technical Context

- **Frontend:** React / Vite. **Backend:** Python / Flask. **LLM layer:** Groq for rationale generation. **Data:** financial market APIs. **Payments:** Stripe. **Hosting:** Railway (evaluating Azure Container Apps for SSE-streaming workloads).
- **Core data layer:** structured JSON signals — the single source of truth feeding rationale, ranking, confidence, guardrails, and theming. Keeping this schema clean, tagged (interest/persona/theme), and versioned is what makes the B2B API tier and later personalization cheap rather than a rewrite.
