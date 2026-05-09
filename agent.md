# SQL Architect - Project Status & Agent Briefing

**Project Status**: Phase 1 Complete ✅ | Phase 1.5 Complete (Security Hardening) ✅ | Ready for Phase 2

**Date**: May 9, 2026

---

## 📊 Executive Summary

**SQL Architect - The Data Agent** is an enterprise-grade AI-powered SQL query translator built with FastAPI, React, Google Gemini API, and Docker. It translates natural language prompts into optimized MySQL queries with production-ready security architecture (zero hardcoded credentials).

### Current Status
- **Backend**: Fully functional, secure, containerized
- **Frontend**: React app running locally (not containerized yet)
- **Database**: MySQL 8.0 with users and query_history tables
- **Cache**: Redis 7-alpine for schema caching
- **AI**: Google Gemini API integration with dynamic model selection
- **Security**: Enterprise-grade (OWASP compliant, audit logging, rate limiting)

---

## 🏗️ Architecture Overview

### Hexagonal Architecture (Backend)

```
┌─────────────────────────────────────────────────────────┐
│            FastAPI Application (main.py)                │
│  - Logging setup, error handlers, startup validation    │
│  - Rate limiting (slowapi: 100 req/60s per IP)          │
│  - CORS middleware (whitelist-based)                    │
│  - Security headers middleware                          │
│  - Audit middleware (operation tracking)                │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│      PORTS & ADAPTERS LAYER (app/application/)          │
│  ├─ controller.py: REST API endpoints (7 routes)        │
│  ├─ service.py: SqlGeneratorService (Gemini integration)│
│  ├─ auth_service.py: JWT + bcrypt passwords            │
│  ├─ sql_validator.py: Whitelist validation             │
│  ├─ schemas.py: Pydantic request/response models       │
│  └─ dependencies.py: FastAPI dependency injection      │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│          DOMAIN LAYER (app/domain/)                      │
│  ├─ user.py: User entity (email PK, password, dates)    │
│  ├─ query_history.py: QueryHistory entity (audit trail)│
│  └─ interfaces.py: Repository interfaces                │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│       INFRASTRUCTURE LAYER (app/infrastructure/)        │
│  ├─ repository.py: Schema introspection (MySQL)        │
│  ├─ user_repository.py: User CRUD                      │
│  ├─ query_history_repository.py: History CRUD          │
│  ├─ cache_service.py: Redis caching                    │
│  ├─ security_logger.py: Secure logging (data masking)  │
│  └─ audit_middleware.py: Audit + security headers      │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│       CONFIGURATION LAYER (app/config/)                 │
│  └─ settings.py: Centralized BaseSettings (40+ options)│
│     - All env vars in one place                         │
│     - Type-safe validation with pydantic               │
│     - Production validation at startup                  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│          EXTERNAL SYSTEMS                               │
│  ├─ MySQL 8.0 (port 3307 in docker)                   │
│  ├─ Redis 7-alpine (port 6379)                        │
│  └─ Google Generative AI (Gemini)                      │
└─────────────────────────────────────────────────────────┘
```

### API Endpoints (7 routes)

#### Authentication (Public)
```
POST   /api/v1/auth/register          Register new user
POST   /api/v1/auth/login             Login (returns JWT)
GET    /api/v1/auth/me                Get current user (requires JWT)
```

#### SQL Generation & Schema (Protected)
```
POST   /api/v1/generate-sql           Generate SQL from natural language
GET    /api/v1/schema                 Get full database schema (cached)
GET    /api/v1/schema/{table}         Get specific table schema (cached)
GET    /api/v1/tables                 List all tables (cached)
```

#### Query History (Protected)
```
GET    /api/v1/history                Get user's query history (paginated)
GET    /api/v1/history/{id}           Get specific query (ownership check)
DELETE /api/v1/history/{id}           Delete query (ownership check)
```

#### System
```
GET    /health                        Health check (no auth needed)
```

---

## 📁 Project Structure

