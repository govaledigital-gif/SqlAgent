from abc import ABC, abstractmethod
from typing import Optional, List

class SqlGeneratorInterface(ABC):
    """Interface for SQL Generation"""
    
    @abstractmethod
    async def generate(self, prompt: str, schema: Optional[str] = None) -> str:
        """
        Generate SQL query from natural language
        
        Args:
            prompt: Natural language description of the query
            schema: Database schema information (optional)
            
        Returns:
            Generated SQL query string
        """
        pass

class SchemaRepositoryInterface(ABC):
    """Interface for Schema Repository"""
    
    @abstractmethod
    async def get_schema(self) -> str:
        """Get database schema"""
        pass
    
    @abstractmethod
    async def get_table_schema(self, table_name: str) -> str:
        """Get specific table schema"""
        pass
    
    @abstractmethod
    async def list_tables(self) -> List[str]:
        """List all available tables"""
        pass
