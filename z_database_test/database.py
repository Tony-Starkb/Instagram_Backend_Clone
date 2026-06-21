"""Example database.py for a production-style SQLAlchemy setup.

This file is a clean template for the standard separation:
- models.py  -> ORM table classes
- schemas.py -> Pydantic validation models
- database.py -> engine, session, Base, get_db()
- db_handler.py -> CRUD / service logic

Use this as the base for your real PostgreSQL integration.
"""

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/instacore",
)

# Production-friendly engine settings.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for getting a SQLAlchemy session.

    Use this in routers like:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all tables for development/testing.

    For production, prefer Alembic migrations instead of this.
    """
    Base.metadata.create_all(bind=engine)


def drop_tables() -> None:
    """Drop all tables (use only in development/testing)."""
    Base.metadata.drop_all(bind=engine)


def check_connection() -> bool:
    """Simple health check for the database connection."""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except SQLAlchemyError:
        return False