```
SqlAgent/
├── back/                              # Backend (Python/FastAPI)
│   ├── app/
│   │   ├── config/
│   │   │   └── settings.py            # CENTRALIZED CONFIG (BaseSettings)
│   │   │       ├─ DATABASE_URL, GOOGLE_API_KEY, JWT_SECRET
│   │   │       ├─ CORS_ORIGINS, FORCE_HTTPS, API_RELOAD
│   │   │       ├─ All 40+ settings with type validation
│   │   │       └─ Production validation method
│   │   │
│   │   ├── domain/                    # Domain Layer
│   │   │   ├─ user.py                 # User entity (SQLAlchemy)
│   │   │   ├─ query_history.py        # QueryHistory entity
│   │   │   └─ interfaces.py           # Repository contracts
│   │   │
│   │   ├── application/               # Application Layer (Business Logic)
│   │   │   ├─ controller.py           # FastAPI routes (7 endpoints)
│   │   │   ├─ service.py              # SqlGeneratorService (Gemini)
│   │   │   ├─ auth_service.py         # JWT + password hashing
│   │   │   ├─ sql_validator.py        # Whitelist-based SQL validation
│   │   │   ├─ schemas.py              # Pydantic models (10+ schemas)
│   │   │   └─ dependencies.py         # FastAPI dependency injection
│   │   │
│   │   └── infrastructure/            # Infrastructure Layer (External Services)
│   │       ├─ repository.py           # Schema introspection (cached)
│   │       ├─ user_repository.py      # User CRUD + pool management
│   │       ├─ query_history_repo.py   # History CRUD + size limits
│   │       ├─ cache_service.py        # Redis wrapper (graceful fallback)
│   │       ├─ security_logger.py      # Logging with data masking
│   │       └─ audit_middleware.py     # Audit trail + security headers
│   │
│   ├── main.py                        # FastAPI app factory
│   │   ├─ Logger setup
│   │   ├─ Middleware registration
│   │   ├─ Exception handlers
│   │   ├─ Startup/shutdown events
│   │   └─ Production validation
│   │
│   ├── Dockerfile                     # Container definition
│   ├── requirements.txt               # 15 pinned dependencies
│   ├── .env                           # Runtime secrets (git-ignored)
│   ├── .env.example                   # Config template (documented)
│   └── scripts/
│       └─ validate_production.py      # Pre-deployment validator
│
├── frontend/                           # Frontend (React)
│   ├── src/
│   │   ├── components/
│   │   ├── controllers/
│   │   ├── services/
│   │   └── App.js
│   ├── package.json
│   └── .env
│
├── docker-compose.yml                 # Multi-container orchestration
│   ├─ mysql (port 3307:3306)
│   ├─ redis (port 6379:6379)
│   └─ backend (port 8001:8000)
│
├── .gitignore                         # Security patterns
├── SECURITY.md                        # Security architecture (300+ lines)
├── VERIFICATION.md                    # Verification checklist
├── README.md                          # User documentation
└── agent.md                           # THIS FILE - Agent briefing
```

---

## 🔒 Security Architecture (Phase 1.5 Complete)

### ✅ Zero Hardcoded Credentials

All configuration comes from environment variables through centralized `settings.py`:
- No `database_url: str = "mysql://..."`
- No `JWT_SECRET = "hardcoded"`
- No `allow_origins=["localhost:3000"]`
- No `timeout=30` constants scattered in code

### ✅ 12 Security Layers

1. **Centralized Configuration** (`app/config/settings.py`)
   - BaseSettings with 40+ typed options
   - Production validation at startup
   - Required values enforced

2. **Authentication** (`app/application/auth_service.py`)
   - JWT with HS256
   - Bcrypt password hashing
   - Configurable password strength (8 chars, uppercase, number, special)
   - 24-hour token expiration

3. **SQL Security** (`app/application/sql_validator.py`)
   - Command whitelist (SELECT only)
   - Blocks: DROP, DELETE, INSERT, UPDATE, ALTER, GRANT, REVOKE
   - Query length limits (5000 chars)

4. **Audit Logging** (`app/infrastructure/security_logger.py`)
   - JSON structured logs
   - Auto-masks: passwords, API keys, tokens, emails, credit cards, SSN
   - Prevents log injection

5. **Audit Trail** (`app/infrastructure/audit_middleware.py`)
   - Tracks: user registration, login, SQL generation, history access
   - Records: user, operation, status, duration, client IP
   - Immutable audit log

6. **Security Headers** (AuditMiddleware in `audit_middleware.py`)
   - X-Content-Type-Options: nosniff
   - X-Frame-Options: DENY
   - CSP, STS, X-XSS-Protection
   - Removes server identification

7. **Rate Limiting** (`main.py` with slowapi)
   - 100 requests per 60 seconds per IP
   - Returns 429 Too Many Requests
   - Prevents brute force/DoS

8. **CORS Protection** (TrustedHostMiddleware + CORSMiddleware)
   - Whitelist-based origin validation
   - Explicit method restrictions (GET, POST)
   - Explicit header restrictions

9. **Data Ownership** (All repositories)
   - Every query tied to user via foreign key
   - Ownership checks on access/delete
   - No cross-user data leakage

10. **Error Handling** (`main.py` exception handlers)
    - Generic messages in production
    - Detailed errors only in development
    - No stack traces exposed
    - Proper HTTP status codes

11. **Input Validation** (`app/application/schemas.py`)
    - Pydantic validation on all inputs
    - Email format validation
    - Length limits on prompts (2000 chars)

12. **Cache Security** (`app/infrastructure/cache_service.py`)
    - Redis password support
    - Optional Redis disabling
    - Configurable TTL (1 hour default)
    - Graceful fallback to DB

