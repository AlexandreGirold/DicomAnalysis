"""
Daily QC Test Models
Database models for daily quality control tests
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from datetime import datetime, timezone
from .config import Base


class SafetySystemsTest(Base):
    """Daily Safety Systems Test"""
    __tablename__ = "daily_safety_systems"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)  # PASS/FAIL/WARNING
    notes = Column(Text, nullable=True)


class SafetySystemsResult(Base):
    """Results table for Safety Systems Test"""
    __tablename__ = "daily_safety_systems_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('daily_safety_systems.id'), nullable=False)
