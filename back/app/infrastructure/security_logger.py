import logging
import json
from datetime import datetime
from typing import Any, Optional
import re

class SecurityLogger:
    """Secure logging that masks sensitive data"""
    
    # Patrones de datos sensibles a enmascarar
    SENSITIVE_PATTERNS = {
        'password': r'(password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^"\'}\s]+)',
        'api_key': r'(api[_-]?key|apikey|token)["\']?\s*[:=]\s*["\']?([^"\'}\s]+)',
        'jwt': r'(jwt|authorization|bearer)["\']?\s*[:=]\s*([A-Za-z0-9\-_.]+)',
        'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b'
    }
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    @staticmethod
    def mask_sensitive_data(text: str) -> str:
        """Mask sensitive data in logs"""
        if not isinstance(text, str):
            return str(text)
        
        masked = text
        for pattern_type, pattern in SecurityLogger.SENSITIVE_PATTERNS.items():
            # Reemplazar valores sensibles con masks
            masked = re.sub(
                pattern,
                lambda m: f"{m.group(1)}='***MASKED***'" if len(m.groups()) > 1 else '***MASKED***',
                masked,
                flags=re.IGNORECASE
            )
        
        return masked
    
    def info(self, message: str, **kwargs):
        """Log info with masked sensitive data"""
        clean_message = self.mask_sensitive_data(message)
        clean_kwargs = {k: self.mask_sensitive_data(str(v)) for k, v in kwargs.items()}
        self.logger.info(clean_message, extra=clean_kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning with masked sensitive data"""
        clean_message = self.mask_sensitive_data(message)
        clean_kwargs = {k: self.mask_sensitive_data(str(v)) for k, v in kwargs.items()}
        self.logger.warning(clean_message, extra=clean_kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error with masked sensitive data"""
        clean_message = self.mask_sensitive_data(message)
        clean_kwargs = {k: self.mask_sensitive_data(str(v)) for k, v in kwargs.items()}
        self.logger.error(clean_message, extra=clean_kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug with masked sensitive data"""
        clean_message = self.mask_sensitive_data(message)
        clean_kwargs = {k: self.mask_sensitive_data(str(v)) for k, v in kwargs.items()}
        self.logger.debug(clean_message, extra=clean_kwargs)

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": SecurityLogger.mask_sensitive_data(record.getMessage()),
        }
        
        if record.exc_info:
            log_data["error"] = self.formatException(record.exc_info)
        
        # Add any extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data)

def setup_logging(log_level: str = "INFO", log_format: str = "json"):
    """Setup application logging"""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
