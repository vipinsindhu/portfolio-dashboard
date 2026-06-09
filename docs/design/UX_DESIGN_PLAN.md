# Modern Stock Research UX - Design Plan

## Vision
A clean, educational stock research platform that guides self-directed investors from discovery (Plan) through analysis (Analysis) to decision-making (Recommendation).

**User Journey:** "I'm curious about AAPL → Let me research it deeply → What should I actually do?"

---

## Design System (Modern Minimal)

### Color Palette
- **Primary**: Clean slate (white backgrounds, light gray borders)
- **Accent Green**: #10b981 (buy signals, positive metrics)
- **Accent Red**: #ef4444 (avoid/sell signals, negative metrics)
- **Accent Neutral**: #6b7280 (holds, neutral signals)
- **Text Primary**: #1f2937 (dark gray, high contrast)
- **Text Secondary**: #6b7280 (medium gray, supporting info)
- **Background**: #ffffff (primary), #f9fafb (secondary)

### Typography
- **Headlines**: 2xl-4xl, weight 700, tracking tight (Apple-like boldness)
- **Body**: 1base, weight 400-500, line-height 1.6 (readable)
- **Small text**: 0.875rem, weight 500, all-caps for labels

### Components
- Card-based layouts (white on light gray)
- Clean borders: 1px solid #e5e7eb
- Spacing: 8px grid (8, 16, 24, 32, 48 rem)
- Icons: Minimal line style (Feather/Heroicons)
- Charts: Clean, minimal (no gridlines, focus on line)

---

## Screen Architecture

### 1. Watchlist (PLAN)
**Purpose:** Discover and curate stocks to research

