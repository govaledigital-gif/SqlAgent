from typing import List, Optional
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from app.domain.interfaces import SchemaRepositoryInterface
import os

class SchemaRepository(SchemaRepositoryInterface):
    """Repository for MySQL database schema"""
    
    def __init__(self):
        database_url = os.getenv("DATABASE_URL", "mysql+pymysql://root:root@localhost/projects_db")
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    async def get_schema(self) -> str:
        """Get complete database schema"""
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
        
        return schema_info
    
    async def get_table_schema(self, table_name: str) -> str:
        """Get specific table schema"""
        inspector = inspect(self.engine)
        
        if table_name not in inspector.get_table_names():
            return f"Table '{table_name}' not found"
        
        columns = inspector.get_columns(table_name)
        schema_info = f"Table: {table_name}\n"
        
        for col in columns:
            col_type = str(col['type'])
            nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
            schema_info += f"  - {col['name']}: {col_type} {nullable}\n"
        
        return schema_info
    
    async def list_tables(self) -> List[str]:
        """List all available tables"""
        inspector = inspect(self.engine)
        return inspector.get_table_names()
    
    async def execute_query(self, query: str):
        """Execute a SQL query and return results"""
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            return result.fetchall()
