# Stock Recommendation MVP - Technical Architecture

## Overview

Signal-generation-focused stock recommendation engine combining Claude AI, real-time fundamentals, and macro economic context.

**Core Thesis:** Rate environment drives sector rotation. Claude Opus can integrate fundamentals + macro into a coherent investment signal that's better than either alone.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React/Vite)                    │
│  - SignalList: Weekly signals in card grid                      │
│  - SignalArchive: Past signals with sector filtering            │
│  - MacroTab: Economic context snapshot                          │
│  - TabBar: Navigation                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (Flask/Python)                     │
│                                                                 │
│  API Layer (backend/api.py):                                   │
│  ├── GET /api/health              → 200 OK                    │
│  ├── GET /api/signals             → Latest 5 signals          │
│  ├── GET /api/signals/archive     → All signals + filtering   │
│  ├── GET /api/macro               → Macro snapshot            │
│  ├── POST /api/signals/generate   → Trigger Claude generation │
│  └── POST /api/signals/accuracy   → Update 30-day outcomes    │
│                                                                 │
│  Signal Engine (backend/signals.py):                           │
│  ├── fetch_macro_context()        → Fed rate, VIX, DXY, etc.  │
│  ├── get_macro_sentiment()        → Readable macro summary    │
│  ├── fetch_fundamentals(ticker)   → P/E, dividend, cap, etc.  │
│  ├── generate_signals(count)      → Claude + yfinance         │
│  ├── load_signals()               → Read signals.json         │
│  ├── save_signals()               → Write signals.json        │
│  └── update_signal_accuracy()     → Track 30-day outcomes     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    External Data Sources                        │
│  ├── yfinance: P/E, dividend, market cap, VIX, Treasury, etc. │
│  ├── Claude Opus API: Signal generation + reasoning            │
│  └── FRED API: Economic data (optional future expansion)       │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Signal Generation Sequence

```
1. User clicks "Generate Signals" (or POST /api/signals/generate)
   ↓
2. Backend fetches data in parallel:
   ├── fetch_macro_context() → Fed rate, VIX, DXY, inflation
   └── fetch_fundamentals(30 tickers) → P/E, dividend, market cap, price action
   ↓
3. Prepare Claude prompt:
   - List 15 top candidates with their fundamentals
   - Include macro sentiment ("Fed rate is restrictive at 5.25%...")
   - Request 5 signals with specific format
   ↓
4. Claude Opus analyzes:
   - Which stocks look cheap/expensive in macro context?
   - How do rates affect sector rotation?
   - What's the risk/reward for each candidate?
   ↓
5. Return structured JSON:
   [
     {
       "ticker": "JPM",
       "direction": "buy",
       "confidence": 8,
       "rationale": "P/E 14.9... high rates boost NIM... manageable credit",
       "sector": "Financial Services",
       "market_cap": 836998922240,
       "created_at": "2026-06-07T00:02:24.274238"
     },
     ...
   ]
   ↓
6. Save to signals.json (appends to array)
   ↓
7. Return latest N signals to frontend
```

### Request Flow (User Perspective)

```
User opens http://localhost:5173
  ↓
React mounts, calls GET /api/signals
  ↓
Backend returns { data: [...], generated_at: "..." }
  ↓
SignalList component renders cards:
  - JPM: BUY 8/10 (Green border, confidence bar)
  - PFE: BUY 7/10 (Green border, confidence bar)
  - AAPL: HOLD 6/10 (Yellow border, confidence bar)
  - etc.
  ↓
User clicks "Signal Archive"
  ↓
SignalArchive component:
  - Fetches GET /api/signals/archive
  - Renders table with past signals
  - Allows filtering by sector dropdown
  - Shows outcomes (win/loss) for signals 30+ days old
```

## Signal Model

