"""
SynthLeak Database Configuration & Session Management.
Uses SQLAlchemy engine with SQLite for persistent, reliable storage.
Provides session dependencies and database lifecycle management.
"""

import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

# Database path resolution: environment variable or default to project data/ directory
DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "data" / "synthleak.db")
DB_PATH = os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)

# Ensure parent directory exists for SQLite database file
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

# Synchronous SQLite URL (reliable across platforms & Python 3.13)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv("LOG_LEVEL", "info").lower() == "debug",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base declarative class for all SynthLeak ORM models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
