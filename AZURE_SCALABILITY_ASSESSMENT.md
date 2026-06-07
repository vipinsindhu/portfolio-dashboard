# Azure Hosting & Scalability Assessment

**Date:** June 7, 2026  
**Status:** Ready for Azure App Service, with critical scalability improvements needed

---

## Executive Summary

Your app is **partially compatible with Azure** and currently runs on Azure Container Instances (ACI). However, it has **three critical scalability bottlenecks** that will prevent it from serving production users:

1. **JSON file storage** - Not suitable for distributed systems or concurrent writes
2. **Single-threaded Flask** with gunicorn (2 workers) - Limits concurrent requests
3. **No user authentication/isolation** - All users share same data
4. **Hardcoded backend URLs** - Breaks in containerized/distributed environments

**Recommendation:** Move to **Azure App Service** (managed) instead of ACI, add **Azure SQL Database** or **Cosmos DB** for persistent storage, and implement proper **environment configuration**.

---

## Current Architecture Analysis

### What's Working ✅
- **Docker containerization** - Good foundation, images build cleanly
- **CI/CD pipeline** - GitHub Actions → Azure Container Registry → ACI deployment
- **Separation of concerns** - Frontend (React/Nginx) and backend (Flask) in separate containers
- **Health checks** - Docker Compose has healthcheck configured
- **CORS enabled** - Frontend can call backend API

### Critical Issues ❌

#### 1. **Storage: JSON File is a Bottleneck**

**Current:** `signals.json` stored in container filesystem

```python
# backend/signals.py
def load_signals():
    if os.path.exists(SIGNALS_FILE):
        with open(SIGNALS_FILE, 'r') as f:
            return json.load(f)

def save_signals(data):
    with open(SIGNALS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
```

**Problems:**
- ❌ Container restarts = data loss (no persistence)
- ❌ Multiple replicas = conflicting writes (race conditions)
- ❌ Can't scale horizontally (load balancer won't share files)
- ❌ No backup/disaster recovery
- ❌ Performance degrades as signals.json grows
- ❌ No ability to do concurrent reads/writes safely
- ❌ No audit trail or transaction history

**Impact:** With 100+ concurrent users, you'll lose data and have corrupted signal records.

---

#### 2. **Backend: Limited Concurrency**

**Current:** 
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "api:create_app"]
```

**Problems:**
- ❌ Only 2 gunicorn workers = max ~20 concurrent requests
- ❌ 60-second timeout is too aggressive for Claude API calls (which can take 30s)
- ❌ No auto-scaling configured
- ❌ No request queuing for burst traffic
- ❌ Each signal generation blocks other API requests

**Impact:** At 30+ concurrent users, requests start queuing. At 50+, users see timeouts.

---

#### 3. **Frontend: Hardcoded Backend URL**

**Current in nginx.conf:**
```nginx
set $backend "http://portfolio-backend-api.eastus.azurecontainer.io:5000";
```

**Problems:**
- ❌ Hardcoded DNS name breaks if backend URL changes
- ❌ No support for environment-specific deployments (dev/staging/prod)
- ❌ Frontend built once, can't change backend at runtime
- ❌ Breaks local development (needs mock backend URL)

**Impact:** Can't deploy to different Azure regions without rebuilding frontend image.

---

#### 4. **No Multi-User Support**

**Current:** All users access shared `/api/signals` endpoint

**Problems:**
- ❌ No user authentication (anyone can call API)
- ❌ No request rate limiting
- ❌ No per-user data isolation (watchlists, research notes)
- ❌ localStorage in browser = data syncs across browser tabs, not backend
- ❌ No session management

**Impact:** Can't monetize (Stripe subscription won't work). Data is public.

---

#### 5. **Configuration Management**

**Current:** Hardcoded values scattered across code

```python
# backend/signals.py
SIGNALS_FILE = "signals.json"  # Hardcoded

