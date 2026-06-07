# Stock Recommendation MVP

AI-powered stock and ETF recommendations with macro context. Claude Opus analyzes fundamentals and economic indicators to deliver buy/hold/avoid signals weekly.

## Current Status

**Phase 1:** Signal generation ✅  
**Phase 2:** Email + Stripe subscription (next)

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- ANTHROPIC_API_KEY environment variable

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Set API key (required for signal generation)
export ANTHROPIC_API_KEY='sk-ant-...'

# Terminal 1: Start backend (port 5000)
python -m flask --app backend.api run --port 5000

# Terminal 2: Start frontend (port 5173)
cd frontend && npm run dev

# Open http://localhost:5173
```

### Generate Fresh Signals

```bash
cd backend
export ANTHROPIC_API_KEY='sk-ant-...'
python -c "from signals import generate_signals; import json; signals = generate_signals(5); print(json.dumps(signals, indent=2))"
```

## What It Does

- **AI Signal Generation** — Claude Opus analyzes 30+ stocks/ETFs combining fundamentals + macro context
- **Macro Integration** — Fed rates, inflation, VIX, USD strength incorporated into reasoning
- **Confidence Scoring** — 1-10 scale reflecting conviction (realistic 6-9 range, not inflated)
- **Signal Archive** — Browse past signals, filter by sector, track outcomes
- **Macro Context** — Real-time economic snapshot displayed with each signal

## Features

### This Week's Signals Tab
- Grid view of 5 latest signals
- Visual confidence bars (color-coded)
- Sector badge and market cap
- 2-3 sentence rationale referencing:
  - Specific P/E, dividend yield, price action
  - How macro conditions affect the thesis
  - Clear risk/reward view
- "View Details" link for full signal data

### Signal Archive Tab
- Table view of past 12 weeks
- Filter by sector (Tech, Finance, Healthcare, etc.)
- Columns: Ticker | Signal | Confidence | Sector | Date | Outcome | Accuracy
- Outcomes populated 30 days after signal (win/loss tracking)

### Macro Context Tab
- 9 economic indicators with current values
- Fed rate, inflation, VIX, DXY, Treasury yield, P/E, gold, GDP, EM trend
- Real-time fetch from yfinance

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/signals` | GET | Latest 5 signals |
| `/api/signals/archive` | GET | All past signals + filtering |
| `/api/signals/{id}` | GET | Single signal detail |
| `/api/signals/generate` | POST | Generate new signals (admin) |
| `/api/signals/accuracy` | POST | Update outcomes (scheduled) |
| `/api/macro` | GET | Macro indicators snapshot |

## Project Structure

```
portfolio-dashboard/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SignalList.jsx (+ .css)      # This week's signals
│   │   │   ├── SignalArchive.jsx (+ .css)   # Past signals table
│   │   │   ├── MacroTab.jsx                 # Macro indicators
│   │   │   ├── TabBar.jsx                   # Navigation
│   │   │   ├── Header.jsx                   # App header
│   │   │   └── *.jsx                        # Utility components
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── app.css
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
│
├── backend/
│   ├── api.py                 # Flask app + signal endpoints
│   ├── signals.py             # Signal generation engine
│   └── __pycache__/
│
├── .github/workflows/
│   └── deploy-to-azure.yml    # CI/CD pipeline
│
├── requirements.txt
├── macro_config.json
├── signals.json               # Generated signals (weekly)
├── FEATURE_ALIGNMENT.md       # Architecture docs
├── SIGNAL_ENGINE_ENHANCEMENTS.md  # Roadmap
├── ARCHITECTURE.md            # Technical design
└── README.md
```

## Signal Generation

### Process

1. **Fetch Fundamentals** — yfinance retrieves P/E, dividend, market cap for 30+ assets
2. **Get Macro Context** — Fetch Fed rate, inflation, VIX, USD strength
3. **Claude Analysis** — Opus analyzes fundamentals + macro environment together
4. **Output** — Structured JSON with direction (buy/hold/avoid), confidence (1-10), rationale
5. **Storage** — Signals saved to signals.json with timestamp for archiving

### Example Signal

```json
{
  "ticker": "JPM",
  "direction": "buy",
  "confidence": 8,
  "sector": "Financial Services",
  "rationale": "P/E 14.9 with 1.92% dividend. High Fed rate (5.25%) boosts net interest margins for this well-capitalized bank. Inflation at 3.2% supports manageable credit conditions.",
  "created_at": "2026-06-07T00:02:24",
  "result": null,
  "accuracy_pct": null
}
```

## Development Notes

### Key Decisions

- **Claude Opus** — Most capable model for nuanced financial reasoning combining fundamentals + macro
- **30+ Candidates** — Diversified across Tech, Finance, Healthcare, Energy, Consumer, Real Estate, ETFs
- **Macro Integration** — High rates = compress tech multiples, boost bank NIMs; key for sector rotation
- **Realistic Confidence** — 6-9 range (not 7-10); reflects actual uncertainty
- **JSON Storage** — Simple, transparent, git-friendly (no database complexity)
- **Weekly Cadence** — Matches market rhythm; prevents signal fatigue

### Testing Signals

Before going live, verify generated signals:
- ✓ Confidence distribution (mix of 6/7/8, not all 8s)
- ✓ Sector diversity (not 4/5 tech stocks)
- ✓ BUY/HOLD/AVOID balance (realistic ratios)
- ✓ Macro reasoning (rates/inflation clearly connected)
- ✓ Risk awareness (mentions downside scenarios)

## Deployment

### Local Testing
```bash
# Two terminals:
# Terminal 1
python -m flask --app backend.api run --port 5000

# Terminal 2
cd frontend && npm run dev
```

### Production (Railway.app)
```bash
# Push to GitHub
git push origin main

# Railway auto-deploys on push
# Frontend: https://portfolio-dashboard-production-xxxx.up.railway.app
# Backend: Same URL, /api/* routes
```

## Roadmap

### Phase 1: MVP ✅
- Signal generation with Claude
- Macro context integration
- React UI (Signal List + Archive)
- Expanded candidate pool (30+ assets)

### Phase 2: Monetization (Next 4 weeks)
- Email delivery (Resend)
- Stripe subscription paywall ($29/month)
- User authentication
- Account management

### Phase 3: Sophistication (Future)
- 30-day accuracy tracking
- B2B API tier with webhooks
- Advanced filtering (sector, confidence, market cap)
- Portfolio integration
- Signal performance leaderboard

## License

MIT

## Author

Built with Claude Code and Anthropic's Claude Opus API.
Recovering lost code from dangling git commits and rebuilding for the stock recommendation market.
