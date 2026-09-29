"""Database engine, session factory, and FastAPI dependency."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.backend.config import settings

# Configure SQLite vs PostgreSQL connection arguments
connect_args = {}
engine_kwargs = {
    "echo": settings.DB_ECHO,
    "pool_pre_ping": True,
}

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    engine_kwargs["connect_args"] = connect_args
else:
    # PostgreSQL / Serverless pool management
    engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    engine_kwargs["pool_recycle"] = 300
    engine_kwargs["connect_args"] = connect_args

engine = create_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session with guaranteed closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
