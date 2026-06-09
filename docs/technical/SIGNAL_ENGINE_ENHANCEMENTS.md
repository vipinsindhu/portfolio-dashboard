# Signal Engine Enhancement Plan

## Current State
- ✅ 15 stocks/ETFs in candidate pool (mostly tech)
- ✅ Claude Opus generating solid signals
- ✅ Fundamentals-focused (P/E, dividends, price action)
- ❌ Limited sector diversity (heavy tech)
- ❌ No macro context integration
- ❌ No bond/fixed income recommendations

## Enhancement Goals

### 1. Expand Candidate Pool (Current: 15 → 30+)
**More sectors:**
- Technology: AAPL, MSFT, GOOGL, NVDA, META (5) ✓
- Healthcare: JNJ, UNH, PFE, ABBV, TMO (5) NEW
- Financials: JPM, BAC, GS, BLK, AXP (5) NEW
- Energy: XOM, CVX, COP (3) NEW
- Consumer: AMZN, WMT, HD, MCD, NKE (5) NEW
- Real Estate: SPG, PLD, VICI (3) NEW
- Industrials: BA, CAT, GE (3) NEW
- ETFs: VTI, VOO, VWO, AGG, BND, GLD (6) ✓

**Result:** Better diversification, appeals to different investor types

### 2. Integrate Macro Context
**Fetch macro indicators:**
- Fed Funds Rate (FRED API)
- 10-Year Treasury Yield
- VIX (Volatility Index)
- USD Index (DXY)
- Inflation (CPI from FRED)

**Include in signal context:**
```
Macro Environment:
- Fed Rate: 5.0% (restrictive)
- VIX: 15.2 (calm markets)
- Dollar: Strong (impacts exporters)
- Inflation: 3.5% (above target)

Implication: Value/Dividend stocks better positioned
             Growth premium compressed
             Emerging markets pressured by strong dollar
```

**Signal prompt enhancement:**
- "In current environment (high rates, low VIX), generate signals..."
- "Consider how Fed policy affects sector positioning..."
- "Account for USD strength vs EM weakness..."

### 3. Add Bond/Fixed Income Recommendations
**Fixed income candidates:**
- AGG (Aggregate Bonds)
- BND (Total Bond)
- TLT (20+ Year Treasuries)
- HYG (High Yield Bonds)
- VCIT (Intermediate Corporate)

**When to recommend:**
- Rising rates → Extend duration
- Falling rates → Reduce duration
- Credit spreads wide → High yield attractive
- Recession risk → Duration protection

### 4. Improve Signal Rationale Quality

**Add these dimensions:**

a) **Relative Value**
   - "Cheap vs 3-year average" 
   - "Discount to industry peers"
   - Instead of just: "Reasonable P/E"

b) **Catalyst/Timeline**
   - "FDA approval expected Q3"
   - "Earnings revision cycle turning"
   - "Valuation inflection point approaching"

c) **Risk/Reward**
   - "Asymmetric risk-reward: 20% upside, 5% downside"
   - "Downside protected by dividend"
   - "Execution risk on integration"

d) **Portfolio Context**
   - "Complement value tilt"
   - "Uncorrelated to tech holdings"
   - "Hedge against rate volatility"

### 5. Enhanced Confidence Scoring

**Current:** 1-10 based on fundamentals

**Enhanced:** 1-10 based on:
- Fundamental score (40%)
- Macro alignment (30%)
- Technical setup (20%)
- Catalyst clarity (10%)

**Example:**
- META: Fundamentals 8/10, Macro alignment 8/10 (value favored), Tech 7/10, Catalysts 8/10 → 8/10 overall
- TSLA: Fundamentals 3/10 (P/E 358), Macro 4/10, Tech 8/10, Catalysts 5/10 → 4/10 (AVOID)

## Implementation Order

### Week 1: Macro Integration
- [ ] Add FRED API calls for economic indicators
- [ ] Fetch VIX, DXY
- [ ] Include macro snapshot in Claude prompt
- [ ] Test with current candidates

### Week 2: Expand Candidate Pool
- [ ] Add 15+ new stocks (Healthcare, Energy, Consumer, Real Estate)
- [ ] Add 5 fixed income ETFs
- [ ] Test yfinance data fetch for all (30 candidates)
- [ ] Ensure all sectors represented

### Week 3: Enhance Rationales
- [ ] Update Claude prompt with multi-dimensional analysis
- [ ] Add catalyst/timeline component
- [ ] Add relative value comparisons
- [ ] Add portfolio context suggestions

### Week 4: Quality Testing & Polish
- [ ] Generate 10 signal batches, review for quality
- [ ] Validate macro logic is sensible
- [ ] Check sector balance (should vary week to week)
- [ ] Stress test with different market conditions
- [ ] Deploy enhanced engine

## Code Changes Required

### backend/signals.py
```python
# New functions:
- fetch_macro_context()  # FRED + yfinance APIs
- get_expanded_candidates()  # 30+ stocks/ETFs
- enhance_signal_prompt()  # Multi-dimensional analysis
- calculate_composite_confidence()  # 4-factor scoring
```

### backend/api.py
```python
# New endpoints:
- GET /api/macro-context  # Current macro snapshot
- POST /api/signals/batch  # Generate N batches for review
```

## Success Criteria

After enhancements, signals should:
- ✅ Cover 8+ sectors (not just tech)
- ✅ Include bond recommendations
- ✅ Reference macro environment
- ✅ Show specific catalysts/timelines
- ✅ Display confidence factors
- ✅ Average confidence 6-7 (realistic, not inflated)
- ✅ Mix of BUY/HOLD/AVOID ratios varies week-to-week
- ✅ Include relative value comparisons

## Timeline
**Total: 4 weeks**
- Week 1: Macro + testing
- Week 2: Candidate expansion
- Week 3: Rationale enhancement
- Week 4: Quality review + deploy

---

After this, you'll have:
✅ Production-grade signal engine
✅ Comprehensive coverage (stocks, bonds, sectors, macro)
✅ Sophisticated multi-factor analysis
✅ Ready for Phase 2 (Email + Stripe)
