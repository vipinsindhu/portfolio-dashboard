# Feature Alignment: Portfolio Dashboard → Stock Recommendation PRD

## Current Build Analysis

### What You Have (Portfolio Dashboard)
- ✅ React + Vite frontend (16 components)
- ✅ Flask + Gunicorn backend
- ✅ Macro analysis engine
- ✅ Portfolio management UI
- ✅ GitHub Actions CI/CD
- ✅ Railway deployment

### What PRD Needs (Stock Recommendation)
- ❌ AI-generated stock/ETF signals (Claude API)
- ❌ Email delivery system (Resend/Mailchimp)
- ❌ Stripe subscription paywall
- ❌ Signal archive with accuracy tracking
- ❌ Compliance disclaimers
- ❌ B2B API tier

---

## Feature Removal List (Align to PRD)

### 🗑️ Remove (Not in PRD Scope)

| Component | Why | Effort |
|-----------|-----|--------|
| PortfolioTab.jsx | Signal product doesn't manage user portfolios | Delete |
| PortfolioForm.jsx | No portfolio management needed | Delete |
| PortfolioSummary.jsx | Depends on portfolio concept | Delete |
| CSVUpload.jsx | No bulk import of holdings needed | Delete |
| OutlookTab.jsx | Personal forecasts ≠ general signals | Delete |
| InvestmentPlanTab.jsx | Portfolio planning out of scope | Delete |
| PlanForm.jsx | Not needed | Delete |
| HealthGauge.jsx | Not in PRD P0 | Delete |
| RegimeCard.jsx | Nice-to-have, not P0 | Simplify/Remove |
| fetch_macro.py | Replace with direct API calls in signal engine | Refactor |

**Impact:** Remove ~60% of frontend code, 0% loss of MVP value

### ✅ Keep & Repurpose

| Component | Reuse For |
|-----------|-----------|
| MacroAnalysis.jsx | Signal card display |
| IndicatorCard.jsx | Signal detail macro context |
| TabBar.jsx | Navigation (Signal List / Archive / Account) |
| Header.jsx | Keep as-is |
| App.jsx | Refactor routing |
| Flask API structure | Expand for signals |

---

## Feature Build List (PRD P0 Requirements)

### TIER 1: Core Signal Engine (Weeks 1-4)

**Backend:**
- [ ] Claude API integration
  - Generate weekly signals using `claude-sonnet-4`
  - Input: yfinance fundamentals + FRED macro + last week's price action
  - Output: `{ticker, direction (buy/hold/avoid), confidence (1-10), rationale}`
  
- [ ] Data fetching pipeline
  - yfinance: price, fundamentals, sector, market cap
  - FRED API: macro context (rates, CPI, GDP)
  - Aggregate into "signal candidates" database
  
- [ ] Signal scoring model
  - Python script: rank candidates by fundamentals + macro fit
  - Feed top 10 into Claude for reasoning
  - Claude returns 3-5 final signals with explanations
  
- [ ] Signal storage
  - SQLite table: `signals (id, ticker, direction, score, rationale, created_at, sector, market_cap)`
  - Durable markdown files (PM Brain style): `signals/YYYY-MM-DD.md`
  
- [ ] API endpoints
  ```
  GET /api/signals              # Latest 5 signals
  GET /api/signals/{id}         # Detail page
  GET /api/signals/archive      # Past 12 weeks
  POST /api/signals/generate    # Admin-only: trigger generation
  GET /api/signals/accuracy     # Historical accuracy
  ```

**Frontend:**
- [ ] SignalList.jsx
  - Cards: ticker | direction (🟢 buy / 🟡 hold / 🔴 avoid) | confidence | sector
  - Filter by sector, market cap, direction
  - Link to detail page
  
- [ ] SignalDetail.jsx
  - Full rationale from Claude
  - Fundamentals snapshot
  - Macro context ("rates are high, P/E stretched")
  - Historical outcome (after 30 days)
  - Disclaimer badge
  
- [ ] SignalArchive.jsx
  - Browse past 12 weeks
  - Filter by date, sector
  - Show outcome vs prediction
  
- [ ] CompliancePage.jsx
  - `/disclaimer` - Required on every signal
  - `/about-signals` - How they work
  - `/disclosure` - "Educational only, not investment advice"

---

### TIER 2: Email + Paywall (Weeks 5-8)

