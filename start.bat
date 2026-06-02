@echo off
REM Portfolio Builder - Docker Startup Script (Windows)

echo.
echo 🚀 Starting Portfolio Builder...
echo ================================
echo.

REM Check if docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop.
    echo    https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed.
    echo    It usually comes with Docker Desktop. Try updating Docker.
    pause
    exit /b 1
)

echo 📦 Building Docker image...
docker-compose build

echo.
echo ✅ Build complete!
echo.
echo Starting container...
docker-compose up

echo.
echo 🎉 Portfolio Builder is running!
echo 📊 Open your browser: http://localhost:5000
pause