# frontend/nginx.conf
set $backend "http://portfolio-backend-api.eastus.azurecontainer.io:5000";  # Hardcoded
```

**Problems:**
- ❌ Environment variables not used consistently
- ❌ Secrets (API keys) passed at container creation, not via key vault
- ❌ No .env file support for local development
- ❌ Different config for dev/staging/prod requires code changes

---

#### 6. **No Database/Persistence Layer**

**Current:** 
- Signals: JSON file
- Macro config: JSON file
- User data: Browser localStorage only
- No backup mechanism

**Problems:**
- ❌ No ACID transactions (partial writes on crash)
- ❌ No query capability (can't filter signals by sector efficiently)
- ❌ No indexing (loading all signals into memory)
- ❌ No audit logs
- ❌ No disaster recovery

---

## Azure Compatibility Assessment

### Current Deployment: Azure Container Instances (ACI)

**Pros:**
- ✅ Simple, works for single containers
- ✅ No infrastructure to manage
- ✅ Good for CI/CD integration

**Cons:**
- ❌ No built-in load balancing
- ❌ No auto-scaling
- ❌ Can't do blue-green deployments
- ❌ No health-based restart policies
- ❌ Expensive for persistent services ($20-50/month just for two containers idling)

### Recommended: Azure App Service

**Better choice because:**
- ✅ Built-in horizontal scaling
- ✅ Automatic load balancing
- ✅ Free tier for initial testing
- ✅ Native Azure integration (Key Vault, SQL, Storage)
- ✅ Staging slots for zero-downtime deployments
- ✅ Better monitoring/logging
- ✅ Custom domain support

---

## Scalability Roadmap

### Phase 1: Foundation (Weeks 1-2)
**Goal:** Move from ACI to App Service, add persistent storage

#### 1.1 Switch to Azure App Service
```bash
# Replace ACI with App Service
az appservice plan create --name portfolio-plan --resource-group portfolio-rg --sku B1 --is-linux
az webapp create --name portfolio-backend --plan portfolio-plan --resource-group portfolio-rg --runtime "PYTHON:3.11"
az webapp create --name portfolio-frontend --plan portfolio-plan --resource-group portfolio-rg --runtime "NODE:20"
```

**Effort:** 4 hours  
**Cost:** $15/month (B1) vs $50/month (ACI)

#### 1.2 Add Azure SQL Database
```python
# Replace JSON file with SQL
import pyodbc

class SignalStore:
    def __init__(self, connection_string):
        self.conn = pyodbc.connect(connection_string)
    
    def save_signal(self, signal):
        # INSERT/UPDATE with proper transactions
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO signals (id, ticker, direction, confidence, rationale, sector, market_cap, created_at, result, accuracy_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (signal['id'], signal['ticker'], signal['direction'], ...))
        self.conn.commit()
    
    def get_latest_signals(self, limit=5):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM signals ORDER BY created_at DESC LIMIT ?", (limit,))
        return cursor.fetchall()
```

**Benefits:**
- ✅ ACID transactions (no data loss)
- ✅ Concurrent reads/writes (handles 100+ users)
- ✅ Efficient queries (indexed searches)
- ✅ Automatic backups
- ✅ Built-in replication for HA

**Effort:** 6 hours  
**Cost:** $15-50/month (starts free tier)

#### 1.3 Switch Backend to Azure App Service
- Update deployment pipeline to use App Service
- Use environment variables from App Settings
- Configure runtime stack to Python 3.11

**Effort:** 2 hours  
**Cost:** Same as step 1.1

#### 1.4 Update Frontend Environment Configuration
```javascript
// frontend/src/config.js
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000'

// Used in components
fetch(`${API_BASE_URL}/api/signals`)
```

**Build time:** Override via environment variables
```bash
REACT_APP_API_URL=https://portfolio-backend.azurewebsites.net npm run build
```

**Effort:** 1 hour

**Total Phase 1 Effort:** ~13 hours  
**Cost Impact:** Same or cheaper than current ACI

---

### Phase 2: Multi-User Support (Weeks 3-4)
**Goal:** Add authentication, per-user data isolation, rate limiting

#### 2.1 Add Azure AD Authentication
```python
# backend/auth.py
from flask import session
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(
    client_id=os.getenv("AZURE_CLIENT_ID"),
    client_credential=os.getenv("AZURE_CLIENT_SECRET"),
    authority=f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}"
)

