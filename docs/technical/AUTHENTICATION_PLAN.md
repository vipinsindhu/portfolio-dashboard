# Authentication & User Management Plan

How to add registration and login to the Portfolio Dashboard.

---

## 📊 Current State

**What's Already in Place:**
- ✅ SQLAlchemy ORM configured (`models.py`)
- ✅ Database infrastructure initialized (`init_db()`, `get_session()`)
- ✅ User model template already written (commented out in models.py)
- ✅ Flask backend with API structure
- ✅ Environment variable support (.env file)

**What's Missing:**
- ❌ User authentication routes
- ❌ Password hashing & security
- ❌ JWT tokens for session management
- ❌ Login/registration UI
- ❌ Protected endpoints
- ❌ User-scoped data (portfolios, watchlists)

---

## 🗄️ Database Requirement

**YES - Database integration IS required.**

### Why?

| Need | File-Based | Database | Winner |
|------|-----------|----------|--------|
| User credentials security | ❌ Unsafe (plaintext JSON) | ✅ Hashed + salted | Database |
| Multi-user isolation | ❌ All users share one file | ✅ Separate user records | Database |
| Concurrent access | ❌ File locks cause conflicts | ✅ Transaction support | Database |
| Scalability | ❌ Degrades with users | ✅ Scales well | Database |
| Query performance | ❌ Load entire file | ✅ Indexed lookups | Database |

**Current state:** Portfolio.json is user-agnostic (stores one portfolio)  
**After auth:** Need per-user portfolios, signals, watchlists → requires database

---

## 🏗️ Implementation Approach

### Phase 1: Database & User Model (Week 1)

**1. Uncomment & enhance User model:**
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)  # UUID
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
```

**2. Add user-scoped models:**
```python
class UserPortfolio(Base):
    __tablename__ = "user_portfolios"
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    holdings = Column(JSON, nullable=False)  # Current portfolio.json content
    created_at = Column(DateTime, default=datetime.utcnow)
```

**3. Choose database:**
- **SQLite** (development): `sqlite:///portfolio.db` - simple, no setup
- **PostgreSQL** (production): Robust, scales, add `psycopg2` driver
- Already configured to support both via SQLAlchemy

**Database URL in .env:**
```bash
# Development
DATABASE_URL=sqlite:///portfolio.db

# Production (Azure)
DATABASE_URL=postgresql://user:pass@host/dbname
```

---

### Phase 2: Authentication Routes (Week 2)

**1. Register endpoint:**
```
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**2. Login endpoint:**
```
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "secure_password"
}
```
Returns: JWT token (httpOnly cookie)

**3. Verify endpoint:**
```
GET /api/auth/verify
Returns: Current user info (requires token)
```

**Libraries needed:**
- `bcrypt` - password hashing
- `PyJWT` - JWT tokens
- `flask-cors` - already installed

---

### Phase 3: Protected Routes (Week 3)

**Current routes (public):**
```
GET  /api/portfolio              → Load portfolio (from file)
POST /api/portfolio/upload       → Upload CSV
GET  /api/portfolio/analysis     → Analyze portfolio
```

**After auth (protected):**
```
GET  /api/portfolio              → Load USER's portfolio (from DB)
POST /api/portfolio/upload       → Upload to USER's portfolio
GET  /api/portfolio/analysis     → Analyze USER's portfolio
POST /api/portfolio/save         → Save USER's portfolio
```

**Implementation:**
- Add `@require_auth` decorator to protected routes
- Extract user ID from JWT token
- Filter database queries by user_id
- Return user-specific data

---

### Phase 4: Frontend Login UI (Week 4)

**New pages:**
- `/login` - Login form + "Sign up" link
- `/register` - Registration form + "Already have account?" link
- `/dashboard` - Main app (protected, requires login)

**Changes to existing flow:**
1. Check token on app load
2. Redirect to `/login` if no token
3. Store token in httpOnly cookie
4. Include token in all API requests

**Frontend routes:**
```javascript
<Routes>
  <Route path="/login" element={<LoginPage />} />
  <Route path="/register" element={<RegisterPage />} />
  <Route path="/*" element={<ProtectedLayout />} />  // Requires auth