```typescript
Signal {
  id: string                 // "AAPL_2026-06-07T10:00:00"
  ticker: string            // "AAPL"
  direction: "buy" | "hold" | "avoid"
  confidence: number        // 1-10, typically 6-9
  rationale: string         // 2-3 sentences from Claude
  sector: string            // "Technology", "Financial Services", etc.
  market_cap: number | null // In dollars
  created_at: string        // ISO timestamp
  result: "win" | "loss" | null  // Set after 30 days
  accuracy_pct: number | null    // Binary outcome 0 or 100
}
```

## Macro Context

### What We Track

| Indicator | Source | Frequency | Used For |
|-----------|--------|-----------|----------|
| Fed Funds Rate | Manual | Latest | "Restrictive" vs "Accommodative" messaging |
| Inflation | Manual | Quarterly estimate | "Above target" → credit pressure |
| VIX | yfinance | Real-time | "Calm markets" vs "High volatility" |
| DXY (USD Index) | yfinance | Real-time | "Strong dollar pressures exporters" |
| 10-Year Treasury | yfinance | Real-time | "Elevated rates compress growth valuations" |
| P/E Ratio (S&P 500) | yfinance | Real-time | Valuation context for stock picks |

### Macro Sentiment Logic

```python
def get_macro_sentiment(macro_data):
  """
  Converts numeric macro data into readable English for Claude prompt.
  
  Example:
    Fed 5.25% + Inflation 3.2% + VIX calm 15.2 + DXY strong 105
    ↓
    "Fed Funds Rate elevated at 5.25% (restrictive). Inflation moderate 
    at 3.2%. VIX is calm at 15.2 (low volatility). USD strong at 105.2 
    (headwind for exporters)."
  """
  
  This text gets embedded in Claude's prompt so it understands
  the macro environment without explicit scoring.
```

## Confidence Scoring

**Current:** 1-10 scale, empirically calibrated by Claude

**Ideal distribution:**
- 6: Uncertain, multiple scenarios plausible
- 7: Good thesis but some execution risk
- 8: Strong conviction, macro + fundamentals aligned
- 9: Rare, only for obvious mispricings

**NOT used:** Formula-based scoring. Claude judges in context of macro + fundamentals simultaneously.

## Signal Storage

**Format:** JSON array, human-readable

**Location:** `signals.json` in repo root

**Structure:**
```json
{
  "signals": [
    { signal objects, newest first },
    ...
  ],
  "generated_at": "2026-06-07T00:02:24Z"
}
```

**Advantages:**
- Git-friendly (easy to see changes)
- Transparent (can inspect raw data)
- No database complexity
- Portable (JSON is standard)

**Limitations:**
- Not optimized for large-scale queries (but 52 weeks × 5 signals = ~260 entries, totally fine)
- No real-time write conflict handling (but single-threaded signal generation prevents issues)

## API Design Decisions

### REST Endpoints

**Why GET for historical data:**
- `GET /api/signals` (latest)
- `GET /api/signals/archive` (all)
- `GET /api/signals/{id}` (detail)

Queries are idempotent; no state mutation.

**Why POST for operations:**
- `POST /api/signals/generate` (create)
- `POST /api/signals/accuracy` (update outcomes)

These mutate server state.

### Response Format

```json
GET /api/signals → {
  "data": [ ... ],
  "generated_at": "2026-06-07T00:02:24Z",
  "total": 5
}
```

Consistent envelope for pagination/metadata in Phase 2.

## Frontend Architecture

### Component Hierarchy

```
App
├── Header (last updated, refresh button)
├── TabBar (navigation: Signals | Archive | Macro)
└── Content (one of):
    ├── SignalList (grid of signal cards)
    ├── SignalArchive (table with filtering)
    └── MacroTab (9 indicators)
```

### State Management

**App.jsx owns:**
- `signals` — Latest signals from /api/signals
- `activeTab` — Current tab ("signals", "archive", "macro")
- `refreshing` — Loading state during generation
- `error` — Error message display

**Child components:**
- `SignalArchive` — Owns `selectedSector` filter state

### Styling Approach

**Color scheme for directions:**
- Buy (Green): #10b981 background, #166534 text
- Hold (Yellow): #fef3c7 background, #92400e text
- Avoid (Red): #fee2e2 background, #7f1d1d text