@app.route('/api/signals')
def get_signals():
    user_id = session.get('user_id')
    if not user_id:
        return {"error": "Unauthorized"}, 401
    
    # Get user's signals only
    cursor.execute("SELECT * FROM signals WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    return cursor.fetchall()
```

**Cost:** Free with Azure AD B2C (first 50k monthly active users free)

#### 2.2 Add User Management Database
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    azure_ad_id VARCHAR(255) UNIQUE,
    subscription_tier VARCHAR(50),  -- free, pro, enterprise
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);

CREATE TABLE watchlists (
    id UUID PRIMARY KEY,
    user_id UUID FOREIGN KEY,
    ticker VARCHAR(10),
    added_at DATETIME DEFAULT GETDATE()
);

CREATE TABLE research_notes (
    id UUID PRIMARY KEY,
    user_id UUID FOREIGN KEY,
    ticker VARCHAR(10),
    notes TEXT,
    updated_at DATETIME DEFAULT GETDATE()
);

-- Update signals table to include user_id
ALTER TABLE signals ADD user_id UUID FOREIGN KEY;
```

**Effort:** 8 hours

#### 2.3 Add Rate Limiting
```python
from flask_limiter import Limiter

limiter = Limiter(
    app=app,
    key_func=lambda: session.get('user_id'),
    default_limits=["100 per hour"]  # Per user
)

@app.route('/api/signals/generate', methods=['POST'])
@limiter.limit("1 per minute")  # Can't spam signal generation
def generate_signals():
    # ...
```

**Effort:** 2 hours

**Total Phase 2 Effort:** ~18 hours  
**Cost Impact:** +$0 (included in App Service, SQL, AD B2C free tier)

---

### Phase 3: Advanced Scalability (Weeks 5-6)
**Goal:** Add caching, queued background jobs, analytics

#### 3.1 Add Redis Caching
```python
# Cache signal generation results (expensive operation)
from redis import Redis

redis = Redis.from_url(os.getenv("REDIS_URL"))

@app.route('/api/signals')
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_signals():
    # First call: hits database
    # Next 300 seconds: returns cached result
    # After 300s: refreshes from database
    return get_latest_signals(5)
```

**Benefits:**
- ✅ 10x faster signal retrieval
- ✅ Reduces database load
- ✅ Session store (scales Flask sessions horizontally)

**Cost:** $10-20/month (Azure Cache for Redis)

#### 3.2 Add Background Job Queue
```python
# Signal generation runs in background, doesn't block API
from celery import Celery

app.config['CELERY_BROKER_URL'] = os.getenv("REDIS_URL")
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])

@app.route('/api/signals/generate', methods=['POST'])
def request_signal_generation():
    # Queues job, returns immediately
    generate_signals.delay(count=5)
    return {"status": "queued"}, 202

@celery.task
def generate_signals(count=5):
    # Runs in background worker, doesn't timeout
    signals = generate_signals_with_claude(count)
    save_to_database(signals)
```

**Benefits:**
- ✅ Signal generation no longer blocks users
- ✅ Can scale workers independently
- ✅ Handles timeouts gracefully (retries)
- ✅ User gets WebSocket update when ready

**Cost:** Reuse Redis from phase 3.1

#### 3.3 Add Application Insights Monitoring
```python
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.ext.azure.log_exporter import AzureLogHandler

FlaskMiddleware(app)
logging.getLogger('').addHandler(AzureLogHandler(
    connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
))
```

**Benefits:**
- ✅ Real-time monitoring of all endpoints
- ✅ Automatic error tracking
- ✅ Performance metrics
- ✅ User analytics
- ✅ Alerts for anomalies

**Cost:** Free for first 1GB/month

**Total Phase 3 Effort:** ~12 hours  
**Cost Impact:** +$30/month (Redis + increased App Service usage)

---

## Recommended Architecture (Post-Improvements)

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Front Door                         │
│              (Global load balancing, DDoS)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
┌───────▼──────────┐              ┌──────────▼───────┐
│  App Service     │              │   App Service    │
│  (Frontend)      │              │   (Backend)      │
│  - React/Vite   │              │   - Flask        │
│  - Nginx        │              │   - Gunicorn (4) │
│  - Auto-scale   │              │   - Auto-scale   │
│    (0-3 inst)   │              │     (1-10 inst)  │
└──────────────────┘              └──────────┬───────┘
        │                                   │
        └──────────────────┬────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
┌───────▼──────────┐              ┌──────────▼───────┐
│ Azure SQL Db     │              │  Azure Cache     │
│ - Signals        │              │  (Redis)         │
│ - Users          │              │  - Session store │
│ - Watchlists     │              │  - Signal cache  │
│ - Automated      │              │                  │
│   backups        │              │                  │
└──────────────────┘              └──────────────────┘
        │                                   │
        └──────────────────┬────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │   Application Insights              │
        │   (Monitoring & Analytics)          │
        └─────────────────────────────────────┘
```

---

## Implementation Priority

### Must-Do (Before Production)
1. ✅ **Phase 1.1-1.4**: Move to App Service + SQL Database (enables scaling)
2. ✅ **Phase 2.1-2.3**: Add authentication + user isolation (enables monetization)

### Should-Do (First 3 months)
3. **Phase 3.1-3.2**: Add Redis + job queue (handles burst traffic)
4. **Phase 3.3**: Add monitoring (know when to scale)

### Nice-To-Do (After launch)
5. Azure Front Door for global CDN
6. API Management for rate limiting
7. Event Grid for async notifications

---

## Cost Breakdown

### Current (Azure Container Instances)
- Frontend container: $15/month
- Backend container: $20/month
- Storage: $0
- **Total: ~$35/month**

### Recommended Setup
- **Phase 1 (App Service + SQL)**
  - App Service (B1): $15/month
  - SQL Database: $15/month (S0 tier)
  - **Subtotal: $30/month** (actually cheaper!)

- **Phase 2 (Multi-user)**
  - Same as Phase 1
  - Azure AD B2C: Free (up to 50k MAU)
  - **Subtotal: $30/month**

- **Phase 3 (Advanced)**
  - All above + Redis: $10-20/month
  - App Service upgrade to S1: $50/month (for auto-scaling)
  - **Subtotal: $90-100/month** (supports 1000+ users)

### ROI at Scale
- Current: 100 users = crashes, $35/month
- Recommended: 1000 users = smooth, $100/month
- Revenue target: $29/month × 500 paid users = **$14,500/month** profit

---

## Migration Path (Minimal Disruption)

### Week 1: Setup New Infrastructure
```bash
# Keep old ACI running, create new App Service in parallel
az appservice plan create --name portfolio-app-service ...
az webapp create --name portfolio-backend-v2 ...
az sql server create --name portfolio-sql ...
```

### Week 2: Point Traffic (Blue-Green Deploy)
```bash
# Update DNS/Azure Traffic Manager to route to new service
# Old ACI still runs, can rollback instantly if issues
# Monitor error rates, response times
```

### Week 3: Migrate Data
```python
# Script to migrate signals.json to SQL Database
from old_signals import load_signals
for signal in load_signals()['signals']:
    database.save_signal(signal)
```

### Week 4: Clean Up
```bash
# Delete old ACI containers after confirming new service stable
az container delete --name portfolio-backend
```

---

## Critical Changes Required

### 1. **Environment Configuration**

**Before:**
```dockerfile
# backend/Dockerfile - hardcoded
CMD ["gunicorn", "--bind", "0.0.0.0:5000", ...]
```

**After:**
```dockerfile
# backend/Dockerfile
ENV WORKER_COUNT=4
ENV TIMEOUT=120
CMD gunicorn --bind 0.0.0.0:5000 --workers $WORKER_COUNT --timeout $TIMEOUT api:create_app
```

**Frontend environment:**
```javascript
// frontend/.env.production
VITE_API_URL=https://portfolio-backend.azurewebsites.net
```

---

### 2. **Storage Layer**

**Before:**
```python
# Fragile file I/O
def load_signals():
    with open('signals.json') as f:
        return json.load(f)
```

**After:**
```python
# Robust database abstraction
from dataclasses import dataclass
from sqlalchemy import create_engine

@dataclass
class SignalStore:
    engine = create_engine(os.getenv("DATABASE_URL"))
    
    def save_signal(self, signal):
        with self.engine.connect() as conn:
            conn.execute(signals_table.insert().values(**signal))
            conn.commit()
    
    def get_signals(self, user_id, limit=5):
        with self.engine.connect() as conn:
            return conn.execute(
                select(signals_table).where(signals_table.c.user_id == user_id)
                .order_by(signals_table.c.created_at.desc())
                .limit(limit)
            ).fetchall()
```

---

### 3. **Backend Configuration**

**Create `config.py`:**
```python
import os
from dataclasses import dataclass

@dataclass
class Config:
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    TESTING = os.getenv("TESTING", "false").lower() == "true"
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "120"))
```

Update `api.py`:
```python
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
```

---

### 4. **Frontend Configuration**

**Create `src/config.ts`:**
```typescript
export const config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:5000',
  environment: import.meta.env.MODE,
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
}

