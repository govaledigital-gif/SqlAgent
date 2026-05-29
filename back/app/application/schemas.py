from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from pydantic import BaseModel
from typing import Optional
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


