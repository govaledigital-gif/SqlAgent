from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from app.config.settings import settings


def create_database_engine():
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL must be configured")

    return create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
    )


def create_session_factory(engine, *, expire_on_commit: bool = False):
    return sessionmaker(bind=engine, expire_on_commit=expire_on_commit)