### ✅ Threat Mitigations

| Threat | Mitigation |
|--------|-----------|
| SQL Injection | Parameterized queries + command whitelist |
| Auth Bypass | JWT validation + token expiration |
| Unauthorized Access | User ownership checks + CORS |
| Brute Force | Rate limiting |
| Configuration Drift | Centralized BaseSettings + startup validation |
| Credential Exposure | No hardcoded values + auto-masking in logs |
| XSS | JSON API + CSP headers |
| CSRF | CORS validation + stateless JWT |
| Privilege Escalation | Stateless JWT + no role system yet |
| Data Exposure | Generic errors in production |

### ✅ Production Validation

Before deploying, run:
```bash
python back/scripts/validate_production.py
```

Checks:
- ENVIRONMENT=production
- Remote database (not localhost)
- JWT secret ≥32 characters
- Google API key present
- CORS origins explicit
- FORCE_HTTPS=true
- API_RELOAD=false
- Log level WARNING or higher
- No localhost in CORS

---

## 🚀 Technology Stack

### Backend
- **FastAPI 0.104.1** - Modern async web framework
- **Uvicorn 0.24.0** - ASGI server
- **SQLAlchemy 2.0.23** - ORM for database
- **PyMySQL 1.1.0** - MySQL driver
- **Pydantic 2.5.0** - Request/response validation
- **PyJWT 2.8.1** - JWT implementation
- **passlib[bcrypt] 1.7.4** - Password hashing
- **Redis 5.0.1** - Cache client
- **google-generativeai 0.4.0** - Gemini API
- **slowapi 0.1.8** - Rate limiting
- **sqlparse 0.4.4** - SQL validation
- **python-dotenv 1.0.0** - Environment loading

### Database & Cache
- **MySQL 8.0** - Main database
- **Redis 7-alpine** - In-memory cache

### Frontend
- **React** - UI framework
- **Node.js 16+** - Runtime

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Orchestration

---

## 🔧 How to Run

### Prerequisites
- Docker & Docker Compose
- Node.js 16+ (for frontend)
- Python 3.11 (for local development)
- Git

### 1. Setup Backend

```bash
cd back

# Copy environment template
cp .env.example .env

# Edit .env with your settings (especially GOOGLE_API_KEY)
nano .env
```

**Minimal .env for development:**
```bash
DATABASE_URL=mysql+pymysql://root:root@db/projects_db
GOOGLE_API_KEY=your-google-api-key
JWT_SECRET=dev-secret-not-secure-min-16-chars
REDIS_HOST=redis
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000
```

### 2. Start Backend Services

```bash
# From back/ directory
docker-compose up --build

# Logs show startup validation
# Look for: "All critical configurations validated"
```

Services:
- **MySQL**: localhost:3307 (user: root, password: root)
- **Redis**: localhost:6379
- **FastAPI**: localhost:8001 (API docs: /api/docs)

### 3. Setup Frontend

```bash
cd frontend

npm install
npm start
```

Frontend runs on localhost:3000

### 4. Test the System

```bash
# Register user
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!@#","full_name":"Test User"}'

# Login (get token)
TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!@#"}' | jq -r .access_token)

# Generate SQL
curl -X POST http://localhost:8001/api/v1/generate-sql \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Get all active users"}'
```

---

## 📝 Development Workflow

### Adding a New API Endpoint

1. **Define Schema** (`app/application/schemas.py`)
   ```python
   class MyRequest(BaseModel):
       field: str
   
   class MyResponse(BaseModel):
       result: str
   ```

2. **Implement Logic** (`app/application/service.py` or create new service)
   ```python
   async def my_logic(request: MyRequest) -> str:
       return "result"
   ```

3. **Add Route** (`app/application/controller.py`)
   ```python
   @router.post("/my-endpoint")
   async def my_endpoint(
       request: MyRequest,
       current_user: str = Depends(get_current_user)  # For protected endpoints
   ):
       result = await service.my_logic(request)
       return MyResponse(result=result)
   ```

4. **Log Operation** (if sensitive)
   - Logger automatically masks sensitive data
   - Use: `logger.info(f"Operation: {operation}")`

5. **Test**
   - Curl request or pytest
   - Check audit logs: `docker-compose logs backend | grep audit`

### Database Migration Example

1. Create new SQLAlchemy model in `app/domain/`
2. Create repository in `app/infrastructure/`
3. Inject repository into controller
4. Database tables auto-created on repository init

### Adding Configuration Option

1. Add field to `Settings` class in `app/config/settings.py`
2. Document in `.env.example`
3. Use in code: `from app.config.settings import settings; print(settings.MY_OPTION)`
4. For production: run `python back/scripts/validate_production.py`

---

## 🐛 Common Issues & Solutions

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Validate config
python back/scripts/validate_production.py

