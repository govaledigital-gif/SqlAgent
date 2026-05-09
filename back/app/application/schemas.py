from pydantic import BaseModel
from typing import Optional

class GenerateSqlRequest(BaseModel):
    """Request model for SQL generation"""
    prompt: str
    schema: Optional[str] = None
    table_name: Optional[str] = None

class GenerateSqlResponse(BaseModel):
    """Response model for SQL generation"""
    query: str
    explanation: Optional[str] = None
    error: Optional[str] = None

class SchemaResponse(BaseModel):
    """Response model for schema"""
    tables: list[str]
    schema: str
