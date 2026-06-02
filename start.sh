#!/bin/bash

# Portfolio Builder — Docker Startup Script
# Simple one-command start

set -e

echo "🚀 Starting Portfolio Builder..."
echo "================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop."
    echo "   https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    echo "   It usually comes with Docker Desktop. Try updating Docker."
    exit 1
fi

# Build and start
echo "📦 Building Docker image..."
docker-compose build

echo ""
echo "✅ Build complete!"
echo ""
echo "Starting container..."
docker-compose up

echo ""
echo "🎉 Portfolio Builder is running!"
echo "📊 Open your browser: http://localhost:5000"