**Responsive breakpoints:**
- Desktop: Full grid (3+ columns)
- Tablet: 2 columns
- Mobile: 1 column

## Deployment Architecture

### Local Development

```
Frontend: npm run dev        → http://localhost:5173 (Vite)
Backend:  flask run --port 5000 → http://localhost:5000 (Flask)
```

Both run in separate processes; frontend proxies /api/* to backend via Vite config.

### Production (Railway.app)

```
├── Frontend Container
│   ├── Node 18 base
│   ├── npm install && npm run build
│   └── serve dist/ via Nginx
│
└── Backend Container
    ├── Python 3.10 base
    ├── pip install -r requirements.txt
    └── gunicorn api:app (or Flask if B1 tier)
```

Both served from single Railway.app project; frontend calls backend at /api/* on same domain.

## Key Implementation Details

### Candidate Pool Selection

30 stocks/ETFs spanning 8 sectors:
- **Tech** (5): AAPL, MSFT, GOOGL, NVDA, META
- **Finance** (4): JPM, BAC, GS, BLK
- **Healthcare** (3): JNJ, UNH, PFE
- **Consumer** (4): AMZN, WMT, HD, MCD
- **Energy** (2): XOM, CVX
- **Real Estate** (2): SPG, PLD
- **ETFs** (6): VTI, VOO, VWO, AGG, BND, GLD

Claude selects top 5 based on fundamental + macro fit.

### Claude Prompt Structure

```
You are a stock analyst. Generate 5 investment signals considering
both fundamental analysis and the current macro environment.

CURRENT MACRO ENVIRONMENT:
[Macro sentiment summary]

CANDIDATE STOCKS/ETFS:
[JSON with P/E, dividend, market cap, sector]

For each signal, provide:
1. Ticker
2. Direction (buy/hold/avoid)
3. Confidence (1-10)
4. Rationale (2-3 sentences including specific metrics + macro connection)

Return ONLY the JSON array, no other text.

IMPORTANT:
- Mix of BUY, HOLD, AVOID
- Confidence varied 5-9 (realistic)
- Include specific numbers (P/E, yield, etc.)
- Connect to macro environment
```

This structure:
- ✓ Forces specific metrics in response
- ✓ Prevents hallucinations (JSON-only)
- ✓ Encourages macro reasoning
- ✓ Calibrates confidence realistically

## Error Handling

### Signal Generation Failures

- yfinance API down → Log error, return empty candidates list
- Claude API error → Return HTTP 500 with error message
- Missing ticker data → Skip that ticker, continue with others

### Storage Failures

- signals.json missing → Create empty structure on first write
- Write error → Return HTTP 500, do NOT corrupt existing data
- Concurrent writes → Single-threaded signal generation prevents this

## Future Extensions

### Phase 2: Monetization
- Add user auth layer
- Stripe subscription enforcement (free users see sample signal only)
- Email delivery via Resend

### Phase 3: Sophistication
- Accuracy dashboard (historical win rate by sector/type)
- B2B API tier with usage metering
- Advanced filtering (time range, confidence threshold, outcome)
- Portfolio integration (surface signals relevant to user's holdings)

### Beyond
- Machine learning on signal quality vs market performance
- Custom portfolio analysis
- Alerts/notifications for macro threshold breaches
- Mobile app wrapper

## Testing Strategy

### Unit Tests (Future)
- `test_fetch_fundamentals()` — yfinance integration
- `test_get_macro_sentiment()` — Macro rendering
- `test_generate_signals()` — Claude integration (mock API)

### Integration Tests (Future)
- End-to-end signal generation + storage + retrieval
- Archive filtering
- Accuracy tracking

### Manual Testing (Current)
- Verify generated signals have realistic confidence distribution
- Verify sector diversity
- Verify macro reasoning in rationales
- Check UI renders signals correctly

---

**Last updated:** 2026-06-07  
**Version:** Phase 1 (Signal Generation MVP)
