from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.domain.query_history import QueryHistory, Base
from app.config.settings import settings
from app.infrastructure.security_logger import SecurityLogger
from typing import List, Optional
from uuid import uuid4

logger = SecurityLogger(__name__)

class QueryHistoryRepository:
    """Repository for query history persistence"""
    
    def __init__(self):
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL must be configured")
        
        self.engine = create_engine(
            settings.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
        # Crear tabla si no existe
        Base.metadata.create_all(bind=self.engine)
    
    def save_query(self, user_email: str, prompt: str, generated_sql: str = None, 
                   is_valid: bool = False, error_message: str = None) -> QueryHistory:
        """Save a query to history"""
        session = self.SessionLocal()
        try:
            # Validar tamaños
            if len(prompt) > settings.MAX_PROMPT_LENGTH:
                raise ValueError(f"Prompt exceeds maximum length of {settings.MAX_PROMPT_LENGTH}")
            
            if generated_sql and len(generated_sql) > settings.MAX_QUERY_LENGTH:
                raise ValueError(f"Query exceeds maximum length of {settings.MAX_QUERY_LENGTH}")
            
            query_id = str(uuid4())
            history = QueryHistory(
                id=query_id,
                user_email=user_email,
                prompt=prompt,
                generated_sql=generated_sql,
                is_valid=is_valid,
                error_message=error_message
            )
            session.add(history)
            session.commit()
            session.refresh(history)
            logger.info(f"Query saved: {query_id} for user {user_email}")
            return history
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error saving query: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_user_history(self, user_email: str, limit: int = 100) -> list:
        """Get query history for a user"""
        if limit > 1000:
            limit = 1000  # Prevent abuse
        
        session = self.SessionLocal()
        try:
            return session.query(QueryHistory)\
                .filter(QueryHistory.user_email == user_email)\
                .order_by(desc(QueryHistory.created_at))\
                .limit(limit)\
                .all()
        except Exception as e:
            logger.error(f"Error getting user history: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_query(self, query_id: str) -> QueryHistory:
        """Get a specific query from history"""
        session = self.SessionLocal()
        try:
            return session.query(QueryHistory).filter(QueryHistory.id == query_id).first()
        except Exception as e:
            logger.error(f"Error getting query: {str(e)}")
            raise
        finally:
            session.close()
    
    def delete_query(self, query_id: str) -> bool:
        """Delete a query from history"""
        session = self.SessionLocal()
        try:
            query = session.query(QueryHistory).filter(QueryHistory.id == query_id).first()
            if query:
                session.delete(query)
                session.commit()
                logger.info(f"Query deleted: {query_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting query: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()