# Check env vars loaded
docker-compose exec backend env | grep DATABASE
```

### Database connection fails
```bash
# Verify MySQL is running
docker-compose ps

# Test connection manually
docker-compose exec backend python -c "import sqlalchemy; print('OK')"

# Check credentials in .env
cat back/.env | grep DATABASE_URL
```

### Redis not working
```bash
# Test Redis
docker-compose exec backend redis-cli -h redis ping

# Check cache keys
docker-compose exec backend redis-cli -h redis KEYS "schema:*"

# Disable Redis (falls back to DB)
# Set REDIS_ENABLED=false in .env
```

### Rate limiting too strict
```bash
# Adjust in back/.env
RATE_LIMIT_REQUESTS=200
RATE_LIMIT_WINDOW=60
```

### Audit logs not showing
```bash
# Logs are JSON-formatted
docker-compose logs backend | grep "operation"

# View in pretty format
docker-compose logs backend | grep "operation" | jq
```

---

## ✅ Completed Features

### Phase 1: Foundation ✅
- [x] User authentication (JWT + bcrypt)
- [x] User registration & login
- [x] Query history persistence
- [x] SQL validation (command whitelist)
- [x] Redis schema caching (1-hour TTL)
- [x] Google Gemini API integration
- [x] Dynamic model selection
- [x] Markdown removal from LLM output
- [x] Protected API endpoints
- [x] User ownership checks on history
- [x] Query history CRUD endpoints

### Phase 1.5: Security Hardening ✅
- [x] Centralized configuration management (BaseSettings)
- [x] Zero hardcoded credentials
- [x] Production validation script
- [x] Secure logging with data masking
- [x] Audit middleware for operation tracking
- [x] Security headers (OWASP)
- [x] Password strength validation
- [x] Rate limiting (slowapi)
- [x] Comprehensive SECURITY.md
- [x] .env.example with full documentation
- [x] Error handling (generic in production)

---

## 🔜 Roadmap: Futuras Fases

### Phase 2: Scalability & Multi-Database Support

#### Phase 2.1: Async Workers with Celery/RabbitMQ
**Objective**: Offload long-running LLM calls from HTTP request thread

**Implementation Details**:
```
Frontend Request
    ↓
FastAPI (returns immediately with job_id)
    ↓
RabbitMQ Queue
    ↓
Celery Workers (process in background)
    ↓
Update Job Status in Redis
    ↓
Frontend polls GET /api/v1/jobs/{job_id}/status
```

**Files to Create/Modify**:
- `app/domain/job.py` - Job entity (status, progress, result)
- `app/infrastructure/job_repository.py` - Job persistence
- `app/infrastructure/celery_app.py` - Celery configuration
- `app/application/job_service.py` - Job management logic
- `app/application/controller.py` - Add job endpoints
- `requirements.txt` - Add celery, kombu, redis
- `docker-compose.yml` - Add rabbitmq service

**New Endpoints**:
```
POST   /api/v1/jobs/generate-sql          Start async SQL generation
GET    /api/v1/jobs/{job_id}/status       Get job status & progress
GET    /api/v1/jobs/{job_id}/result       Get job result (when complete)
DELETE /api/v1/jobs/{job_id}               Cancel job
GET    /api/v1/jobs                       List user's jobs
```

**Database Changes**:
- New table: `jobs` (id, user_email, status, prompt, result, created_at, updated_at)
- Status values: PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
- Result stored in `job_result` text field (nullable until complete)

**Configuration** (add to settings.py):
```python
CELERY_BROKER_URL: str           # redis://redis:6379/0
CELERY_RESULT_BACKEND: str       # redis://redis:6379/0
JOB_TIMEOUT_SECONDS: int = 300   # 5 minutes
JOB_STATUS_POLL_INTERVAL: int = 2  # seconds
```

**Key Features**:
- [ ] Celery workers configured (concurrency, pool size)
- [ ] RabbitMQ message broker
- [ ] Job persistence (SQLite or Redis)
- [ ] Status polling endpoint
- [ ] Webhook callbacks (optional)
- [ ] Job cancellation
- [ ] Timeout handling
- [ ] Error recovery & retries
- [ ] Frontend job UI (progress bar, results)
- [ ] Job history (per user)

**Benefits**:
- FastAPI returns immediately (better UX)
- Long LLM calls don't block request handler
- Scales horizontally (add more workers)
- Handles thousands of concurrent users
- Can process multiple jobs simultaneously

#### Phase 2.2: Multi-Database Support
**Objective**: Support PostgreSQL, SQL Server, BigQuery, SQLite in addition to MySQL

**Architecture**:
```
DatabaseFactory (settings.DB_TYPE)
    ├─ MySQLRepository (current)
    ├─ PostgreSQLRepository
    ├─ SQLServerRepository
    └─ BigQueryRepository
