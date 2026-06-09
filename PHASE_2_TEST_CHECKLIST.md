# Phase 2 Testing Checklist

**Date Started:** 2026-06-08  
**App URL:** http://localhost:5001  
**Backend:** http://localhost:5000  
**Test API:** http://localhost:5000/api/signals/short-term

---

## ✅ Component Rendering

### RecommendationStats Component
- [ ] Component renders without errors
- [ ] Average confidence displays correctly (shows number/10)
- [ ] Confidence bars fill correctly based on value
- [ ] Confidence color changes (green 8+, orange 6-7, red <6)
- [ ] Buy/Hold/Avoid counts display correctly
- [ ] "Last updated" shows time correctly
- [ ] Time ago updates every 30 seconds (watch for 1 minute)

### FilterBar Component
- [ ] Filter bar renders without errors
- [ ] Direction dropdown shows all options (All, Buy, Hold, Avoid)
- [ ] Confidence slider works (1-10)
- [ ] Confidence slider updates label in real-time
- [ ] Sector dropdown populated with sectors
- [ ] Active filters display when filters applied
- [ ] "Clear All" button appears only when filters active
- [ ] Stats pills show buy/hold/avoid counts

### SignalCardEnhanced Component
- [ ] Signal cards render without errors
- [ ] Ticker and sector display correctly
- [ ] Direction badge shows correct color (green/blue/red)
- [ ] Confidence bars render correctly (0-10)
- [ ] Confidence color matches direction
- [ ] Rationale text truncates at 2 lines
- [ ] "Show more" appears for long rationales
- [ ] Time ago displays ("2h ago" format)
- [ ] Win rate badge appears (if available)
- [ ] "Learn More" button is clickable

### Main ShortTerm Page
- [ ] Page header renders correctly
- [ ] Stats component displays at top
- [ ] Filter bar appears below stats
- [ ] Signal sections appear (Buy, Hold, Avoid)
- [ ] Section titles show with correct icons and colors
- [ ] Signals grouped correctly by direction
- [ ] Loading spinner appears on initial load
- [ ] Error message displays (if applicable)
- [ ] Empty state shows when no signals match filters

---

## 🔄 Filtering Functionality

### Direction Filter
- [ ] Select "Buy" → only buy signals appear
- [ ] Select "Hold" → only hold signals appear
- [ ] Select "Avoid" → only avoid signals appear
- [ ] Select "All" → all signals return
- [ ] Filter updates immediately
- [ ] Stats update to reflect filtered results

### Confidence Slider
- [ ] Drag slider to 7 → only 7+ confidence signals appear
- [ ] Drag slider to 9 → only 9+ confidence signals appear
- [ ] Slider label updates in real-time
- [ ] API called with correct min_confidence parameter

### Sector Filter
- [ ] Select a sector → only that sector appears
- [ ] Select "All Sectors" → all sectors appear
- [ ] Multiple sector selections work (if applicable)

### Combined Filters
- [ ] Direction=Buy + Confidence=8 → only buy signals with 8+ confidence
- [ ] Direction=Avoid + Sector=Technology → only avoid tech signals
- [ ] All three filters together work correctly

---

## 📊 Data Accuracy

### Stats Display
- [ ] Average confidence calculation is correct
- [ ] Buy count matches number of buy signals
- [ ] Hold count matches number of hold signals
- [ ] Avoid count matches number of avoid signals
- [ ] Total count is correct

### Signal Data
- [ ] Ticker symbols display correctly
- [ ] Confidence scores match backend response
- [ ] Direction (buy/hold/avoid) matches backend
- [ ] Rationale text is complete and readable
- [ ] Sector matches backend data

---

## 📱 Responsive Design

### Desktop (1400px+)
- [ ] Page width is centered and limited to 1200px
- [ ] Signal grid shows 3+ columns
- [ ] Stats grid shows 3 columns (confidence, direction, updated)
- [ ] Filter controls show inline (not stacked)
- [ ] All text is readable at this width

### Tablet (1024px)
- [ ] Signal grid shows 2 columns
- [ ] Stats grid shows appropriate column count
- [ ] Filter controls respond appropriately
- [ ] Touch targets are large enough (44px+)
- [ ] Spacing is appropriate for tablet

### Mobile (<768px)
- [ ] Signal grid shows 1 column (stacked)
- [ ] Stats stack vertically
- [ ] Filter bar is collapsed by default
- [ ] Filter toggle works (expand/collapse)
- [ ] All buttons are touch-friendly (44px+)
- [ ] Fonts are readable without zooming
- [ ] Horizontal scrolling doesn't occur

---

## 🎨 Visual Design

### Colors & Contrast
- [ ] Buy signals (green) have good contrast
- [ ] Hold signals (blue) have good contrast
- [ ] Avoid signals (red) have good contrast
- [ ] Text on backgrounds is readable (WCAG AA)
- [ ] Active filter tags stand out

### Typography
- [ ] Headers are clearly larger than body text
- [ ] Font sizes are consistent throughout
- [ ] Line heights are appropriate for readability
- [ ] Text truncation works correctly

### Spacing & Alignment
- [ ] Cards have consistent padding
- [ ] Gaps between elements are uniform
- [ ] Section titles are properly aligned
- [ ] Buttons are properly centered/aligned

---

## ⚡ Performance & Loading

### Initial Load
- [ ] Page loads without lag
- [ ] Loading spinner appears and disappears
- [ ] All components render within 2 seconds
- [ ] No console errors

### Filter Updates
- [ ] Applying filters is instant (no lag)
- [ ] Network request sent to backend
- [ ] Results update smoothly
- [ ] No page reflow/layout jank

### Real-time Updates
- [ ] "Time ago" updates without page refresh
- [ ] Updates happen every 30 seconds
- [ ] No memory leaks (check DevTools)

---

## 🐛 Error Handling

### Network Errors
- [ ] Network error shows clear message
- [ ] Error message suggests user action
- [ ] No broken UI after error

### Empty States
- [ ] Empty state appears when no signals match
- [ ] Message is helpful ("Try adjusting filters")
- [ ] Page is still usable

### Edge Cases
- [ ] 0 signals → empty state
- [ ] 1 signal → displays correctly
- [ ] 100 signals → all display, performance ok
- [ ] Very long rationale → "Show more" works

---

## 🔗 Integration

### With Existing Features
- [ ] Portfolio section still appears (if portfolio uploaded)
- [ ] CTA section appears (if no portfolio)
- [ ] Existing SignalCard components still work (portfolio recs)
- [ ] No conflicts with existing CSS

### Browser DevTools
- [ ] No console errors
- [ ] No console warnings
- [ ] Network tab shows successful requests
- [ ] Response times reasonable (<500ms)

---

## Test Summary

| Category | Status | Notes |
|----------|--------|-------|
| Components | ⭕ Pending | |
| Filtering | ⭕ Pending | |
| Data | ⭕ Pending | |
| Responsive | ⭕ Pending | |
| Design | ⭕ Pending | |
| Performance | ⭕ Pending | |
| Errors | ⭕ Pending | |
| Integration | ⭕ Pending | |

---

**Instructions:**
1. Open http://localhost:5001 in browser
2. Navigate to "📈 Recommendations" tab
3. Go through checklist items one by one
4. Check off items as you verify them
5. Note any issues in the Notes column
6. Report back with findings

---

**Test completed by:** [Your name]  
**Date completed:** [Date]  
**Issues found:** [Number]  
**Blockers:** [Any critical issues?]
