# Portfolio Builder 📊

Macro-aware investment planning with real-time economic indicators and portfolio management.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/vipinsindhu/portfolio-dashboard)

## Quick Start

### 🚀 Easiest: GitHub Codespaces (no install needed)
Click the badge above or [open in Codespaces](https://codespaces.new/vipinsindhu/portfolio-dashboard), then:
```bash
docker-compose up --build
```
Visit `http://localhost:5001` in the browser preview.

### 💻 Local Docker
```bash
docker-compose up --build
# Open http://localhost:5001
```

### 🏃 Mac/Linux
```bash
chmod +x start.sh
./start.sh
```

### 🏃 Windows
```bash
.\start.bat
```

## What It Does

- **📈 Macro Dashboard** — 9 key indicators (Fed rate, inflation, VIX, gold, Treasury yield, P/E ratio, GDP, dollar index, EM trend)
- **💪 Market Health Score** — 0–100 gauge based on macro signals (Bullish / Constructive / Neutral / Cautious / Bearish)
- **📁 Portfolio Management** — Add holdings via form or CSV upload, track cost basis and allocation %
- **🎯 Investment Plan Generator** — Fill a form with your situation and get macro-aligned ETF recommendations
- **🔄 Real-time Updates** — Fetch live macro data via API button

## Features

### Macro Indicators Tab
- 9 economic signals with gauges
- Live data from yfinance (VIX, gold, treasury, P/E)
- Manual quarterly updates (Fed rate, inflation, GDP)

### Outlook Tab
- Market health score (0–100) with doughnut gauge
- Signal breakdown (tailwinds / neutral / headwinds)
- Macro table with all signals and context
- 5-regime guide (Bullish to Bearish strategies)

### Portfolio Tab ⭐ NEW
**Two ways to add holdings:**
1. **CSV Upload** — Format: `Ticker,Shares,CostBasis`
   ```
   AAPL,100,150.50
   MSFT,50,350.00
   BND,200,80.00
   ```
2. **Manual Form** — Add holdings one-by-one via form

**Portfolio summary shows:**
- Individual holding allocation %
- Total portfolio value
- Remove button for each holding

### Investment Plan Tab
**Answer 4 questions:**
1. Investment amount ($)
2. Timeline (short / medium / long)
3. Current portfolio size
4. Risk tolerance (conservative / moderate / aggressive)

**Get:**
- Recommended allocation (stocks / bonds / cash %)
- Specific ETF recommendations grouped by type
- Macro regime-aware strategy
- Legal disclaimer

## Project Structure

```
portfolio-dashboard/
├── .devcontainer/
│   └── devcontainer.json        # GitHub Codespaces config
├── backend/
│   ├── api.py                   # Flask API (3 routes)
│   ├── fetch_macro.py           # yfinance data fetching
│   ├── macro_config.json        # Macro signals storage
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx              # Root state management
│   │   ├── app.css              # Dark theme styling
│   │   ├── lib/
│   │   │   ├── macroUtils.js    # Health score logic
│   │   │   └── recommendation.js # Investment plan logic
│   │   └── components/          # 14 React components
│   │       ├── Header.jsx
│   │       ├── TabBar.jsx
│   │       ├── MacroTab.jsx
│   │       ├── OutlookTab.jsx
│   │       ├── PortfolioTab.jsx     # NEW
│   │       ├── InvestmentPlanTab.jsx
│   │       └── ... (10 more)
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml           # Frontend (5001) + Backend (5000)
├── README.md (this file)
└── start.sh / start.bat
```

## How It Works

### Backend (Flask API)
```
GET  /api/health   → {"status":"ok","timestamp":"..."}
GET  /api/macro    → Full macro_config.json with all signals
POST /api/refresh  → Trigger data fetch, return updated config
```

### Frontend (React 18 + Vite)
- Fetches macro data on mount
- Tabs: Macro → Outlook → Portfolio → Investment Plan
- Chart.js doughnut gauge for health score
- Form state management for portfolio and investment plan

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/macro` | Current macro data |
| POST | `/api/refresh` | Refresh macro data |

## Testing with Users

### Option 1: GitHub Codespaces (Share a link)
```
https://codespaces.new/vipinsindhu/portfolio-dashboard
```
Users click, run `docker-compose up --build`, test immediately.

### Option 2: ngrok Tunnel
```bash
ngrok http 5001
```
Share the public URL (e.g., `https://abc123.ngrok.io`).

### Option 3: Clone & Local
```bash
git clone https://github.com/vipinsindhu/portfolio-dashboard.git
cd portfolio-dashboard
docker-compose up --build
# Share localhost:5001 or use ngrok tunnel
```

## Configuration

### Change Macro Refresh Time
Edit `backend/api.py` to modify the schedule.

### Edit Macro Signals
Edit `backend/macro_config.json` directly (bind-mounted in container).

### Add More Indicators
Update `macro_config.json` structure and add React components.

## Macro Signals Reference

| Signal | Source | Type | Notes |
|--------|--------|------|-------|
| Fed Funds Rate | Manual | Quarterly | Affects borrowing costs, valuation |
| Core PCE | Manual | Quarterly | Inflation measure |
| 10-yr Treasury | yfinance | Daily | Risk-free rate, equity multiple pressure |
| S&P 500 P/E | yfinance | Daily | Valuation metric (vs 17x avg) |
| VIX | yfinance | Daily | Market volatility (below 20 = calm) |
| Gold Spot | yfinance | Daily | Inflation hedge, risk-off indicator |
| Dollar Index | yfinance | Daily | USD strength (watch 101, 105 inflection) |
| GDP Growth | Manual | Quarterly | Above 2% = earnings support |
| EM Trend | Manual | Quarterly | Cyclical recovery play |

## Health Score Calculation

```
score = ((signal_sum + indicator_count) / (2 * indicator_count)) * 100
```

Where each signal ∈ {-1, 0, +1}

**Regimes:**
- **Bullish** (70+) — Add equity, increase risk
- **Constructive** (55–69) — Balanced allocation
- **Neutral** (45–54) — Hedge with bonds/gold
- **Cautious** (30–44) — Reduce risk, raise cash
- **Bearish** (<30) — Deleveraging, prepare for corrections

## Development

### Run Frontend Dev Server
```bash
cd frontend
npm install
npm run dev
# Visit http://localhost:5173
```

### Backend API Testing
```bash
curl http://localhost:5001/api/macro
curl -X POST http://localhost:5001/api/refresh
```

## Troubleshooting

**Port 5001 already in use?**
```bash
docker-compose down  # Stop all containers
# Or change port in docker-compose.yml
```

**Containers won't start?**
```bash
docker-compose logs  # Check logs
docker-compose down && docker-compose up --build --force-recreate
```

**API returning errors?**
```bash
docker-compose logs portfolio-backend  # Check Flask logs
curl http://localhost:5001/api/health  # Verify connection
```

## Disclaimers

⚠️ **Not financial advice.** This is an educational tool for macro analysis and portfolio planning. Consult a licensed financial advisor before making investment decisions. Past performance does not guarantee future results. All investing carries risk, including potential loss of principal.

## License

MIT