**Backend:**
- [ ] Email delivery (Resend integration)
  - Weekly digest: 3-5 signals + rationale
  - Schedule: Every Monday 8 AM
  - Track opens/clicks
  - Unsubscribe links
  
- [ ] Stripe integration
  - Free tier: 1 signal/week + archive (read-only)
  - Paid tier ($29/mo): Full digest + filters + history
  - Webhook handlers: `charge.paid`, `customer.subscription.updated`
  
- [ ] User authentication
  - Email/password signup
  - Email verification
  - JWT tokens
  - Link to Stripe customer ID
  
- [ ] Subscription state
  - Query user's subscription status
  - Enforce paywall on paid features
  - Handle failed renewals

**Frontend:**
- [ ] SignupPage.jsx
  - Email, password, confirm
  - Terms & compliance acknowledgment
  
- [ ] LoginPage.jsx
  - Email/password login
  - Forgot password flow
  
- [ ] AccountPage.jsx
  - Subscription status
  - Billing history
  - Email preferences
  - Manage payment method
  
- [ ] Paywall logic
  - Free users: See 1 latest signal + archive (read-only)
  - Paid users: All signals + filters + email delivery
  - CTA: "Upgrade for full access"

---

### TIER 3: Accuracy Tracking + B2B (Weeks 9-12)

**Backend:**
- [ ] Accuracy tracker
  - Cron job (daily): Compare predicted direction vs actual 30-day price movement
  - Update signal record: `{actual_direction, result (win/loss), accuracy_pct}`
  - Calculate rolling accuracy (last 4 weeks, by sector)
  
- [ ] B2B API tier
  - API keys for developers
  - Rate limits: 100 req/min (free), 1000+ (paid)
  - Webhook delivery for real-time signals
  - Usage metering → Stripe billing

**Frontend:**
- [ ] AccuracyDashboard.jsx
  - Historical win rate
  - Confidence vs outcome correlation
  - Accuracy by sector
  - "This week: 67% accuracy"

---

## Architecture Improvements (PM Brain Alignment)

### Add Decision Documentation

Create `.claude/` directory structure:

```
.claude/
├── CLAUDE.md                    # Operating manual
├── knowledge/
│   ├── signal-product.md        # North-star metric, non-goals
│   ├── users.md                 # Personas from PRD
│   └── architecture.md          # API contracts
└── decisions/
    ├── 2026-06-signal-model.md  # Signal schema decision
    ├── 2026-06-email-provider.md # Why Resend?
    └── 2026-06-accuracy-tracking.md # 30-day accuracy window
```

### Durable Signal Records

Store signals as markdown for auditability:

```
signals/
├── 2026-06-07-weekly.md
    Content:
    - Weekly digest summary
    - 3-5 signals with Claude rationale
    - Macro context snapshot
    - Links to detail pages
├── accuracy/
│   └── 2026-06-analysis.md      # Rolling accuracy metrics
└── hypotheses/
    └── confidence-scoring.md     # Testing scoring model
```

---

## Implementation Roadmap

### Phase 1: MVP (4 weeks)
- Remove portfolio/planning components
- Build signal generation (Claude + scoring)
- Create signal list/detail pages
- Launch with free tier (1 signal/week)

### Phase 2: Launch (4 weeks)
- Add Stripe + subscription
- Email delivery system
- User auth
- Launch paid tier

### Phase 3: Scale (4 weeks)
- Accuracy tracking
- B2B API tier
- Signal filtering
- Referral program (future)

---

## Key Changes Summary

| Item | Current | PRD-Aligned | Benefit |
|------|---------|-------------|---------|
| Frontend components | 16 | 8 | -50% complexity, focused UX |
| Frontend files | ~3,500 lines | ~1,800 lines | Faster iteration |
| Backend endpoints | 5 | 12+ | Rich signal API |
| Backend logic | Macro display | Signal generation | Core value delivery |
| Deployment | Backend only | Full-stack (+ email, Stripe) | Revenue-ready |
| Data model | Indicators + Signals | Signals + Users + Subscriptions | Business model |

---

## Next Steps (Choose One)

1. **Start rebuild** - I can remove portfolio components and start signal engine
2. **Plan first** - Create detailed .claude/decisions/ docs before coding
3. **Hybrid** - Keep portfolio dashboard as separate feature, build signals separately
4. **Validate** - Talk to 5 investors first to test if signals are valuable before building

What's your preference?
