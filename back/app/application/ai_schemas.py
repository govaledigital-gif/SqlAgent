from pydantic import BaseModel, Field
from typing import Optional


class SQLOptimizeRequest(BaseModel):
    company_id: str
    sql: str = Field(min_length=1)


class SQLOptimizeResponse(BaseModel):
    original: str
    suggested_sql: str
    explanation: Optional[str] = None


class NLQueryRequest(BaseModel):
    company_id: str
    question: str = Field(min_length=1)


class NLQueryResponse(BaseModel):
    sql: str
    explanation: Optional[str] = None
    confidence: Optional[float] = None
    results: Optional[list[dict]] = None
