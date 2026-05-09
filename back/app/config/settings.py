from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """
    Central configuration management.
    All values must come from environment variables or .env file.
    No hardcoded values except sensible defaults for development.
    """
    
    # ============ DATABASE ============
    DATABASE_URL: str = ""  # Required - mysql+pymysql://user:pass@host/db
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # ============ REDIS ============
    REDIS_HOST: str = "localhost"  # Change to "redis" in docker
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_ENABLED: bool = True
    
    # ============ API ============
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = False  # Never True in production
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # ============ SECURITY ============
    JWT_SECRET: str = ""  # Required - must be strong and unique
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    JWT_REFRESH_EXPIRATION_DAYS: int = 7
    
    # Password requirements
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100  # requests
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # CORS
    CORS_ORIGINS: list[str] = []  # Must be set in production
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["GET", "POST"]
    CORS_ALLOW_HEADERS: list[str] = ["Content-Type", "Authorization"]
    CORS_MAX_AGE: int = 600
    
    # HTTPS/TLS
    FORCE_HTTPS: bool = True  # Enable in production
    SSL_CERTFILE: Optional[str] = None
    SSL_KEYFILE: Optional[str] = None
    
    # ============ AI/LLM ============
    GOOGLE_API_KEY: str = ""  # Required for Gemini
    LLM_TIMEOUT_SECONDS: int = 30
    LLM_MAX_RETRIES: int = 2
    
    # ============ LOGGING ============
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "json"  # json or text
    SENTRY_DSN: Optional[str] = None  # Optional error tracking
    
    # ============ FEATURES ============
    SCHEMA_CACHE_TTL: int = 3600  # 1 hour
    QUERY_HISTORY_RETENTION_DAYS: int = 90
    MAX_QUERY_LENGTH: int = 5000
    MAX_PROMPT_LENGTH: int = 2000
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def validate_production(self):
        """Validate that production settings are secure"""
        if self.ENVIRONMENT == "production":
            errors = []
            
            if not self.JWT_SECRET or len(self.JWT_SECRET) < 32:
                errors.append("JWT_SECRET must be set and at least 32 characters in production")
            
            if not self.GOOGLE_API_KEY:
                errors.append("GOOGLE_API_KEY is required in production")
            
            if not self.DATABASE_URL:
                errors.append("DATABASE_URL is required")
            
            if not self.CORS_ORIGINS:
                errors.append("CORS_ORIGINS must be explicitly set in production")
            
            if not self.FORCE_HTTPS:
                errors.append("FORCE_HTTPS should be True in production")
            
            if self.API_RELOAD:
                errors.append("API_RELOAD must be False in production")
            
            if errors:
                raise ValueError("Production security checks failed:\n" + "\n".join(errors))

# Global settings instance
settings = Settings()

# Validate on startup
if settings.ENVIRONMENT == "production":
    settings.validate_production()