</Routes>
```

---

## 🔐 Security Checklist

- ✅ Hash passwords with bcrypt (cost factor 12)
- ✅ Use httpOnly, Secure cookies for JWT
- ✅ CSRF protection on forms
- ✅ Rate limiting on auth endpoints (prevent brute force)
- ✅ Validate email format
- ✅ Enforce strong password requirements
- ✅ Hash user emails in logs (PII protection)
- ✅ SQL injection protection (SQLAlchemy parameterized queries)
- ✅ XSS protection (sanitize inputs)

---

## 📋 Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/models.py` | Modify | Uncomment User, add UserPortfolio |
| `backend/auth.py` | Create | Authentication logic (register, login, verify) |
| `backend/api.py` | Modify | Add auth routes, protect endpoints |
| `backend/middleware.py` | Create | JWT verification middleware |
| `frontend/src/pages/LoginPage.jsx` | Create | Login UI |
| `frontend/src/pages/RegisterPage.jsx` | Create | Registration UI |
| `frontend/src/context/AuthContext.jsx` | Create | User state management |
| `frontend/src/hooks/useAuth.js` | Create | Custom hook for auth |
| `.env` | Modify | Add DATABASE_URL, JWT_SECRET |
| `requirements.txt` | Modify | Add bcrypt, PyJWT |

---

## 🚀 Implementation Strategy

### Option A: Quick (2-3 weeks)
- Use SQLite for simplicity
- Basic email/password auth
- Simple JWT tokens
- Minimal UI polish

**Pros:** Fast to implement, good for MVP  
**Cons:** SQLite not ideal for production scale

### Option B: Production-Ready (4-5 weeks)
- Use PostgreSQL from start
- Bcrypt + JWT + refresh tokens
- Email verification
- Password reset flow
- Rate limiting
- Comprehensive testing

**Pros:** Scales to production, secure  
**Cons:** More work upfront

### Option C: Enterprise (6-8 weeks)
- Azure AD integration (SSO)
- OAuth2 with Stripe for billing
- Audit logging
- 2FA support
- Advanced analytics

**Pros:** Enterprise-grade  
**Cons:** Most complex, longest timeline

---

## 💾 Data Migration Strategy

**Current state:**
- One `portfolio.json` file (anonymous user)
- Multiple `signals.json` (global signals)

**After auth:**
- One portfolio per user (in database)
- User-scoped signals (each user sees their own analysis)
- Global signals still available (for recommendations)

**Migration plan:**
1. Create "Default User" account for existing portfolio.json
2. Import portfolio.json data into UserPortfolio table
3. Keep signals global (all users can see all signals)
4. Add user-specific analysis results

---

## 🧪 Testing Strategy

**Unit tests:**
- Password hashing (bcrypt)
- JWT token creation/validation
- Email validation

**Integration tests:**
- Register flow (create user, hash password, store in DB)
- Login flow (lookup user, verify password, return token)
- Protected routes (valid token → access, no token → 403)
- User isolation (user A can't see user B's portfolio)

**Security tests:**
- Brute force attempts (rate limiting)
- SQL injection attempts
- XSS attempts in email/password fields
- CSRF on forms

---

## 📈 Estimated Timeline

| Phase | Tasks | Time | Complexity |
|-------|-------|------|------------|
| 1 | Database + User model | 3-4 days | Low |
| 2 | Auth routes + JWT | 4-5 days | Medium |
| 3 | Protect endpoints | 3-4 days | Medium |
| 4 | Login/Register UI | 4-5 days | Medium |
| 5 | Testing + polish | 5-7 days | High |
| **Total** | | **3-4 weeks** | **Medium** |

---

## ⚠️ Things to Watch Out For

1. **Session persistence:** Token expires → user gets logged out → educate users about refresh
2. **CORS/cookies:** Different domains require careful CORS setup
3. **Password reset:** Need email service (Sendgrid, etc.) if implementing
4. **Data ownership:** Ensure users can't query other users' data
5. **Legacy data:** Migration of current portfolio.json to new system
6. **Database secrets:** Don't commit DATABASE_URL to git

---

## 🎯 Recommended Approach

**Go with Option B (Production-Ready):**
- PostgreSQL on Azure (your current platform)
- Bcrypt + JWT tokens
- Email validation (optional, can add later)
- Good security posture from day 1
- Scales with your user base

---

## Next Steps

1. **Decide:** Which implementation option? (A, B, or C)
2. **Database:** Choose PostgreSQL or SQLite
3. **Setup:** Create database tables
4. **Implement:** Follow Phase 1-5 above
5. **Test:** Write unit + integration tests
6. **Deploy:** Update Docker, Azure config

---

**Questions before starting?**
- What's your expected user count?
- Do you need email verification?
- Do you want password reset functionality?
- Should portfolios be private or shareable?

---

**Last Updated:** 2026-06-08
