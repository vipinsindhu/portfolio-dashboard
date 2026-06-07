FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY api.py signals.py ./

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Wait for Ollama and pull Mistral model, then start API
CMD bash -c '\
    echo "Waiting for Ollama to be ready..." && \
    until curl -s http://portfolio-ollama:11434/api/tags > /dev/null 2>&1; do \
      sleep 2; \
    done && \
    echo "Ollama is ready, pulling Mistral model..." && \
    curl -X POST http://portfolio-ollama:11434/api/pull -d "{\"name\": \"mistral\"}" && \
    echo "Model ready, starting API server..." && \
    exec gunicorn \
      --bind 0.0.0.0:5000 \
      --workers ${MAX_WORKERS:-4} \
      --timeout ${REQUEST_TIMEOUT:-180} \
      --access-logfile - \
      --error-logfile - \
      api:app'
