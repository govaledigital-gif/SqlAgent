# SQL Architect - Security Architecture

## Overview

SQL Architect implements a comprehensive, defense-in-depth security architecture with zero tolerance for hardcoded credentials, configuration drift, or security vulnerabilities.

## Security Layers

### 1. Configuration Management (Centralized & Validated)

**Location:** `app/config/settings.py`

✓ All environment variables centralized in single BaseSettings class
✓ No hardcoded values except development-only defaults (never used in production)
✓ Production validation enforces security requirements at startup
✓ Type-safe configuration with pydantic validation

**Production Validation Checks:**
- JWT_SECRET ≥ 32 characters
- DATABASE_URL configured for remote database
- GOOGLE_API_KEY present and valid
- CORS_ORIGINS explicitly set (no localhost fallback)
- FORCE_HTTPS=true
- API_RELOAD=false
- Proper log levels

**Implementation:**
```python
# Settings never exposed in logs
# Connection strings never logged
# Secrets masked in all outputs
```

### 2. Authentication & Authorization

**JWT Implementation:** `app/application/auth_service.py`

✓ HS256 algorithm with strong secrets
✓ 24-hour token expiration (configurable)
✓ Token type validation (only "access" tokens accepted)
✓ Password hashing with bcrypt (automatic salt)
✓ Configurable password strength requirements

**Password Requirements (Configurable):**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 number
- At least 1 special character

**Token Claims:**
```json
{
  "sub": "user@example.com",
  "exp": 1234567890,
  "iat": 1234567890,
  "type": "access"
}
```

**Protected Endpoints:** All non-auth endpoints require valid JWT via HTTPBearer

### 3. SQL Security (Input Validation)

**Location:** `app/application/sql_validator.py`

✓ Command whitelist enforcement (only SELECT allowed)
✓ Dangerous command blocking (DROP, DELETE, INSERT, UPDATE, ALTER, etc.)
✓ SQL injection prevention via sqlparse analysis
✓ Comment removal and whitespace normalization
✓ Query length limits (5000 characters default)

**Dangerous Commands Blocked:**
- DROP, DELETE, TRUNCATE
- ALTER, CREATE
- INSERT, UPDATE
- GRANT, REVOKE
- EXEC, EXECUTE

### 4. Logging & Audit Trail

**Location:** `app/infrastructure/security_logger.py` & `app/infrastructure/audit_middleware.py`

✓ Structured JSON logging
✓ Automatic sensitive data masking
  - Passwords
  - API keys
  - Tokens
  - Email addresses (optional)
  - Credit cards
  - SSN

✓ Audit logging for critical operations:
  - User registration
  - User login
  - SQL generation
  - Query history access
  - Resource deletions

