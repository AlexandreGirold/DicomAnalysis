"""
Monthly QC Test Models
Database models for monthly quality control tests
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
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
    filenames = Column(Text, nullable=True)
    position_175 = Column(Float, nullable=False)
    position_215 = Column(Float, nullable=False)


class PositionTableV2Result(Base):
    __tablename__ = "monthly_position_table_v2_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('monthly_position_table_v2.id'), nullable=False)


class AlignementLaserTest(Base):
    __tablename__ = "monthly_alignement_laser"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    filenames = Column(Text, nullable=True)
    ecart_proximal = Column(Float, nullable=False)
    ecart_central = Column(Float, nullable=False)
    ecart_distal = Column(Float, nullable=False)


class AlignementLaserResult(Base):
    __tablename__ = "monthly_alignement_laser_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('monthly_alignement_laser.id'), nullable=False)


class QuasarTest(Base):
    __tablename__ = "monthly_quasar"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    filenames = Column(Text, nullable=True)
    latence_status = Column(String, nullable=False)
    latence_reason = Column(String, nullable=True)
    coord_correction = Column(Float, nullable=True)
    x_value = Column(Float, nullable=True)
    y_value = Column(Float, nullable=True)
    z_value = Column(Float, nullable=True)


class QuasarResult(Base):
    __tablename__ = "monthly_quasar_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('monthly_quasar.id'), nullable=False)


class IndiceQualityTest(Base):
    __tablename__ = "monthly_indice_quality"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    filenames = Column(Text, nullable=True)
    d5_m1 = Column(Float, nullable=True)
    d5_m2 = Column(Float, nullable=True)
    d5_m3 = Column(Float, nullable=True)
    d10_m1 = Column(Float, nullable=False)
    d10_m2 = Column(Float, nullable=False)
    d10_m3 = Column(Float, nullable=False)
    d15_m1 = Column(Float, nullable=True)
    d15_m2 = Column(Float, nullable=True)
    d15_m3 = Column(Float, nullable=True)
    d20_m1 = Column(Float, nullable=False)
    d20_m2 = Column(Float, nullable=False)
    d20_m3 = Column(Float, nullable=False)


class IndiceQualityResult(Base):
    __tablename__ = "monthly_indice_quality_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('monthly_indice_quality.id'), nullable=False)