```
┌─────────────────────────────────────────┐
│  Research Watchlist                     │
│  Build your stock research list         │
├─────────────────────────────────────────┤
│                                         │
│ [Search/Add Stock Input]                │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ AAPL                         $215   │ │
│ │ Apple Inc. • Tech           +2.4%   │ │
│ │ Added 3 days ago         [Research] │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ NVDA                        $625   │ │
│ │ NVIDIA Corp. • Tech         +8.1%   │ │
│ │ Added 1 week ago         [Research] │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ TSLA                        $240   │ │
│ │ Tesla Inc. • Consumer       -1.2%   │ │
│ │ Added 2 weeks ago        [Research] │ │
│ └─────────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

**Key Elements:**
- Search bar with autocomplete (type ticker or company name)
- Cards showing: Ticker | Company | Sector | Current price | YTD % | "Research" button
- Filter by sector dropdown
- Sort options (recently added, most researched, etc.)
- "Quick add" from signal recommendations

**Interactions:**
- Click [Research] → Navigate to Research Detail
- Click ticker card → Navigate to Research Detail
- Remove from watchlist (subtle X button)
- Pin top 3 for quick access

---

### 2. Research Detail (ANALYSIS)
**Purpose:** Deep dive into fundamentals, technicals, valuation, macro fit

```
┌─────────────────────────────────────────────────────────────┐
│  AAPL • Apple Inc.                           [Back]         │
│  Technology • $215 • +2.4% today                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MACRO FIT: How does this fit the current environment?      │
│  ┌─────────────────────────────────────────────────────────┐
│  │ Fed rates are HIGH (5.25%) → Growth premium compressed │
│  │ VIX is CALM (15.2) → Lower execution risk              │
│  │ Dollar is STRONG → Pressures international sales        │
│  │ P/E is elevated → Requires strong growth to justify     │
│  └─────────────────────────────────────────────────────────┘
│                                                             │
│  FUNDAMENTALS: The business itself                         │
│  ┌──────────────────────┬──────────────────────────────────┐
│  │ Metric       │ Value │ Assessment                      │
│  ├──────────────────────┼──────────────────────────────────┤
│  │ P/E Ratio    │ 32.4  │ Premium vs tech avg 27.1        │
│  │ PEG Ratio    │ 1.8   │ Fair for 18% growth             │
│  │ Dividend     │ 0.93% │ Low but growing                 │
│  │ Free Cash    │ $95B  │ Excellent, funds buybacks       │
│  │ Debt/Equity  │ 0.84  │ Moderate, manageable            │
│  │ ROE          │ 158%  │ Exceptional capital efficiency  │
│  └──────────────────────┴──────────────────────────────────┘
│                                                             │
│  VALUATION ANALYSIS: Is it cheap, fair, or expensive?     │
│  ┌─────────────────────────────────────────────────────────┐
│  │ DCF Fair Value: $230 (vs current $215)                 │
│  │ Upside/Downside: +7% upside potential                  │
│  │ Valuation: Fair (within ±10% of fair value)            │
│  │                                                         │
│  │ Driver of valuation:                                   │
│  │ - 12% revenue growth baked in                          │
│  │ - 25% operating margin maintained                      │
│  │ - 5.25% discount rate reflects current Fed policy      │
│  └─────────────────────────────────────────────────────────┘
│                                                             │
│  TECHNICAL SETUP: Chart + momentum                         │
│  ┌─────────────────────────────────────────────────────────┐
│  │ [52-week chart, minimal styling]                       │
│  │                                                         │
│  │ Price action:                                           │
│  │ - Above 200-day MA (+8%)                               │
│  │ - RSI 62 (approaching overbought)                      │
│  │ - Volume above avg (accumulation phase)                │
│  └─────────────────────────────────────────────────────────┘
│                                                             │
│  RISK ASSESSMENT: What could go wrong?                    │
│  ┌─────────────────────────────────────────────────────────┐
│  │ Market Risk: Apple large-cap, lower volatility         │
│  │ Macro Risk: Elevated rates compress growth valuations   │
│  │ Competition Risk: Samsung, Chinese brands growing       │
│  │ Regulatory Risk: Antitrust scrutiny on app store       │
│  │ Execution Risk: New product cycles critical            │
│  │ Valuation Risk: Limited margin of safety               │
│  └─────────────────────────────────────────────────────────┘
│                                                             │
│  YOUR NOTES                                               │
│  ┌─────────────────────────────────────────────────────────┐
│  │ [Text area - save user's research notes]               │
│  │                                                         │
│  │ "Strong business, but premium valuation in high-rate   │
│  │ environment. Wait for pullback or earnings catalyst."  │
│  │                                                         │
│  │ Saved 2 days ago                                        │
│  └─────────────────────────────────────────────────────────┘
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Sections:**

1. **Macro Fit** (Top)
   - Current macro environment context
   - How it affects THIS specific stock
   - Fed rates → Valuation compression
   - Sector rotation implications

2. **Fundamentals**
   - P/E, PEG, dividend, FCF, debt/equity, ROE
   - Industry comparison benchmarks
   - Trend indicators (growing/declining)

3. **Valuation Analysis**
   - DCF fair value estimate
   - Upside/downside potential
   - Is it cheap, fair, or expensive?
   - What growth assumptions are baked in?

4. **Technical Setup**
   - Clean 52-week chart
   - Price vs moving averages
   - RSI/momentum
   - Volume trend

5. **Risk Assessment**
   - 5-6 key risks for THIS stock
   - Macro risk (market-wide)
   - Operational risk (company-specific)
   - Valuation risk (overpaid?)

6. **User Notes**
   - Sticky text area for research notes
   - Auto-save, timestamped
   - Carry forward to recommendation decision

**Design Notes:**
- Sections scroll vertically (long-form research)
- Heavy whitespace between sections
- Bold headings + clear hierarchy
- Data in readable tables/cards
- Charts minimal but informative
- Color coding: Green for positive, red for negative, neutral for neutral

---

### 3. Recommendation (RECOMMENDATION)
**Purpose:** Make the buy/hold/avoid decision with clear reasoning

```
┌─────────────────────────────────────────────────────────────┐
│  AAPL Recommendation                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  YOUR DECISION                                              │
│  ┌─────────────────────────────────────────────────────────┐
│  │                                                         │
│  │           HOLD                                          │
│  │      (Don't buy yet)                                    │
│  │                                                         │
│  │ Confidence: 7/10                                        │
│  │ Conviction: Moderate                                    │
│  │                                                         │
│  └─────────────────────────────────────────────────────────┘
│                                                             │
│  WHY HOLD (Not BUY)?                                        │
│  ┌─────────────────────────────────────────────────────────┐
│  │ ✓ Strong business, excellent fundamentals              │
│  │ ✓ Fair valuation (7% upside potential)                │
│  │ ✓ Technical setup shows strength                        │
│  │                                                         │
│  │ ✗ Limited margin of safety given macro headwinds       │
│  │ ✗ Fed rates elevated, growth premium compressed        │
│  │ ✗ Already above 200-day MA (confirmation bias risk)    │
│  │                                                         │
│  │ → BETTER PRICE TARGET: $200 (-7% from current)         │
│  │ → CATALYST: Earnings or Fed rate signals               │
│  └─────────────────────────────────────────────────────────┘
│                                                             │
│  ACTION ITEMS                                              │
│  ┌─────────────────────────────────────────────────────────┐
│  │ [✓] Set price alert: $200 (BUY trigger)               │
│  │ [✓] Monitor next earnings (Jan 28)                     │
│  │ [ ] Review if Fed cuts rates                           │
│  │ [ ] Reassess in 3 months                               │
│  └─────────────────────────────────────────────────────────┘
│                                                             │
│  ALTERNATIVE SCENARIOS                                     │
│  ┌──────────────────────┬──────────────────────────────────┐
│  │ IF Price drops to $200                                 │
│  │ → BUY (margin of safety created)                       │
│  │                                                         │
│  │ IF Fed cuts rates 1%                                   │
│  │ → UPGRADE to BUY (valuation multiple expands)          │
│  │                                                         │
│  │ IF Earnings miss forecast                              │
│  │ → DOWNGRADE to AVOID (growth story broken)             │
│  └──────────────────────┴──────────────────────────────────┘
│                                                             │
│  SAVE DECISION                                              │
│  ┌─────────────────────────────────────────────────────────┐
│  │ [Save Decision] [Edit] [Archive]                       │
│  │                                                         │
│  │ Saved as: "AAPL Hold @ $215 (June 7, 2026)"           │
│  └─────────────────────────────────────────────────────────┘
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Sections:**

1. **Your Decision** (Large, prominent)
   - BUY / HOLD / AVOID (bold, color-coded)
   - Confidence score (1-10)
   - One-line thesis

2. **Why This Decision?**
   - Pros (3-4 bullets with checkmarks)
   - Cons (3-4 bullets with X marks)
   - Clear trade-off summary

3. **Action Items**
   - Price alerts (set triggers)
   - Monitoring tasks (earnings date, catalyst)
   - Review schedule (quarterly reassessment)

4. **Alternative Scenarios**
   - If price moves X, what changes?
   - If macro shifts, what happens?
   - If company misses, downgrade to avoid
   - Forces thinking through scenarios

5. **Save Decision**
   - Timestamp and archive
   - Track history of your calls
   - Review accuracy over time (future)

**Design Notes:**
- Simple, bold typography
- Color-coded decision (green/neutral/red)
- Clear reasoning (pros vs cons)
- Forward-looking (what could change this?)
- Action-oriented (price alerts, review dates)

---

## Tab Navigation (Modern Minimal)

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  RESEARCH                PORTFOLIO              SIGNALS      │
│     ├─ Watchlist                                            │
│     ├─ Research Detail                                      │
│     └─ Decision                                             │
│                          ├─ Holdings                        │
│                          └─ Allocation                      │
│                                            ├─ Weekly        │
│                                            ├─ Archive       │
│                                            └─ Accuracy      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Simpler flow:**
- RESEARCH → All stock research (Plan → Analysis → Recommendation)
- PORTFOLIO → Holdings + allocation (future phase)
- SIGNALS → Generated Claude signals (existing feature)

---

## Key UX Principles (Modern Minimal)

1. **Whitespace as information architecture**
   - Big vertical gaps between sections
   - No information overload on single view
   - Scroll reveals deeper analysis

2. **Bold typography creates hierarchy**
   - Headline sizes vary significantly (2xl vs 4xl)
   - Weight contrast (700 bold for headers, 400 for body)
   - All-caps labels for metadata

3. **Color restraint**
   - Mostly grayscale
   - Green/red/neutral ONLY for sentiment/signals
   - No unnecessary gradients or shadows

4. **Cards over complexity**
   - Bordered cards group related concepts
   - Clean separation of concerns
   - Responsive stack on mobile

5. **Action-oriented language**
   - "Set price alert" not "Configure notification"
   - "View technicals" not "See chart"
   - Clear verbs, no jargon

---

## Implementation Roadmap

### Phase 1 (Now)
- [ ] Watchlist management (add/remove/organize)
- [ ] Research detail view (one-page scrollable)
- [ ] Recommendation decision (save + track)
- [ ] Modern minimal styling (CSS framework)

### Phase 2 (Next)
- [ ] Price alerts (set triggers on Research)
- [ ] Decision history (track accuracy)
- [ ] Portfolio integration (show holdings)

### Phase 3 (Future)
- [ ] Mobile app
- [ ] Collaboration (share research with friends)
- [ ] AI research assistant (auto-fill fundamentals)

---

## Components to Build

**React components:**
```
src/components/
├── Research/
│   ├── ResearchWatchlist.jsx       # Watchlist (Plan)
│   ├── ResearchDetail.jsx          # Deep dive (Analysis)
│   ├── RecommendationCard.jsx      # Decision + reasoning
│   ├── MacroFitSection.jsx         # Macro context
│   ├── FundamentalsTable.jsx       # P/E, dividend, etc.
│   ├── ValuationAnalysis.jsx       # DCF + upside/downside
│   ├── TechnicalChart.jsx          # 52-week chart
│   ├── RiskAssessment.jsx          # Risk factors
│   └── ResearchNotes.jsx           # User notes area
├── Common/
│   ├── Card.jsx                    # Reusable card
│   ├── MetricCard.jsx              # Single metric display
│   ├── BadgeGroup.jsx              # Signal/sentiment badges
│   └── ActionButton.jsx            # CTA buttons
└── Layout/
    ├── ResearchLayout.jsx          # Three-section layout
    └── TabNavigation.jsx           # RESEARCH | PORTFOLIO | SIGNALS
```

**Styling:**
```
- Tailwind CSS with custom colors
- Dark-friendly (supports light/dark mode)
- Responsive grid (mobile-first)
- Font: Inter (modern minimal standard)
```

---

## Success Metrics

**For the UX:**
- Can users find what they need to research a stock? (task completion)
- Do they understand the macro-to-decision flow? (concept clarity)
- Does the design feel modern and professional? (aesthetic satisfaction)
- Can they act on the recommendation? (actionability)

**For engagement:**
- Users build watchlists with 5+ stocks
- Users spend 5+ minutes on research detail
- Users make and save a recommendation decision
- Users set price alerts and track catalysts

---

**Ready to build?** This design pairs stock research education with a clean, modern interface that guides retail investors from curiosity to decision.

