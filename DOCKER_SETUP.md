# Portfolio Builder — Docker Setup

Run Portfolio Builder in Docker for automated daily updates and web dashboard serving.

## Quick Start

### Prerequisites
- Docker Desktop (Mac/Windows) or Docker Engine (Linux)
- Docker Compose (usually included with Docker Desktop)

### 1. Build & Run

```bash
cd portfolio-dashboard
docker-compose up --build
```

The first build will take 2-3 minutes. Once running, you'll see:

```
📊 Dashboard available at: http://localhost:5001
```

Open your browser to **http://localhost:5001** to view the dashboard.

### 2. What Happens Automatically

✅ **On startup:** Fetches live macro data and regenerates dashboard
✅ **Daily at 4:30pm UTC** (8:30am PT): Auto-refresh macro data + dashboard
✅ **24/7 availability:** Web server running, accessible anytime

## File Structure

```
portfolio-dashboard/
├── Dockerfile              # Container image definition
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
├── scheduler.py            # Scheduler + Flask web server
├── fetch_macro.py          # Fetch live macro data from APIs
├── generate_dashboard.py   # Generate HTML dashboard
├── macro_config.json       # Macro signals config
└── docs/
    └── index.html          # Generated dashboard
```

## Docker Commands

### Start Container
```bash
docker-compose up
```

### Stop Container
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f
```

### Rebuild Image (after code changes)
```bash
docker-compose up --build
```

### Run Manually Without Docker Compose
```bash
# Build image
docker build -t portfolio-builder .

# Run container
docker run -p 5000:5000 -v $(pwd)/docs:/app/docs portfolio-builder
```

## Customization

### Change Schedule Time

Edit `scheduler.py` line 35:
```python
schedule.every().day.at("16:30").do(run_updates)  # Change "16:30" to desired UTC time
```

Time format: 24-hour UTC (HH:MM)
- 8:30am PT = 16:30 UTC
- 9:00am PT = 17:00 UTC

### Update Macro Signals Manually

1. Edit `macro_config.json` directly
2. Container picks up changes immediately
3. Or restart to force regeneration:
   ```bash
   docker-compose restart
   ```

### Access Dashboard from Network

If running on a remote machine:
- Local: `http://localhost:5001`
- Network: `http://<your-ip>:5001`

Change port in `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Access via http://localhost:8080
```

## Troubleshooting

### Container won't start
```bash
docker-compose logs
```
Check for Python dependency issues or port conflicts.

### Port 5000 already in use
Change port in `docker-compose.yml`:
```yaml
ports:
  - "5001:5000"  # Use port 5001 instead
```

### Macro data not updating
Check logs:
```bash
docker-compose logs -f | grep "Running fetch"
```

Verify internet connection inside container:
```bash
docker-compose exec portfolio-builder curl https://www.google.com
```

### Persistent data / config
The `docker-compose.yml` volume mounts ensure:
- `docs/` folder syncs (dashboard updates visible on host)
- `macro_config.json` stays in sync (edit on host, changes reflect in container)

## Environment Details

**Base Image:** `python:3.11-slim` (lightweight, ~160MB)
**Dependencies:** yfinance, pandas, flask, schedule
**Memory:** ~200MB typical usage
**CPU:** Minimal (only active during scheduled updates)

## Health Check

Container includes a health check endpoint:
```bash
curl http://localhost:5000/health
# Response: {"status": "ok", "timestamp": "2026-05-31T..."}
```

## Next Steps

1. **Start container:** `docker-compose up`
2. **Open dashboard:** http://localhost:5000
3. **Fill out Investment Plan form** with your details
4. **Get macro-aligned recommendations** updated daily

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Verify files exist: `ls -la`
- Test local Python: `python fetch_macro.py`
