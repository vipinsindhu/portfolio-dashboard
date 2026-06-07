FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for ODBC (needed for Azure SQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    odbc-postgresql \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY api.py .
COPY config.py .
COPY models.py .
COPY signals.py .
COPY signals_db.py .
COPY fetch_macro.py .
COPY macro_config.json .

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health')" || exit 1

# Run with gunicorn using environment variables for worker count and timeout
CMD exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers ${MAX_WORKERS:-4} \
    --timeout ${REQUEST_TIMEOUT:-120} \
    --access-logfile - \
    --error-logfile - \
    api:create_app
