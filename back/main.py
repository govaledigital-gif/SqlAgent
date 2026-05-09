from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

from app.application.controller import router
from app.config.settings import settings
from app.infrastructure.security_logger import setup_logging, SecurityLogger
from app.infrastructure.audit_middleware import AuditMiddleware, SecurityHeadersMiddleware

# Setup logging first
setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
logger = SecurityLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SQL Architect - The Data Agent",
    description="AI-powered SQL query translator from natural language",
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
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.CORS_ORIGINS
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
    logger.warning(f"Validation error on {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request. Please check your input."}
    )

# Include routes
app.include_router(router)

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
    logger.info(f"Starting SQL Architect in {settings.ENVIRONMENT} mode")
    
    # Validate configuration
    if not settings.DATABASE_URL:
        logger.error("DATABASE_URL is not configured")
        raise RuntimeError("DATABASE_URL environment variable is required")
    
    if not settings.JWT_SECRET or len(settings.JWT_SECRET) < 16:
        logger.error("JWT_SECRET is not properly configured")
        raise RuntimeError("JWT_SECRET must be set and at least 16 characters")
    
    if not settings.GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY is not configured")
        raise RuntimeError("GOOGLE_API_KEY environment variable is required")
    
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
    logger.info("Shutting down SQL Architect")

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
