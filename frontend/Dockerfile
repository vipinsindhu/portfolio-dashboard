FROM node:20-slim AS builder

WORKDIR /build

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy application
COPY . .

# Build with environment-specific API URL if provided
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Force fresh build by busting cache
ARG BUILD_TIMESTAMP
RUN npm run build

FROM nginx:alpine

# Install envsubst for environment variable substitution
RUN apk add --no-cache gettext

# Copy built application
COPY --from=builder /build/dist /usr/share/nginx/html

# Copy nginx configuration (with variables)
COPY nginx.conf /etc/nginx/conf.d/default.conf.template

# Create entrypoint script for environment variable substitution
RUN printf '#!/bin/sh\nBACKEND_URL="${BACKEND_URL:-http://portfolio-backend:5000}"\nsed "s|BACKEND_URL_PLACEHOLDER|${BACKEND_URL}|g" /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf\nexec nginx -g "daemon off;"\n' > /docker-entrypoint.sh && chmod +x /docker-entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
