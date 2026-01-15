"""
Database Configuration
Core SQLAlchemy setup and connection management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Database path configuration
DB_PATH = Path(__file__).parent.parent / "data" / "qc_tests.db"
DB_PATH.parent.mkdir(exist_ok=True)

# SQLAlchemy setup
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, echo=False)

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database: creates all tables if they don't exist.
    Safe to call multiple times - only creates missing tables.
    """
    Base.metadata.create_all(bind=engine)
