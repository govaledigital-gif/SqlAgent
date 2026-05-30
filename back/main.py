from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
from urllib.parse import urlparse

from app.application.controller import router as legacy_router
from app.application.inventory_controller import router as inventory_router
from app.application.ai_controller import router as ai_router
from app.config.settings import settings
from app.infrastructure.security_logger import setup_logging, SecurityLogger
from app.infrastructure.audit_middleware import AuditMiddleware, SecurityHeadersMiddleware
from app.infrastructure.observability import MetricsMiddleware, init_sentry, router as observability_router

# Setup logging first
setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
logger = SecurityLogger(__name__)
init_sentry()

# Create FastAPI app
app = FastAPI(
    title="Inventory Platform",
    description="Modular inventory platform with AI copilot",
    version="1.0.0",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    content={"detail": "Rate limit exceeded. Please try again later."}
))

# Security Middleware: Trusted Host
if settings.CORS_ORIGINS:
    allowed_hosts = sorted({
        parsed.hostname
        for parsed in (urlparse(origin) for origin in settings.CORS_ORIGINS)
        if parsed.hostname
    })
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )

# CORS Middleware - Restrictive configuration
cors_origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    max_age=settings.CORS_MAX_AGE,
)

# Security and Audit Middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(MetricsMiddleware)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler that masks sensitive information"""
    logger.error(f"Unhandled exception: {str(exc)}")
    
    # Never expose internal details in production
    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred. Please try again later."}
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)}
        )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors securely"""
    # Log detailed validation errors for debugging in development
    try:
        details = exc.errors()
    except Exception:
        details = str(exc)
    logger.warning(f"Validation error on {request.url.path}: {details}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request. Please check your input."}
    )

# Include routes
app.include_router(legacy_router)
app.include_router(inventory_router)
app.include_router(ai_router)
app.include_router(observability_router)

# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info(f"Starting Inventory Platform in {settings.ENVIRONMENT} mode")
    
    # Validate configuration
    if not settings.DATABASE_URL:
        logger.error("DATABASE_URL is not configured")
        raise RuntimeError("DATABASE_URL environment variable is required")
    
    if not settings.JWT_SECRET or len(settings.JWT_SECRET) < 16:
        logger.error("JWT_SECRET is not properly configured")
        raise RuntimeError("JWT_SECRET must be set and at least 16 characters")
    
    if settings.LLM_PROVIDER.lower() == "google" and not settings.GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY is not configured for Google LLM provider")
        raise RuntimeError("GOOGLE_API_KEY environment variable is required when LLM_PROVIDER=google")

    # Register inventory models before startup completes
    from app.domain import inventory  # noqa: F401
    
    # Production-specific validations
    if settings.ENVIRONMENT == "production":
        try:
            settings.validate_production()
            logger.info("Production security validations passed")
        except ValueError as e:
            logger.error(f"Production validation failed: {str(e)}")
            raise RuntimeError(str(e))
    
    logger.info("All critical configurations validated")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Inventory Platform")

if __name__ == "__main__":
    import uvicorn
    
    # Only for development - use proper WSGI server in production
    if settings.ENVIRONMENT != "production":
        uvicorn.run(
            "main:app",
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=settings.API_RELOAD,
            log_level=settings.LOG_LEVEL.lower()
        )
    else:
        logger.error("Use a production ASGI server (e.g., gunicorn, uvicorn daemon)")
        raise RuntimeError("main.py should not be run directly in production")