**Audit Log Example:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "operation": "USER_LOGIN",
  "user": "user@example.com",
  "method": "POST",
  "path": "/api/v1/auth/login",
  "status_code": 200,
  "duration_ms": 250,
  "client_ip": "192.168.1.100"
}
```

### 5. HTTP Security Headers

**Location:** `app/infrastructure/audit_middleware.py`

✓ X-Content-Type-Options: nosniff
✓ X-Frame-Options: DENY
✓ X-XSS-Protection: 1; mode=block
✓ Strict-Transport-Security: max-age=31536000
✓ Content-Security-Policy: default-src 'self'
✓ Referrer-Policy: strict-origin-when-cross-origin
✓ Permissions-Policy: geolocation=(), microphone=(), camera=()
✓ Server header removed

### 6. CORS Configuration

**Location:** `main.py`

✓ Whitelist-based origin validation
✓ Credentials allowed only for same-origin
✓ Explicit method restrictions (GET, POST only)
✓ Explicit header restrictions (Content-Type, Authorization)
✓ TrustedHostMiddleware for additional validation

**Development vs Production:**
- Development: localhost:3000 (for local testing)
- Production: Must be explicitly configured

### 7. Rate Limiting

**Library:** slowapi

✓ Per-IP rate limiting
✓ 100 requests per 60 seconds (configurable)
✓ Graceful degradation with 429 responses

### 8. Database Security

**Connection:**
✓ Connection pooling with health checks
✓ Database URL from environment (never hardcoded)
✓ SQLAlchemy with parameterized queries (automatic SQL injection prevention)
✓ Pool pre-ping to verify connections

**Data Ownership:**
✓ Every query tied to user email via foreign key
✓ User ownership validation on history access/deletion
✓ No cross-user data leakage possible

**Schema Protection:**
✓ Read-only schema introspection
✓ No DDL operations allowed
✓ Table name validation before queries

### 9. Cache Security

**Location:** `app/infrastructure/cache_service.py`

✓ Redis password support
✓ Optional Redis disabling (graceful fallback to DB)
✓ Configurable TTL (1 hour default for schema cache)
✓ Cache key pattern isolation (schema:*, schema:table:*)
✓ Connection timeout protection

### 10. Error Handling

**Location:** `main.py`

✓ Generic error messages in production
✓ Detailed errors only in development
✓ No stack traces exposed to clients
✓ Request ID tracking for support

**Error Response (Production):**
```json
{
  "detail": "An internal error occurred. Please try again later."
}
```

### 11. Input Validation

**Pydantic Schemas:** `app/application/schemas.py`

✓ Type validation on all inputs
✓ Email format validation
✓ Length limits on prompts (2000 chars)
✓ Length limits on queries (5000 chars)
✓ UTF-8 encoding enforcement

### 12. Production Validation Script

**Location:** `scripts/validate_production.py`

Run before production deployment:
```bash
python scripts/validate_production.py
```

Validates:
- Environment=production
- Database URL is remote
- JWT secret strength (32+ chars)
- API key configuration
- CORS origins explicit
- HTTPS enforcement
- Auto-reload disabled
- Log level appropriate
- No localhost in CORS

### 13. Automated Secret Scanning

**CI Controls:**

✓ Bandit runs in the main CI workflow for Python SAST
✓ pip-audit runs in the main CI workflow for dependency vulnerabilities
✓ Gitleaks runs in a dedicated security workflow for secret detection

**Security workflow cadence:**
- On pull requests
- On pushes to the default branch
- Weekly scheduled scan

If a secret is added by mistake, rotate it immediately and remove it from git history.

## Security Best Practices Implemented

### ✓ Defense in Depth
Multiple security layers (auth → validation → logging → rate limiting)

### ✓ Least Privilege
- Users can only see their own history
- API endpoints require authentication
- Read-only schema access
- No admin endpoints

### ✓ Secure Defaults
- Development defaults are safe (explicit production config required)
- HTTPS enforcement in production
- Auto-reload disabled in production
- Detailed logging only in development

### ✓ Input Validation
- Whitelist approach for SQL commands
- Pydantic schema validation
- Length limits on all inputs
- Type checking on all API parameters

### ✓ Secret Management
- No hardcoded secrets (environment variables only)
- Secrets masked in logs automatically
- JWT secrets never exposed
- API keys validated at startup

### ✓ Audit Trail
- All critical operations logged
- User actions tied to authentication
- Timestamps and client IPs recorded
- Structured logging for analysis

### ✓ Error Handling
- No sensitive data in error messages
- Stack traces hidden in production
- Proper HTTP status codes
- Request tracking for support

## Threat Model

### Mitigated Threats

1. **SQL Injection** → Parameterized queries + Command whitelist
2. **Authentication Bypass** → JWT validation + Token expiration
3. **Unauthorized Data Access** → User ownership checks + CORS validation
4. **Cross-Site Scripting (XSS)** → JSON API (no HTML) + Security headers
5. **Cross-Site Request Forgery (CSRF)** → SameSite cookies + CORS
6. **Brute Force** → Rate limiting + Exponential backoff (future)
7. **Configuration Drift** → Centralized BaseSettings + Production validation
8. **Credential Exposure** → Secret masking + No hardcoded values
9. **DDoS** → Rate limiting + Cloud WAF (future)
10. **Privilege Escalation** → Stateless JWT + User ownership checks

### Out of Scope (Require Infrastructure)

- SSL/TLS termination (Use reverse proxy: nginx, CloudFront)
- DDoS protection (Use cloud WAF: AWS WAF, Azure WAF)
- Intrusion detection (Use cloud monitoring: CloudWatch, Azure Monitor)
- Physical security (Handled by cloud provider)

## Deployment Checklist

### Before Production

- [ ] Run `python scripts/validate_production.py`
- [ ] Set `ENVIRONMENT=production`
- [ ] Generate strong JWT_SECRET: `openssl rand -hex 32`
- [ ] Configure DATABASE_URL to remote database
- [ ] Configure GOOGLE_API_KEY
- [ ] Set CORS_ORIGINS to your domain(s)
- [ ] Enable FORCE_HTTPS=true
- [ ] Set API_RELOAD=false
- [ ] Use production ASGI server (gunicorn/uvicorn daemon)
- [ ] Enable HTTPS/TLS at reverse proxy
- [ ] Configure log aggregation (CloudWatch, ELK, etc.)
- [ ] Review all environment variables
- [ ] Run secret scan workflow and rotate any leaked credentials

### After Deployment

- [ ] Verify HTTPS is enforced
- [ ] Test authentication flows
- [ ] Verify rate limiting works
- [ ] Check audit logs are generated
- [ ] Monitor error rates
- [ ] Review sensitive data masking in logs

## Configuration Examples

### Development Environment
```bash
ENVIRONMENT=development
DATABASE_URL=mysql+pymysql://root:root@localhost/projects_db
GOOGLE_API_KEY=your-test-key
JWT_SECRET=dev-secret-not-secure
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=DEBUG
```

### Staging Environment
```bash
ENVIRONMENT=staging
DATABASE_URL=mysql+pymysql://user:pass@staging-db.example.com/projects_db
GOOGLE_API_KEY=staging-api-key
JWT_SECRET=$(openssl rand -hex 32)
CORS_ORIGINS=https://staging.example.com
LOG_LEVEL=INFO
```

### Production Environment
```bash
ENVIRONMENT=production
DATABASE_URL=mysql+pymysql://user:pass@prod-db.example.com/projects_db
GOOGLE_API_KEY=prod-api-key
JWT_SECRET=$(openssl rand -hex 32)
CORS_ORIGINS=https://app.example.com,https://example.com
FORCE_HTTPS=true
API_RELOAD=false
LOG_LEVEL=WARNING
RATE_LIMIT_ENABLED=true
```

## Incident Response

### If JWT Secret is Compromised
1. Generate new JWT_SECRET: `openssl rand -hex 32`
2. Update ENVIRONMENT variable
3. Restart application
4. All existing tokens become invalid
5. Users must re-login

### If Database Credentials are Exposed
1. Rotate database password immediately
2. Update DATABASE_URL
3. Restart application
4. Review audit logs for access

### If Google API Key is Exposed
1. Revoke exposed key in Google Cloud Console
2. Generate new API key
3. Update GOOGLE_API_KEY
4. Restart application

## Compliance

- ✓ OWASP Top 10 mitigation
- ✓ NIST Cybersecurity Framework alignment
- ✓ No hardcoded credentials (PCI-DSS 6.5.10)
- ✓ Secure password hashing (NIST guidelines)
- ✓ Audit logging (SOC 2 requirement)
- ✓ Error handling (OWASP requirement)
- ✓ Input validation (CWE-20 mitigation)

## Future Enhancements

- [ ] Multi-factor authentication (MFA)
- [ ] OAuth2 integration for social login
- [ ] API key-based authentication alternative
- [ ] Encryption at rest (database)
- [ ] Encryption in transit (TLS everywhere)
- [ ] Field-level access control
- [ ] Data residency compliance
- [ ] SAML integration for enterprise
- [ ] Hardware security key support
- [ ] Quarterly security audits

## References

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [PCI-DSS Requirements](https://www.pcisecuritystandards.org/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
