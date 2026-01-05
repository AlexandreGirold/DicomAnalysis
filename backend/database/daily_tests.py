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
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    filenames = Column(Text, nullable=True)
    accelerator_warmup = Column(String, nullable=False)
    audio_indicator = Column(String, nullable=False)
    visual_indicators_console = Column(String, nullable=False)
    visual_indicator_room = Column(String, nullable=False)
    beam_interruption = Column(String, nullable=False)
    door_interlocks = Column(String, nullable=False)
    camera_monitoring = Column(String, nullable=False)
    patient_communication = Column(String, nullable=False)
    table_emergency_stop = Column(String, nullable=False)


class SafetySystemsResult(Base):
    __tablename__ = "daily_safety_systems_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('daily_safety_systems.id'), nullable=False)
