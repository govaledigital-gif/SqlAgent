from typing import List, Optional
from sqlalchemy import inspect, text
from app.domain.interfaces import SchemaRepositoryInterface
from app.infrastructure.cache_service import CacheService
from app.config.settings import settings
from app.infrastructure.database import create_database_engine, create_session_factory
from app.infrastructure.security_logger import SecurityLogger
import json

logger = SecurityLogger(__name__)

class SchemaRepository(SchemaRepositoryInterface):
    """Repository for database schema with caching"""
    
    def __init__(self):
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL must be configured")
        
        self.engine = create_database_engine()
        self.SessionLocal = create_session_factory(self.engine)
        self.cache = CacheService()
    
    async def get_schema(self) -> str:
        """Get complete database schema with caching"""
        cache_key = "schema:full"
        
        # Intentar obtener del caché
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            # Si no está en caché, obtener de la BD
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            schema_info = "Database Schema:\n"
            for table in tables:
                columns = inspector.get_columns(table)
                schema_info += f"\nTable: {table}\n"
                for col in columns:
                    col_type = str(col['type'])
                    nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
                    schema_info += f"  - {col['name']}: {col_type} {nullable}\n"
            
            # Guardar en caché
            self.cache.set(cache_key, schema_info, settings.SCHEMA_CACHE_TTL)
            return schema_info
        except Exception as e:
            logger.error(f"Error getting schema: {str(e)}")
            raise
    
    async def get_table_schema(self, table_name: str) -> str:
        """Get specific table schema with caching"""
        cache_key = f"schema:table:{table_name}"
        
        # Validar nombre de tabla para prevenir inyección
        if not self._is_valid_identifier(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        
        # Intentar obtener del caché
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            inspector = inspect(self.engine)
            
            if table_name not in inspector.get_table_names():
                return f"Table '{table_name}' not found"
            
            columns = inspector.get_columns(table_name)
            schema_info = f"Table: {table_name}\n"
            
            for col in columns:
                col_type = str(col['type'])
                nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
                schema_info += f"  - {col['name']}: {col_type} {nullable}\n"
            
            # Guardar en caché
            self.cache.set(cache_key, schema_info, settings.SCHEMA_CACHE_TTL)
            return schema_info
        except Exception as e:
            logger.error(f"Error getting table schema: {str(e)}")
            raise
    
    async def list_tables(self) -> List[str]:
        """List all available tables with caching"""
        cache_key = "schema:tables"
        
        # Intentar obtener del caché
        cached = self.cache.get(cache_key)
        if cached:
            return json.loads(cached)
        
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            # Guardar en caché
            self.cache.set(cache_key, json.dumps(tables), settings.SCHEMA_CACHE_TTL)
            return tables
        except Exception as e:
            logger.error(f"Error listing tables: {str(e)}")
            raise
    
    async def execute_query(self, query: str):
        """Execute a SQL query and return results"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                return result.fetchall()
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
    
    def invalidate_schema_cache(self):
        """Invalidate all schema caches when schema changes"""
        self.cache.clear_pattern("schema:*")
    
    @staticmethod
    def _is_valid_identifier(name: str) -> bool:
        """Check if a string is a valid SQL identifier"""
        import re
        # Allow alphanumeric, underscore, and letters from other languages
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name))
