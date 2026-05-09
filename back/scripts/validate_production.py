#!/usr/bin/env python3
"""
Production Configuration Validator
Run this script before deploying to production to ensure all security requirements are met.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.settings import settings
from app.infrastructure.security_logger import SecurityLogger

logger = SecurityLogger(__name__)

class ConfigValidator:
    """Validate production configuration"""
    
    REQUIREMENTS = [
        {
            "name": "Environment",
            "check": lambda: settings.ENVIRONMENT == "production",
            "error": "ENVIRONMENT must be set to 'production'"
        },
        {
            "name": "Database URL",
            "check": lambda: settings.DATABASE_URL and "localhost" not in settings.DATABASE_URL,
            "error": "DATABASE_URL must be set to a remote database (not localhost)"
        },
        {
            "name": "JWT Secret Strength",
            "check": lambda: len(settings.JWT_SECRET) >= 32,
            "error": "JWT_SECRET must be at least 32 characters (use: openssl rand -hex 32)"
        },
        {
            "name": "Google API Key",
            "check": lambda: settings.GOOGLE_API_KEY and len(settings.GOOGLE_API_KEY) > 20,
            "error": "GOOGLE_API_KEY must be configured and valid"
        },
        {
            "name": "CORS Origins",
            "check": lambda: settings.CORS_ORIGINS and len(settings.CORS_ORIGINS) > 0,
            "error": "CORS_ORIGINS must be explicitly set (not using localhost fallback)"
        },
        {
            "name": "HTTPS/TLS",
            "check": lambda: settings.FORCE_HTTPS == True,
            "error": "FORCE_HTTPS must be True in production"
        },
        {
            "name": "Auto Reload",
            "check": lambda: settings.API_RELOAD == False,
            "error": "API_RELOAD must be False in production"
        },
        {
            "name": "Logging Level",
            "check": lambda: settings.LOG_LEVEL in ["WARNING", "ERROR", "CRITICAL"],
            "error": "LOG_LEVEL should be WARNING or higher in production"
        },
        {
            "name": "No Localhost in CORS",
            "check": lambda: not any("localhost" in origin or "127.0.0.1" in origin 
                                     for origin in settings.CORS_ORIGINS),
            "error": "CORS_ORIGINS should not contain localhost in production"
        },
        {
            "name": "SSL Certificates (if custom)",
            "check": lambda: not settings.SSL_CERTFILE or os.path.exists(settings.SSL_CERTFILE),
            "error": "SSL_CERTFILE path does not exist"
        }
    ]
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Run all validation checks.
        Returns: (all_pass: bool, errors: list[str])
        """
        errors = []
        
        print("\n" + "="*60)
        print("PRODUCTION CONFIGURATION VALIDATOR")
        print("="*60 + "\n")
        
        for req in cls.REQUIREMENTS:
            try:
                if req["check"]():
                    print(f"✓ {req['name']}")
                else:
                    print(f"✗ {req['name']}")
                    errors.append(req["error"])
            except Exception as e:
                print(f"✗ {req['name']} (Exception: {str(e)})")
                errors.append(f"{req['name']}: {str(e)}")
        
        print("\n" + "="*60)
        
        if errors:
            print(f"FAILED: {len(errors)} requirement(s) not met\n")
            for i, error in enumerate(errors, 1):
                print(f"{i}. {error}")
            print("\n" + "="*60 + "\n")
            return False, errors
        else:
            print("SUCCESS: All production requirements met!\n")
            print("Configuration Summary:")
            print(f"  Environment: {settings.ENVIRONMENT}")
            print(f"  Database: {'✓ Configured' if settings.DATABASE_URL else '✗ Missing'}")
            print(f"  API Key: {'✓ Configured' if settings.GOOGLE_API_KEY else '✗ Missing'}")
            print(f"  CORS Origins: {', '.join(settings.CORS_ORIGINS)}")
            print(f"  HTTPS: {'✓ Enabled' if settings.FORCE_HTTPS else '✗ Disabled'}")
            print("\n" + "="*60 + "\n")
            return True, []

if __name__ == "__main__":
    success, errors = ConfigValidator.validate()
    sys.exit(0 if success else 1)
