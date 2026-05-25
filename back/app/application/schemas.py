from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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

class LoginRequest(BaseModel):
    """Request model for user login"""
    email: str
    password: str

class RegisterRequest(BaseModel):
    """Request model for user registration"""
    email: str
    password: str
    full_name: Optional[str] = ""
    invite_token: Optional[str] = None

class TokenResponse(BaseModel):
    """Response model for token"""
    access_token: str
    token_type: str = "bearer"
    email: str

class UserResponse(BaseModel):
    """Response model for user"""
    email: str
    full_name: Optional[str] = None
    is_active: bool

class QueryHistoryResponse(BaseModel):
    """Response model for query history"""
    id: str
    user_email: str
    prompt: str
    generated_sql: Optional[str] = None
    is_valid: bool
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class QueryHistoryListResponse(BaseModel):
    """Response model for query history list"""
    total: int
    queries: list[QueryHistoryResponse]