```

**Files to Create**:
- `app/domain/database_provider.py` - Database provider interface
- `app/infrastructure/providers/mysql_repository.py` - Refactored current code
- `app/infrastructure/providers/postgres_repository.py` - New
- `app/infrastructure/providers/sqlserver_repository.py` - New
- `app/infrastructure/providers/bigquery_repository.py` - New
- `app/infrastructure/database_factory.py` - Factory pattern

**Configuration** (add to settings.py):
```python
DATABASE_TYPE: str = "mysql"  # mysql, postgresql, sqlserver, bigquery
DATABASE_URL: str  # Connection string varies by type
DATABASE_DIALECT: str  # SQLAlchemy dialect
DATABASE_DRIVER: str  # Driver name
DATABASE_TIMEOUT: int = 30
```

**Implementation Per DB Type**:

**MySQL** (Current):
- Driver: PyMySQL
- Connection URL: `mysql+pymysql://user:pass@host/db`
- Special handling: None (already working)

**PostgreSQL**:
- Driver: psycopg2
- Connection URL: `postgresql+psycopg2://user:pass@host/db`
- Requirements: `psycopg2-binary==2.9.9`
- Special handling: SERIAL -> BIGSERIAL for IDs, TEXT for unlimited strings

**SQL Server**:
- Driver: pyodbc
- Connection URL: `mssql+pyodbc://user:pass@host/db?driver=ODBC+Driver+17+for+SQL+Server`
- Requirements: `pyodbc==4.0.38`
- Special handling: Collation, query syntax differences
- Authentication: Can use Windows Auth or SQL Auth

**BigQuery**:
- Driver: google-cloud-bigquery
- Connection: Service account JSON
- Requirements: `google-cloud-bigquery==3.11.1`
- Special handling: No transactions, schema inference, cost optimization

**New Endpoints**:
```
GET    /api/v1/databases           List connected databases
POST   /api/v1/databases           Add new database connection
GET    /api/v1/databases/{id}      Get database info
PUT    /api/v1/databases/{id}      Update connection
DELETE /api/v1/databases/{id}      Remove connection
GET    /api/v1/schema?db_id=1      Get schema from specific DB
```

**Database Changes**:
- New table: `database_connections` 
  - id, user_email, db_type, connection_name, connection_url, is_active, created_at
- New table: `query_history_v2`
  - Add `database_id` foreign key

**Key Features**:
- [ ] Database connection management
- [ ] Per-connection schema caching
- [ ] Connection pooling per database
- [ ] Multi-database query generation
- [ ] Connection encryption (passwords stored encrypted)
- [ ] Connection health checks
- [ ] Automatic driver installation
- [ ] Connection testing endpoint
- [ ] Dialect-specific SQL generation
- [ ] Cross-database query translation (future)

**Benefits**:
- Enterprises can query all their databases
- Not locked to MySQL
- Supports data warehouses (BigQuery)
- Connection management UI for users

#### Phase 2.3: Observability & Monitoring
**Objective**: Production-grade logging, metrics, and error tracking

**Files to Create**:
- `app/infrastructure/metrics.py` - Prometheus metrics
- `app/infrastructure/tracing.py` - OpenTelemetry setup
- `docker-compose.monitoring.yml` - Monitoring stack
- `config/prometheus.yml` - Prometheus config
- `config/grafana/dashboards/` - Dashboard definitions

**Configuration** (add to settings.py):
```python
PROMETHEUS_ENABLED: bool = True
PROMETHEUS_PORT: int = 9090
OTEL_ENABLED: bool = True
OTEL_EXPORTER: str = "jaeger"  # jaeger, zipkin
SENTRY_ENABLED: bool = True
SENTRY_SAMPLE_RATE: float = 0.1  # 10% of transactions
METRICS_LABELS: dict = {"service": "sql-architect", "version": "1.0"}
```

**Metrics to Track**:
```
sql_generation_duration_seconds       # Histogram
sql_generation_errors_total           # Counter
api_request_duration_seconds          # Histogram
cache_hit_ratio                       # Gauge
database_connection_pool_size         # Gauge
jwt_validation_duration_ms            # Histogram
audit_log_entries_total               # Counter
gemini_api_calls_total                # Counter
rate_limit_exceeded_total             # Counter
```

**Logging Improvements**:
- [ ] Request ID correlation (passed through all logs)
- [ ] Structured logging (already JSON format)
- [ ] Log sampling in production
- [ ] Log aggregation (ELK/Datadog/CloudWatch)
- [ ] Trace context propagation

**Tools to Integrate**:
- **Prometheus**: Metrics scraping & storage
- **Grafana**: Visualization dashboards
- **Jaeger**: Distributed tracing
- **Sentry**: Error tracking & session replay
- **OpenTelemetry**: Unified instrumentation

