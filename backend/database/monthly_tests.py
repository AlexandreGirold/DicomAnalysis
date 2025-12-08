"""
Monthly QC Test Models
Database models for monthly quality control tests
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from datetime import datetime, timezone
from .config import Base


class PositionTableV2Test(Base):
    """Monthly Position Table V2 Test"""
    __tablename__ = "monthly_position_table_v2"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)


class PositionTableV2Result(Base):
    """Results table for Position Table V2 Test"""
    __tablename__ = "monthly_position_table_v2_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('monthly_position_table_v2.id'), nullable=False)


class AlignementLaserTest(Base):
    """Monthly Alignement Laser Test"""
    __tablename__ = "monthly_alignement_laser"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)


class AlignementLaserResult(Base):
    """Results table for Alignement Laser Test"""
    __tablename__ = "monthly_alignement_laser_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('monthly_alignement_laser.id'), nullable=False)


class QuasarTest(Base):
    """Monthly QUASAR Test"""
    __tablename__ = "monthly_quasar"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)


class QuasarResult(Base):
    """Results table for QUASAR Test"""
    __tablename__ = "monthly_quasar_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('monthly_quasar.id'), nullable=False)


class IndiceQualityTest(Base):
    """Monthly Indice de Qualité Test"""
    __tablename__ = "monthly_indice_quality"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)


class IndiceQualityResult(Base):
    """Results table for Indice de Qualité Test"""
    __tablename__ = "monthly_indice_quality_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('monthly_indice_quality.id'), nullable=False)