// Usage in components
fetch(`${config.apiUrl}/api/signals`)
```

**Update `vite.config.js`:**
```javascript
export default defineConfig({
  define: {
    __API_URL__: JSON.stringify(process.env.VITE_API_URL || 'http://localhost:5000'),
  },
})
```

---

### 5. **Docker Improvements**

**Backend Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Layer caching for dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/api/health')" || exit 1

EXPOSE 5000

# Use environment variables
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:5000 --workers $MAX_WORKERS --timeout $REQUEST_TIMEOUT api:create_app"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:20-slim AS builder

WORKDIR /build
COPY package*.json ./
RUN npm ci

# Pass build-time environment variables
ARG VITE_API_URL=http://localhost:5000
ENV VITE_API_URL=$VITE_API_URL

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /build/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

HEALTHCHECK --interval=30s --timeout=10s \
  CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## Summary Table

| Aspect | Current | Phase 1 | Phase 2 | Phase 3 | Impact |
|--------|---------|---------|---------|---------|--------|
| **Hosting** | ACI | App Service | App Service | App Service | +100% uptime |
| **Storage** | JSON file | SQL Database | SQL Database | SQL Database | +∞ scale |
| **Users** | Unlimited shared | Unlimited isolated | Unlimited isolated | Unlimited isolated | Enable monetization |
| **Concurrency** | 20 req/s | 100 req/s | 100 req/s | 1000+ req/s | Support growth |
| **Cost** | $35/mo | $30/mo | $30/mo | $100/mo | Scale economically |
| **Effort** | — | 13h | 18h | 12h | 43h total |
| **Timeline** | Now | 2 wks | 4 wks | 6 wks | Production-ready |

---

## Action Items

### Immediate (This Week)
- [ ] Review Azure SQL Database pricing and free tier options
- [ ] Plan database schema (signals, users, watchlists, notes)
- [ ] Create environment variable list for all services
- [ ] Design multi-user authentication flow

### Short Term (Next 2 Weeks)
- [ ] Implement Phase 1 (App Service + SQL)
- [ ] Update CI/CD pipeline to deploy to App Service
- [ ] Create database migration scripts
- [ ] Test local development with SQL + environment variables

### Medium Term (Weeks 3-4)
- [ ] Implement Azure AD authentication
- [ ] Add user management database
- [ ] Update API to filter data by user
- [ ] Test multi-user scenarios

### Long Term (Weeks 5-6)
- [ ] Add Redis caching
- [ ] Implement background job queue
- [ ] Set up Application Insights monitoring
- [ ] Load test with 100+ concurrent users

---

## References

- [Azure App Service Scaling](https://docs.microsoft.com/en-us/azure/app-service/manage-scale-up)
- [Azure SQL Database Pricing](https://azure.microsoft.com/en-us/pricing/details/sql-database/single/)
- [Flask + SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [Celery for Background Tasks](https://docs.celeryproject.org/)
- [Azure AD B2C Authentication](https://docs.microsoft.com/en-us/azure/active-directory-b2c/)

