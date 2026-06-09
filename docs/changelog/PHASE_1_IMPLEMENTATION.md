# Phase 1 Implementation Guide: Foundation (App Service + SQL Database)

**Timeline:** 2 weeks  
**Effort:** 13 hours  
**Cost Impact:** $30/month (same or cheaper than current ACI setup)

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Setup Instructions](#setup-instructions)
4. [Local Development](#local-development)
5. [Data Migration](#data-migration)
6. [Deployment](#deployment)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Tools Required
```bash
# Azure CLI
az --version  # Should be 2.50+

# Git
git --version

# Python 3.11+
python --version

# Node.js 20+
node --version
npm --version

# Docker (for local testing)
docker --version
docker-compose --version
```

### Azure Resources Needed
- Active Azure subscription
- Sufficient quota for:
  - 2× App Service instances (Standard tier)
  - 1× SQL Database (Standard tier)
  - 1× Storage Account (for backups)

---

## Architecture Overview

### Current (Azure Container Instances)
```
┌─────────────────────────────────────────┐
│         Azure Container Registry        │
└──────────────────────┬──────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼─────────┐         ┌────────▼────────┐
│  ACI Backend    │         │  ACI Frontend   │
│  (1 CPU, 1GB)   │         │ (0.5 CPU, 0.5GB)│
└──────────┬──────┘         └────────┬────────┘
           │                         │
        ┌──┴─────────────────────────┘
        │
┌───────▼─────────────────────────────────┐
│       JSON Files (Lost on restart)      │
└─────────────────────────────────────────┘
```

### New (App Service + SQL Database)
```
┌─────────────────────────────────────────┐
│         Azure Container Registry        │
└──────────────────────┬──────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼──────────────┐    ┌────────▼──────────┐
│  App Service Backend │    │ App Service Frontend│
│  - Auto-scale 1-4   │    │ - Auto-scale 0-2   │
│  - Load balanced    │    │ - Global CDN       │
└────────┬─────────────┘    └───────┬───────────┘
         │                          │
         │ ┌────────────────────────┘
         │ │
         │ │ Environment Variables (Key Vault)
         │ │ - DATABASE_URL
         │ │ - ANTHROPIC_API_KEY
         │ │
         ▼ ▼
    ┌──────────────────┐
    │ Azure SQL Database│
    │ - Auto-backup    │
    │ - Failover       │
    │ - Point-in-time  │
    └──────────────────┘
```

---

## Setup Instructions

### Step 1: Create Azure Resources

#### 1.1 Create Resource Group
```bash
export RESOURCE_GROUP="portfolio-rg"
export LOCATION="eastus"

az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

#### 1.2 Create SQL Database Server
```bash
export SQL_SERVER_NAME="portfolio-sql-$(date +%s)"
export ADMIN_USER="sqladmin"
export ADMIN_PASSWORD="P@ssw0rd$(date +%s)"

# Create SQL server
az sql server create \
  --name $SQL_SERVER_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --admin-user $ADMIN_USER \
  --admin-password $ADMIN_PASSWORD

# Allow Azure services to access (required for App Service)
az sql server firewall-rule create \
  --name "AllowAzureServices" \
  --server $SQL_SERVER_NAME \
  --resource-group $RESOURCE_GROUP \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

#### 1.3 Create SQL Database
```bash
export DATABASE_NAME="portfolio_db"

az sql db create \
  --name $DATABASE_NAME \
  --server $SQL_SERVER_NAME \
  --resource-group $RESOURCE_GROUP \
  --service-objective S0 \
  --backup-storage-redundancy Local

# Get connection string
az sql db show-connection-string \
  --name $DATABASE_NAME \
  --server $SQL_SERVER_NAME \
  --client sqlcmd

# Example output:
# sqlcmd -S tcp:portfolio-sql-1717754400.database.windows.net,1433 -d portfolio_db -U sqladmin -P <password>

# For Python, construct connection string:
# DATABASE_URL="mssql+pyodbc://sqladmin:<password>@portfolio-sql-1717754400.database.windows.net/portfolio_db?driver=ODBC+Driver+17+for+SQL+Server"
```

#### 1.4 Create App Service Plan
```bash
export APP_PLAN_NAME="portfolio-plan"

az appservice plan create \
  --name $APP_PLAN_NAME \
  --resource-group $RESOURCE_GROUP \
  --sku B1 \
  --is-linux
```

#### 1.5 Create Container Registry
```bash
export REGISTRY_NAME="portfolioregistry$(date +%s | tail -c 5)"

az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $REGISTRY_NAME \
  --sku Standard

# Get credentials
az acr credential show \
  --name $REGISTRY_NAME \
  --resource-group $RESOURCE_GROUP

# Output: username and password for push/pull
```

### Step 2: Update Configuration Files

#### 2.1 Create `.env.production` (DO NOT COMMIT)
```bash
# Backend environment
export DATABASE_URL="mssql+pyodbc://sqladmin:YourPassword@server.database.windows.net/portfolio_db?driver=ODBC+Driver+17+for+SQL+Server"
export ANTHROPIC_API_KEY="sk-ant-..."
export FLASK_ENV="production"
export MAX_WORKERS="4"
export REQUEST_TIMEOUT="120"

# Frontend environment
export BACKEND_URL="https://portfolio-backend.azurewebsites.net"
export VITE_API_URL="https://portfolio-backend.azurewebsites.net"
```

#### 2.2 Update docker-compose.yml (for local testing)
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    environment:
      DATABASE_URL: "sqlite:///portfolio.db"  # Local SQLite for dev
      FLASK_ENV: development
      DEBUG: "true"
    ports:
      - "5000:5000"
    volumes:
      - ./backend:/app

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_URL: "http://localhost:5000"
    environment:
      BACKEND_URL: "http://backend:5000"
    ports:
      - "5173:80"
    depends_on:
      - backend
```

### Step 3: Build and Push Images

#### 3.1 Build Backend Image
```bash
cd backend

# Build with proper tagging
docker build \
  -t $REGISTRY_NAME.azurecr.io/portfolio-backend:latest \
  -t $REGISTRY_NAME.azurecr.io/portfolio-backend:v1.0 \
  .

cd ..
```

#### 3.2 Build Frontend Image
```bash
cd frontend

# Build with API URL argument
docker build \
  --build-arg VITE_API_URL="https://portfolio-backend.azurewebsites.net" \
  -t $REGISTRY_NAME.azurecr.io/portfolio-frontend:latest \
  -t $REGISTRY_NAME.azurecr.io/portfolio-frontend:v1.0 \
  .

cd ..
```

#### 3.3 Login to Registry and Push
```bash
# Login to ACR
az acr login --name $REGISTRY_NAME

# Push images
docker push $REGISTRY_NAME.azurecr.io/portfolio-backend:latest
docker push $REGISTRY_NAME.azurecr.io/portfolio-frontend:latest
```

### Step 4: Deploy to App Service

#### 4.1 Create Backend App Service
```bash
az webapp create \
  --name portfolio-backend \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_PLAN_NAME \
  --deployment-container-image-name $REGISTRY_NAME.azurecr.io/portfolio-backend:latest

# Configure Docker settings
az webapp config container set \
  --name portfolio-backend \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name $REGISTRY_NAME.azurecr.io/portfolio-backend:latest \
  --docker-registry-server-url https://$REGISTRY_NAME.azurecr.io \
  --docker-registry-server-user $(az acr credential show --name $REGISTRY_NAME --query username -o tsv) \
  --docker-registry-server-password $(az acr credential show --name $REGISTRY_NAME --query 'passwords[0].value' -o tsv)

# Set environment variables
az webapp config appsettings set \
  --name portfolio-backend \
  --resource-group $RESOURCE_GROUP \
  --settings \
    DATABASE_URL="mssql+pyodbc://sqladmin:YourPassword@server.database.windows.net/portfolio_db?driver=ODBC+Driver+17+for+SQL+Server" \
    ANTHROPIC_API_KEY="sk-ant-..." \
    FLASK_ENV="production" \
    MAX_WORKERS="4" \
    REQUEST_TIMEOUT="120"

# Enable continuous deployment
az webapp deployment container config \
  --name portfolio-backend \
  --resource-group $RESOURCE_GROUP \
  --enable-cd
```

#### 4.2 Create Frontend App Service
```bash
az webapp create \
  --name portfolio-frontend \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_PLAN_NAME \
  --deployment-container-image-name $REGISTRY_NAME.azurecr.io/portfolio-frontend:latest

# Configure Docker settings
az webapp config container set \
  --name portfolio-frontend \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name $REGISTRY_NAME.azurecr.io/portfolio-frontend:latest \
  --docker-registry-server-url https://$REGISTRY_NAME.azurecr.io \
  --docker-registry-server-user $(az acr credential show --name $REGISTRY_NAME --query username -o tsv) \
  --docker-registry-server-password $(az acr credential show --name $REGISTRY_NAME --query 'passwords[0].value' -o tsv)

# Set environment variables
az webapp config appsettings set \
  --name portfolio-frontend \
  --resource-group $RESOURCE_GROUP \
  --settings \
    BACKEND_URL="https://portfolio-backend.azurewebsites.net" \
    WEBSITES_ENABLE_APP_SERVICE_STORAGE="true"
```

### Step 5: Migrate Data

#### 5.1 Run Migration Script Locally
```bash
cd backend

# First, migrate data from JSON to database
python migrate_to_database.py \
  --database-url "mssql+pyodbc://sqladmin:YourPassword@server.database.windows.net/portfolio_db?driver=ODBC+Driver+17+for+SQL+Server"

# Or with environment variable
export DATABASE_URL="mssql+pyodbc://sqladmin:YourPassword@server.database.windows.net/portfolio_db?driver=ODBC+Driver+17+for+SQL+Server"
python migrate_to_database.py

cd ..
```

---

## Local Development

### Setup Local Environment

#### Option A: Using Docker Compose (Recommended)
```bash
# Start all services (backend + frontend + SQLite)
docker-compose up -d

# Verify
curl http://localhost:5000/api/health
# Output: {"status": "ok", "timestamp": "...", "storage": "database"}

# Open frontend
open http://localhost:5173
```

#### Option B: Local Python + Node
```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
export FLASK_ENV=development
export DATABASE_URL="sqlite:///portfolio.db"
python api.py
# Server runs on http://localhost:5000

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
# Server runs on http://localhost:5173
```

### Testing Database Connection
```bash
python -c "
from backend.models import init_db, get_session
from config import get_config

config = get_config()
engine = init_db(config.DATABASE_URL)
session = get_session(engine)
print('✓ Database connected successfully')
"
```

---

## Data Migration

### Full Migration Workflow

#### Step 1: Backup Current Data
```bash
cp signals.json signals.json.backup
cp macro_config.json macro_config.json.backup
```

#### Step 2: Test Migration Locally
```bash
cd backend
export DATABASE_URL="sqlite:///test.db"
python migrate_to_database.py --dry-run

# If successful:
python migrate_to_database.py
```

#### Step 3: Verify Migration
```bash
cd backend
python -c "
from models import init_db, get_session, Signal
config = get_config()
engine = init_db(config.DATABASE_URL)
session = get_session(engine)

signals = session.query(Signal).all()
print(f'Migrated {len(signals)} signals')
for signal in signals[:3]:
    print(f'  - {signal.ticker}: {signal.direction} ({signal.confidence}/10)')
"
```

#### Step 4: Deploy to Production
Once verified locally, the migration runs automatically when the backend app starts (creates tables if they don't exist).

---

## Deployment

### Automated Deployment (CI/CD)

Update `.github/workflows/deploy-to-azure.yml`:

```yaml
name: Deploy to Azure App Service

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  REGISTRY_NAME: portfolioregistry
  RESOURCE_GROUP: portfolio-rg

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Backend
        run: |
          docker build \
            -t ${{ env.REGISTRY_NAME }}.azurecr.io/portfolio-backend:${{ github.sha }} \
            -t ${{ env.REGISTRY_NAME }}.azurecr.io/portfolio-backend:latest \
            ./backend
      
      - name: Build Frontend
        run: |
          docker build \
            --build-arg VITE_API_URL="https://portfolio-backend.azurewebsites.net" \
            -t ${{ env.REGISTRY_NAME }}.azurecr.io/portfolio-frontend:${{ github.sha }} \
            -t ${{ env.REGISTRY_NAME }}.azurecr.io/portfolio-frontend:latest \
            ./frontend
      
      - name: Login to ACR
        uses: azure/docker-login@v1
        with:
          login-server: ${{ env.REGISTRY_NAME }}.azurecr.io
          username: ${{ secrets.AZURE_REGISTRY_USERNAME }}
          password: ${{ secrets.AZURE_REGISTRY_PASSWORD }}
      
      - name: Push Images
        run: |
          docker push ${{ env.REGISTRY_NAME }}.azurecr.io/portfolio-backend:latest
          docker push ${{ env.REGISTRY_NAME }}.azurecr.io/portfolio-frontend:latest
      
      - name: Deploy Backend
        uses: azure/webapps-deploy@v2
        with:
          app-name: 'portfolio-backend'
          images: ${{ env.REGISTRY_NAME }}.azurecr.io/portfolio-backend:latest
      
      - name: Deploy Frontend
        uses: azure/webapps-deploy@v2
        with:
          app-name: 'portfolio-frontend'
          images: ${{ env.REGISTRY_NAME }}.azurecr.io/portfolio-frontend:latest
```

---

## Verification

### Health Checks

```bash
# Backend health
curl https://portfolio-backend.azurewebsites.net/api/health

# Frontend health
curl https://portfolio-frontend.azurewebsites.net/health

# Get signals
curl https://portfolio-backend.azurewebsites.net/api/signals

# Get stock data
curl https://portfolio-backend.azurewebsites.net/api/stock/AAPL
```

### Monitor Logs

```bash
# View backend logs
az webapp log tail --name portfolio-backend --resource-group portfolio-rg

# View frontend logs
az webapp log tail --name portfolio-frontend --resource-group portfolio-rg

# View database activity (Azure Portal)
# Portal → SQL Database → Query editor → Run queries
```

---

## Troubleshooting

### Issue: Database Connection Fails

**Symptoms:** `Error: Failed to connect to database`

**Solutions:**
```bash
# 1. Verify connection string
echo $DATABASE_URL

# 2. Check firewall rules
az sql server firewall-rule list \
  --server $SQL_SERVER_NAME \
  --resource-group $RESOURCE_GROUP

# 3. Test connection locally
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); engine.execute('SELECT 1')"

# 4. Verify credentials
az sql server show \
  --name $SQL_SERVER_NAME \
  --resource-group $RESOURCE_GROUP
```

### Issue: Frontend Can't Reach Backend

**Symptoms:** `CORS error, Failed to fetch`

**Solutions:**
```bash
# 1. Check backend URL in frontend logs
az webapp log tail --name portfolio-frontend --resource-group portfolio-rg

# 2. Verify CORS configuration
curl -H "Origin: https://portfolio-frontend.azurewebsites.net" \
  https://portfolio-backend.azurewebsites.net/api/signals -v

# 3. Check nginx configuration
# Frontend logs will show what BACKEND_URL is being used
```

### Issue: Migration Failed

**Symptoms:** `Error migrating signal`

**Solutions:**
```bash
# 1. Check database has tables
python -c "from models import Base, Signal; print(Signal.__table__.columns.keys())"

# 2. Run migration with dry-run first
python migrate_to_database.py --dry-run

# 3. Check JSON file format
python -c "import json; json.load(open('signals.json'))"

# 4. Manual check
python -c "
from models import init_db, get_session, Signal
from config import get_config
engine = init_db('your-database-url')
session = get_session(engine)
signals = session.query(Signal).count()
print(f'Signals in database: {signals}')
"
```

---

## Next Steps

After Phase 1 is complete:
- ✅ Data is persistent (survives container restarts)
- ✅ Can scale horizontally (multiple instances)
- ✅ Automatic backups enabled
- ✅ Environment-specific configuration

**Ready for Phase 2:** Add Azure AD authentication and user isolation (4 weeks)

---

## Cost Summary

| Resource | Tier | Monthly Cost |
|----------|------|--------------|
| App Service (Backend) | B1 | $15 |
| App Service (Frontend) | B1 | $15 |
| SQL Database | S0 | $15 |
| **Total** | | **$45** |

**Compared to current ACI:** $35/month → $45/month (+$10 for database durability and features)

Future savings when traffic grows and you move to S1 with auto-scaling (~$100/month for 10x capacity).