**New Endpoints**:
```
GET    /metrics                   Prometheus metrics (no auth)
GET    /api/v1/health/detailed    Health + dependencies status
GET    /api/v1/health/readiness   K8s readiness probe
GET    /api/v1/health/liveness    K8s liveness probe
```

**Dashboard Queries** (Grafana):
- Requests per second (RPS)
- P50/P95/P99 latency
- Error rate by endpoint
- Cache hit ratio
- Database connection pool usage
- Celery worker status
- Gemini API quota usage
- User activity heatmap

**Key Features**:
- [ ] Prometheus metrics export
- [ ] Grafana dashboards
- [ ] Distributed tracing with Jaeger
- [ ] Error tracking with Sentry
- [ ] Request ID logging
- [ ] Performance profiling
- [ ] Alerting rules
- [ ] Log sampling
- [ ] Metrics retention (15 days)
- [ ] Custom business metrics

**Benefits**:
- Understand system performance
- Detect issues before users complain
- Debug production problems
- Capacity planning
- Cost optimization (track API usage)

---

### Phase 3: Enterprise Features & Multi-Tenancy

#### Phase 3.1: Multi-Tenancy & Organizations
**Objective**: Multiple organizations with separate data and configurations

**Architecture**:
```
Organization 1                Organization 2
├─ User 1                    ├─ User A
├─ User 2                    ├─ User B
├─ Database Connections      ├─ Database Connections
├─ Query History             ├─ Query History
└─ API Keys                  └─ API Keys
```

**Files to Create**:
- `app/domain/organization.py` - Organization entity
- `app/domain/organization_member.py` - Member entity
- `app/infrastructure/organization_repository.py` - Org CRUD
- `app/infrastructure/organization_member_repository.py` - Member CRUD
- `app/application/organization_service.py` - Org logic
- `app/application/middleware/tenant_middleware.py` - Tenant isolation

**Configuration** (add to settings.py):
```python
MULTI_TENANCY_ENABLED: bool = True
TENANT_ISOLATION_LEVEL: str = "database"  # database, schema, row
DEFAULT_ORG_QUOTA_QUERIES_PER_DAY: int = 10000
```

**Database Changes**:
- New table: `organizations` (id, name, owner_email, plan, created_at)
- New table: `organization_members` (id, org_id, user_email, role, created_at)
- New table: `organization_settings` (org_id, setting_key, setting_value)
- Modify `users`: Add `default_org_id` (nullable for backward compat)
- Modify `query_history`: Add `org_id` index

**New Endpoints**:
```
POST   /api/v1/organizations              Create organization
GET    /api/v1/organizations/{id}         Get org details
PUT    /api/v1/organizations/{id}         Update org
DELETE /api/v1/organizations/{id}         Delete org (admin only)
GET    /api/v1/organizations/{id}/members List members
POST   /api/v1/organizations/{id}/members Invite member
DELETE /api/v1/organizations/{id}/members/{user} Remove member
GET    /api/v1/organizations/{id}/settings Get org settings
```

**Tenant Isolation**:
- [ ] Data never leaks between orgs
- [ ] Query history filtered by org
- [ ] Database connections isolated
- [ ] API keys scoped to org
- [ ] Audit logs include org context
- [ ] Usage tracking per org

#### Phase 3.2: Role-Based Access Control (RBAC)
**Objective**: Fine-grained permissions for different user roles

**Roles**:
```
Owner
├─ Can: Manage org, invite/remove members, view all queries, change settings
Analyst
├─ Can: Generate queries, view own queries, invite viewers, manage connections
Viewer
├─ Can: View generated queries (read-only)
Guest
└─ Can: View documentation only
```

**Files to Create**:
- `app/domain/role.py` - Role entity
- `app/application/permission.py` - Permission checking
- `app/application/middleware/rbac_middleware.py` - RBAC enforcement
- Database roles table

**Configuration** (add to settings.py):
```python
RBAC_ENABLED: bool = True
DEFAULT_ROLE: str = "analyst"
```

**New Endpoint**:
```
PATCH  /api/v1/organizations/{id}/members/{user}/role  Change user role
```

**Permission Checks**:
- [ ] Decorator-based: `@require_role("analyst")`
- [ ] Query-level: User can only see own queries (unless owner)
- [ ] Connection-level: Org members can access org connections
- [ ] Settings-level: Only owner can change settings

#### Phase 3.3: SQL Execution & Results
**Objective**: Execute validated SQL queries safely and return results

**Files to Create**:
- `app/domain/query_result.py` - Query result entity
- `app/infrastructure/query_executor.py` - Safe execution layer
- `app/application/execution_service.py` - Execution logic
- `app/infrastructure/query_sandbox.py` - Sandbox implementation

