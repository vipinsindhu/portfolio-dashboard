FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (includes APScheduler for macro data refresh)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY api.py signals.py ./

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Start API with Gunicorn
# APScheduler will start on first request and refresh macro data every hour
CMD exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers ${MAX_WORKERS:-4} \
    --timeout ${REQUEST_TIMEOUT:-180} \
    --access-logfile - \
    --error-logfile - \
    api:app
