from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class QueryHistory(Base):
    """Query history model"""
    __tablename__ = "query_history"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID
    user_email = Column(String(255), ForeignKey("users.email"), nullable=False, index=True)
    prompt = Column(Text, nullable=False)  # Input natural language
    generated_sql = Column(Text, nullable=True)  # Generated SQL
    is_valid = Column(Boolean, default=False)  # Whether SQL is valid
    error_message = Column(Text, nullable=True)  # Error if generation failed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<QueryHistory {self.id} for {self.user_email}>"