**Configuration** (add to settings.py):
```python
SQL_EXECUTION_ENABLED: bool = False  # Disable by default
EXECUTION_TIMEOUT_SECONDS: int = 30
MAX_RESULT_ROWS: int = 10000
READONLY_MODE: bool = True
```

**Safety Features**:
- [ ] Read-only mode (no INSERT/UPDATE/DELETE)
- [ ] Row limit (max 10k results)
- [ ] Timeout protection (30s max)
- [ ] Resource limits (CPU, memory)
- [ ] Query logging (for audit)
- [ ] User approval workflow (optional)
- [ ] Dry run mode (explain plan only)
- [ ] Cost estimation (BigQuery)

**New Endpoints**:
```
POST   /api/v1/queries/execute           Execute query (validated)
GET    /api/v1/queries/{id}/results      Get query results
GET    /api/v1/queries/{id}/explain      Get execution plan
POST   /api/v1/queries/dry-run           Test query without executing
```

**Result Format**:
```json
{
  "query_id": "uuid",
  "rows": [
    {"id": 1, "name": "John"},
    {"id": 2, "name": "Jane"}
  ],
  "column_info": [
    {"name": "id", "type": "INTEGER"},
    {"name": "name", "type": "VARCHAR"}
  ],
  "execution_time_ms": 250,
  "row_count": 2,
  "total_rows_available": 100000
}
```

#### Phase 3.4: Results Visualization
**Objective**: Charts, tables, and dashboards for query results

**Frontend Components**:
```
QueryResults
├─ Table View (sortable, filterable)
├─ Chart View (line, bar, pie)
├─ Map View (geospatial)
├─ Export Options (CSV, JSON, Excel)
└─ Sharing Options (public link, embed)
```

**Files to Create** (Frontend):
- `src/components/ResultsTable.js` - Data table
- `src/components/ResultsChart.js` - Chart visualization
- `src/components/ResultsMap.js` - Geospatial viz
- `src/components/ExportModal.js` - Export options

**Visualization Library**:
- **Recharts** or **Chart.js** for charts
- **Leaflet** for maps
- **react-grid-layout** for dashboards

**Key Features**:
- [ ] Auto-detect chart type (based on data)
- [ ] Customizable colors & labels
- [ ] Drill-down capability
- [ ] Export to CSV/JSON/Excel
- [ ] Public sharing links
- [ ] Embedded visualizations
- [ ] Saved dashboard layouts

#### Phase 3.5: User Quotas & Billing
**Objective**: Usage tracking and billing integration

**Configuration** (add to settings.py):
```python
BILLING_ENABLED: bool = False
STRIPE_API_KEY: str = ""
QUOTA_ENFORCEMENT: bool = True
```

**Database Changes**:
- New table: `usage_metrics` (org_id, queries_count, db_connections, api_calls, timestamp)
- New table: `billing_plans` (id, name, monthly_queries, price_cents)
- New table: `subscriptions` (id, org_id, plan_id, status, next_billing_date)
- New table: `invoices` (id, org_id, amount_cents, status, url)

**Quotas**:
```
Free Tier:
  - 100 queries/day
  - 1 database connection
  - 1 user

Pro Tier ($29/mo):
  - 10,000 queries/day
  - 10 database connections
  - 5 users

Enterprise: Custom
  - Unlimited
  - Dedicated support
  - SLA
```

**Billing Integration**:
- [ ] Stripe webhook handling
- [ ] Automatic invoicing
- [ ] Usage metrics collection
- [ ] Quota enforcement
- [ ] Overage handling
- [ ] Trial period management
- [ ] Plan upgrades/downgrades
- [ ] Payment history

**New Endpoints**:
```
GET    /api/v1/billing/plans              List pricing plans
POST   /api/v1/billing/subscribe          Start subscription
GET    /api/v1/billing/subscription       Get current subscription
POST   /api/v1/billing/cancel             Cancel subscription
GET    /api/v1/billing/usage              Get usage metrics
GET    /api/v1/billing/invoices           Get past invoices
```

---

### Phase 4: Advanced Features (Future)

#### Phase 4.1: API Keys & Service Accounts
- [ ] Generate API keys for programmatic access
- [ ] Service account authentication
- [ ] Rate limits per API key
- [ ] API key rotation
- [ ] Audit log per key

#### Phase 4.2: Query Templates & Saved Queries
- [ ] Save queries for reuse
- [ ] Query templates with placeholders
- [ ] Sharing templates within org
- [ ] Version history
- [ ] Query recommendations

#### Phase 4.3: Data Lineage & Impact Analysis
- [ ] Track data sources
- [ ] Show column dependencies
- [ ] Impact analysis (if I change this field...)
- [ ] Data dictionary integration
- [ ] PII detection

#### Phase 4.4: Scheduled Queries & Reports
- [ ] Schedule queries to run at intervals
- [ ] Email reports automatically
- [ ] Data export to S3/GCS
- [ ] Webhook notifications
- [ ] Report scheduling UI

