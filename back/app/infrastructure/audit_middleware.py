from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
from app.infrastructure.security_logger import SecurityLogger

logger = SecurityLogger(__name__)

class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for auditing critical operations"""
    
    # Endpoints that require audit logging
    AUDIT_PATHS = {
        "/api/v1/auth/register": "USER_REGISTRATION",
        "/api/v1/auth/login": "USER_LOGIN",
        "/api/v1/generate-sql": "SQL_GENERATION",
        "/api/v1/history/": "HISTORY_ACCESS",
    }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        
        # Get user from JWT if available
        user = "anonymous"
        try:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                from app.application.auth_service import AuthService
                token = auth_header[7:]
                email = AuthService.verify_token(token)
                if email:
                    user = email
        except:
            pass
        
        # Process request
        response = await call_next(request)
        
        # Log audit event if applicable
        duration = time.time() - start_time
        self._log_audit_event(request, response, user, duration)
        
        return response
    
    def _log_audit_event(self, request: Request, response: Response, user: str, duration: float):
        """Log audit events for critical operations"""
        path = request.url.path
        method = request.method
        
        # Check if this is a sensitive endpoint
        should_audit = False
        operation = None
        
        for audit_path, op_name in self.AUDIT_PATHS.items():
            if path.startswith(audit_path):
                should_audit = True
                operation = op_name
                break
        
        if should_audit:
            status_code = response.status_code
            
            audit_log = {
                "timestamp": time.time(),
                "operation": operation,
                "user": user,
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": int(duration * 1000),
                "client_ip": request.client.host if request.client else "unknown"
            }
            
            if status_code >= 400:
                logger.warning(f"Audit: {operation} failed", **audit_log)
            else:
                logger.info(f"Audit: {operation} succeeded", **audit_log)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Remove server identification
        try:
            del response.headers["Server"]
        except KeyError:
            pass
        
        return response
