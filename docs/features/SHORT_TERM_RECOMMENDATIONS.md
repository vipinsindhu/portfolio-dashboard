# Short-Term Investment Recommendations Page

Plan for building a dedicated recommendations tab showing top buy/avoid signals for the week.

---

## 🎯 Requirements Summary

**What:** Standalone page showing top 10 stock recommendations (buy/avoid) for short-term trading (1-7 day horizon)  
**Integration:** New tab alongside Portfolio, Analyse, Learn  
**Data Source:** Groq LLM signals (auto-generated hourly)  
**Target User:** Beginner investors looking for quick trading opportunities  
**Language:** Simplified, beginner-friendly explanations  

---

## 🏗️ Architecture Overview

### Current Signal Infrastructure (Already Built)
```
API Endpoints:
- GET /api/signals          → Latest 5 signals
- GET /api/signals/archive  → Past signals, filterable by sector
- GET /api/signals/<id>     → Signal details
- POST /api/signals/generate → Manual generation (admin)

Components:
- SignalCard.jsx           → Individual signal display
- SignalList.jsx           → List of signals
- SignalArchive.jsx        → Past signals search/filter
- RecommendationView.jsx   → Current recommendation display
```

### What We Need to Add
```
New Page:
- ShortTermRecommendations.jsx  (main page)

New Components:
- RecommendationFilter.jsx      (filter by direction: buy/avoid/hold)
- RecommendationStats.jsx       (meta info: avg confidence, last updated)
- RecommendationGrid.jsx        (grid/list view toggle)
- SignalDetails.jsx             (expanded view with rationale)

New API:
- GET /api/signals/short-term   (get top 10 buy/avoid signals)

Styling:
- ShortTermRecommendations.css
```

---

## 📊 Data Model

### Current Signal Structure (from signals.py)
```python
{
  "id": "sig_12345",
  "ticker": "AAPL",
  "direction": "buy|hold|avoid",
  "confidence": 1-10,
  "rationale": "Apple showing strong momentum with....",
  "sector": "Technology",
  "market_cap": 2800000000000,
  "created_at": "2026-06-08T10:30:00",
  "result": null|"win"|"loss",
  "accuracy_pct": null|0|100
}
```

### What We Need to Add

**Filter/Sort Options:**
- Direction filter (Buy, Hold, Avoid)
- Confidence threshold (show only 7+ confidence)
- Sector filter (optional)
- Sort by confidence, recency, or sector

**Display Enhancements:**
- Show "time since generated" (e.g., "2 hours ago")
- Color-code by confidence level
- Show accuracy if available
- Display relevant market context

---

## 🎨 UI/UX Design

### Page Layout
```
┌─────────────────────────────────────────────────────┐
│ Short-Term Investment Recommendations               │
│ Top opportunities this week based on market signals │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 📊 Stats                                            │
│ Avg Confidence: 7.2/10 | Last Updated: 2 hours ago│
│ Buy Signals: 4 | Avoid: 3 | Hold: 3                │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Filters: [All Signals ▼] [All Sectors ▼] [View: Grid]│
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 🟢 AAPL - BUY (9/10)                               │
│ Strong momentum with positive earnings expectations │
│ Tech | 2h ago | Win rate: 85%                      │
├─────────────────────────────────────────────────────┤
│ 🔴 TSLA - AVOID (8/10)                             │
│ Overbought conditions with declining sentiment     │
│ Tech | 2h ago | Win rate: 92%                      │
├─────────────────────────────────────────────────────┤
│ ⏸️  MSFT - HOLD (6/10)                              │
│ Mixed signals, wait for clearer direction          │
│ Tech | 1h ago | Win rate: 78%                      │
└─────────────────────────────────────────────────────┘
```

### Color Scheme
```
Buy (Green):     #0d7d3b or #22c55e
Hold (Blue):     #5568d3 or #3b82f6
Avoid (Red):     #dc3545 or #ef4444
Confidence:
  8-10 (High):   Dark/saturated color
  6-7 (Medium):  Medium saturation
  1-5 (Low):     Desaturated/faded
```

---

## 💾 Implementation Plan

### ✅ Phase 1: Backend Enhancement (COMPLETE)

**✅ 1. Updated API endpoint:**
- Endpoint: `GET /api/signals/short-term`
- Location: [backend/api.py](../../backend/api.py) (lines ~189-265)
- Status: **IMPLEMENTED & TESTED**