#### Phase 4.5: AI Enhancements
- [ ] Query optimization suggestions
- [ ] Anomaly detection
- [ ] Cost prediction (for BigQuery)
- [ ] Natural language query feedback
- [ ] Context-aware suggestions

#### Phase 4.6: Advanced Security
- [ ] Field-level encryption
- [ ] Fine-grained data masking
- [ ] SSO integration (Okta, Azure AD)
- [ ] SCIM provisioning
- [ ] IP whitelisting
- [ ] VPC private connectivity

#### Phase 4.7: Infrastructure & Scale
- [ ] Kubernetes deployment
- [ ] Horizontal pod autoscaling
- [ ] Multi-region deployment
- [ ] Database sharding
- [ ] Caching layer optimization

---

## 📊 Implementation Timeline (Estimated)

| Phase | Duration | Priority | Status |
|-------|----------|----------|--------|
| Phase 1 (Foundation) | 2 weeks | Critical | ✅ DONE |
| Phase 1.5 (Security) | 1 week | Critical | ✅ DONE |
| Phase 2.1 (Async Workers) | 2 weeks | High | 📋 Next |
| Phase 2.2 (Multi-DB) | 2 weeks | High | 📋 Planned |
| Phase 2.3 (Observability) | 1 week | Medium | 📋 Planned |
| Phase 3.1 (Multi-Tenancy) | 2 weeks | High | 📋 Planned |
| Phase 3.2 (RBAC) | 1 week | Medium | 📋 Planned |
| Phase 3.3 (SQL Execution) | 2 weeks | Medium | 📋 Planned |
| Phase 3.4 (Visualization) | 2 weeks | Low | 📋 Planned |
| Phase 3.5 (Billing) | 2 weeks | Medium | 📋 Planned |
| Phase 4+ (Advanced) | TBD | Low | 📋 Future |

**Total Estimated**: ~17 weeks for Phases 1-3.5

---

## 📚 Key Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `app/config/settings.py` | Centralized configuration | 120+ |
| `main.py` | FastAPI app with security | 150+ |
| `app/application/controller.py` | REST API endpoints | 170 |
| `app/application/service.py` | Gemini integration | 150+ |
| `app/application/auth_service.py` | JWT + passwords | 100+ |
| `app/infrastructure/security_logger.py` | Logging + masking | 150 |
| `app/infrastructure/audit_middleware.py` | Audit + headers | 120 |
| `SECURITY.md` | Security documentation | 300+ |
| `scripts/validate_production.py` | Production validator | 120 |
| `.env.example` | Config template | 100+ |

---

## 🎯 Code Conventions

### Variable Naming
- `snake_case` for functions and variables
- `UPPER_CASE` for constants
- `PascalCase` for classes

### Error Handling
- Use FastAPI `HTTPException` for API errors
- Log errors with context: `logger.error(f"Operation failed: {str(e)}")`
- Never expose internal details in production

### Database Queries
- Use SQLAlchemy ORM (never raw SQL in app code)
- Always validate user ownership before access
- Use connection pooling (configured in settings)

### Logging
- Use `SecurityLogger` for all operations
- Automatic masking happens (no manual filtering needed)
- Include user context when available

### API Responses
- Return Pydantic models (auto-validation)
- Use proper HTTP status codes
- Include error messages for failures

### Caching
- Cache keys: `{entity}:{identifier}` (e.g., `schema:table:users`)
- Cache TTL from settings (no hardcoding)
- Graceful fallback if Redis unavailable

---

## 📞 Support & Resources

- **Architecture Questions**: See SECURITY.md & README.md
- **Configuration**: See .env.example
- **API Documentation**: http://localhost:8001/api/docs (Swagger UI)
- **Production Deployment**: Run `python back/scripts/validate_production.py`
- **Security Issues**: See SECURITY.md > Incident Response

---

## 🎓 For Next Developer/Agent

When taking over this project:

1. **First**: Read this file entirely
2. **Second**: Check `SECURITY.md` for security architecture
3. **Third**: Review `.env.example` for all configuration options
4. **Fourth**: Run `docker-compose up --build` to verify setup
5. **Fifth**: Run `python back/scripts/validate_production.py` to test validator
6. **Sixth**: Create a user and test the API endpoints
7. **Seventh**: Review audit logs: `docker-compose logs backend | grep audit`

All environment variables come from `.env` (which is git-ignored for security).
Never commit `.env` or hardcoded secrets.
Always use `settings.VARIABLE_NAME` instead of `os.getenv()`.
Production validation must pass before deployment.

---

**Last Updated**: May 9, 2026  
**Maintained By**: GitHub Copilot  
**Status**: Production-Ready (Phase 1.5 Complete)