**Implemented features:**
```python
@app.route("/api/signals/short-term", methods=["GET"])
def get_short_term_signals():
    """Get top 10 buy/avoid signals for short-term trading
    
    Query parameters:
    - limit: number of signals to return (default: 10)
    - direction: filter by direction (buy/hold/avoid, default: all)
    - min_confidence: minimum confidence threshold (1-10, default: 6)
    - sector: filter by sector (default: all)
    
    Returns:
    {
      "signals": [...],           # top N signals sorted by confidence
      "total": 10,                # number of signals returned
      "generated_at": "2026-06-08T10:30:00",  # last signal generation time
      "stats": {
        "avg_confidence": 7.5,    # average confidence of returned signals
        "buy_count": 4,           # signals with direction=buy
        "hold_count": 2,          # signals with direction=hold
        "avoid_count": 4,         # signals with direction=avoid
        "by_direction": {...}     # breakdown by direction
      },
      "filters": {
        "min_confidence": 6,      # applied filters
        "direction": "all",
        "sector": "all"
      }
    }
    ```

**Filtering & sorting logic:**
- ✅ Gets latest 50 signals from signal_store
- ✅ Filters by: confidence >= min_confidence, direction (optional), sector (optional)
- ✅ Sorts by confidence (descending)
- ✅ Returns top N with calculated stats
- ✅ Includes error handling with try/catch

**2. ✅ Metadata tracking:**
- Signal "age" can be calculated from created_at vs current time (frontend responsibility)
- Win rate already available in signal structure (from archive)
- Confidence-based strength categorization ready for frontend

---

### ✅ Phase 2: Frontend Page (COMPLETE)

**✅ Created new components:**

1. **RecommendationStats.jsx** - Display statistics
   - Average confidence meter with color-coded levels
   - Signal counts by direction (buy, hold, avoid)
   - Last updated time with auto-refresh hint
   - Real-time "time ago" updates every 30 seconds
   - Responsive grid (3 cards desktop, 1 mobile)
   - Location: [frontend/src/components/tabs/ShortTerm/RecommendationStats.jsx](../../frontend/src/components/tabs/ShortTerm/RecommendationStats.jsx)

2. **FilterBar.jsx** - Filtering controls
   - Direction filter (All/Buy/Hold/Avoid)
   - Confidence slider (1-10 threshold)
   - Sector dropdown (11 common sectors)
   - Active filters display with tags
   - Clear All button
   - Stats summary showing current counts
   - Expandable/collapsible on mobile
   - Location: [frontend/src/components/tabs/ShortTerm/FilterBar.jsx](../../frontend/src/components/tabs/ShortTerm/FilterBar.jsx)

3. **SignalCardEnhanced.jsx** - Individual signal display
   - Ticker with sector and direction badge
   - Confidence visualization (10-bar chart)
   - Rationale with "show more" expansion
   - Time indicator ("2h ago" format)
   - Win rate badge (if available)
   - Color-coded by direction (green/blue/red)
   - Smooth hover animations
   - "Learn More" button
   - Location: [frontend/src/components/tabs/ShortTerm/SignalCardEnhanced.jsx](../../frontend/src/components/tabs/ShortTerm/SignalCardEnhanced.jsx)

4. **Updated ShortTerm.jsx** - Main page orchestration
   - Integrated all new components
   - Real-time filter refetching
   - Signals grouped by direction
   - Loading and error states
   - Portfolio recommendations section
   - Call-to-action for portfolio upload
   - Responsive layout (3 breakpoints)
   - Location: [frontend/src/components/tabs/ShortTerm/ShortTerm.jsx](../../frontend/src/components/tabs/ShortTerm/ShortTerm.jsx)

**CSS Files Created:**
- RecommendationStats.css (~130 lines)
- FilterBar.css (~250 lines)
- SignalCardEnhanced.css (~280 lines)
- ShortTerm.css (updated with new sections)

**Responsive Design:**
- ✅ Desktop (1400px+): 3-column grid, full filter controls
- ✅ Tablet (1024px): 2-column grid, collapsible filters
- ✅ Mobile (<768px): 1-column stack, mobile-optimized filters

---

### ✅ Phase 3: Polish & Integration (COMPLETE)

**What's Done:**

**1. ✅ Navigation Integration:**
- "📈 Short-term" tab already present in main app navigation
- ShortTerm component fully integrated in App.jsx
- Tab displays alongside Learn, Analyse, Long-term tabs
- Navigation between tabs works smoothly

**2. ✅ Auto-Refresh Implementation:**
- Manual refresh button with loading state
- Auto-refresh every 60 minutes (matches signal generation)
- Button shows "🔄 Refresh" (idle) or "⏳ Refreshing..." (loading)
- Disabled during refresh to prevent duplicate requests
- Console logging for debugging

**3. ✅ UI/UX Improvements:**
- Header reorganized with refresh button placement
- Responsive button layout (inline desktop, stacked mobile)
- Hover effects and smooth transitions
- Loading state feedback visible to users

**4. ✅ Responsive Design:**
- Desktop (1400px+): Refresh button inline with header
- Tablet (1024px): Refresh button stacks below header
- Mobile (<768px): Full-width button for easy tapping

---

## 🎯 Feature Status: PRODUCTION READY ✅

The short-term investment recommendations feature is complete and ready for production with:
- ✅ Fully functional backend API
- ✅ Beautiful, responsive frontend
- ✅ Auto-refresh capabilities
- ✅ Manual refresh controls
- ✅ Integrated navigation
- ✅ Comprehensive documentation

---

## 📚 Implementation Documentation

See detailed documentation for each phase:
- [Phase 1 Backend](PHASE_1_SHORT_TERM_COMPLETE.md) - API endpoint implementation
- [Phase 2 Frontend](PHASE_2_SHORT_TERM_COMPLETE.md) - Component development
- [Phase 3 Polish](PHASE_3_SHORT_TERM_COMPLETE.md) - Integration and auto-refresh

---

## 🔄 Future Enhancements (Optional)

These features could be added later:
- Signal details modal with full rationale
- Watchlist functionality
- Share signal button
- Historical accuracy charts by sector
- Email/push notifications
- Signal comparison with user's portfolio

---

## 📝 File Structure

```
frontend/src/
├── pages/
│   └── ShortTermRecommendations.jsx  (main page)
│
├── components/
│   ├── Recommendation/
│   │   ├── RecommendationStats.jsx
│   │   ├── RecommendationStats.css
│   │   ├── FilterBar.jsx
│   │   ├── FilterBar.css
│   │   ├── RecommendationGrid.jsx
│   │   ├── RecommendationGrid.css
│   │   ├── SignalCardEnhanced.jsx
│   │   └── SignalCardEnhanced.css
│   │
│   └── shared/
│       └── (existing SignalCard.jsx - reuse)
│
└── styles/
    └── ShortTermRecommendations.css

backend/src/
├── api.py (add /api/signals/short-term endpoint)
├── signals.py (add helper functions)
└── (no schema changes needed)
```

---

## 🧪 Testing Strategy

**Frontend:**
- Render with different signal counts (0, 1, 10, 20)
- Test filters (direction, sector, confidence)
- Test responsive layout (mobile, tablet, desktop)
- Test loading/error states

**Backend:**
- Test endpoint with various query params
- Verify filtering logic
- Check stats calculation
- Benchmark performance (50 signals → top 10 should be fast)

**Integration:**
- Signals update → Page refreshes (via polling or WebSocket?)
- Filter + sort work together correctly
- Stats update when filters change

---

## ⏱️ Timeline

| Phase | Tasks | Duration |
|-------|-------|----------|
| 1 | Backend endpoint + logic | 2-3 days |
| 2 | Frontend page + components | 3-4 days |
| 3 | Polish + integration | 2-3 days |
| Testing + QA | | 2-3 days |
| **Total** | | **9-13 days** |

---

## 🎯 Success Criteria

✅ Page displays top 10 buy/avoid signals for the week  
✅ Filters work (direction, sector, confidence)  
✅ Stats show accurate counts and averages  
✅ Mobile responsive and accessible  
✅ Signal updates reflect hourly generation  
✅ Performance < 1s load time  
✅ Beginner-friendly language throughout  
✅ Win rate displayed for applicable signals  

---

## 🔄 Data Flow

```
Groq LLM (hourly)
     ↓
generate_signals() → 50 new signals
     ↓
signal_store.save_signals()
     ↓
signals.json / Database
     ↓
GET /api/signals/short-term
     ↓
ShortTermRecommendations.jsx
     ↓
Display top 10 to user
```

---

## 🚀 Potential Enhancements (Future)

- 📊 Chart historical accuracy by sector
- 📍 Map signals to user's portfolio (highlight relevant signals)
- 🔔 Notifications for new high-confidence signals
- 📱 Widget showing latest signal
- 💾 Save signals to watchlist
- 📈 Track signal performance over time
- 🤖 AI explanation of why signals changed
- 📧 Email digest of daily top signals

---

## Questions Before Starting

1. Should we auto-refresh the page? (Every 5 mins? When new signals arrive?)
2. Do you want a "Details" page for each signal? (Show full rationale + context)
3. Should we show historical performance of signals? (Win rate per sector?)
4. Any preferred way to handle time zones? (User's local or UTC?)
5. Minimum confidence threshold? (Currently using 6+, good?)

---

**Ready to start Phase 1?**

---

**Last Updated:** 2026-06-08
