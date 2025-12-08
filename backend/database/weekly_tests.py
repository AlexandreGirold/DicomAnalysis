"""
Weekly QC Test Models
Database models for weekly quality control tests
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from datetime import datetime, timezone
from .config import Base


class NiveauHeliumTest(Base):
    """Weekly Niveau d'Hélium Test"""
    __tablename__ = "weekly_niveau_helium"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)


class NiveauHeliumResult(Base):
    """Results table for Niveau d'Hélium Test"""
    __tablename__ = "weekly_niveau_helium_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('weekly_niveau_helium.id'), nullable=False)
    helium_level = Column(Float, nullable=False)


class MLCLeafJawTest(Base):
    """Weekly MLC Leaf and Jaw Test"""
    __tablename__ = "weekly_mlc_leaf_jaw"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)


class MVICTest(Base):
    """Weekly MVIC (MV Imaging Check) Test"""
    __tablename__ = "weekly_mvic"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)


class MVICResult(Base):
    """Results table for MVIC Test"""
    __tablename__ = "weekly_mvic_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('weekly_mvic.id'), nullable=False)
    image_number = Column(Integer, nullable=False)
    top_left_angle = Column(Float, nullable=False)
    top_right_angle = Column(Float, nullable=False)
    bottom_left_angle = Column(Float, nullable=False)
    bottom_right_angle = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    width = Column(Float, nullable=False)


class PIQTTest(Base):
    """Weekly PIQT (Philips Image Quality Test)"""
    __tablename__ = "weekly_piqt"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)


class PIQTResult(Base):
    """Results table for PIQT Test"""
    __tablename__ = "weekly_piqt_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('weekly_piqt.id'), nullable=False)

    # FFU1 NEMA measurements
    ffu1_nema_sn_b1 = Column(Float, nullable=True)
    ffu1_nema_sn_b2 = Column(Float, nullable=True)
    ffu1_nema_sn_b3 = Column(Float, nullable=True)
    ffu1_nema_int_unif1 = Column(Float, nullable=True)
    ffu1_nema_int_unif2 = Column(Float, nullable=True)
    ffu1_nema_int_unif3 = Column(Float, nullable=True)
    
    # FFU2 NEMA measurements
    ffu2_nema_sn_b1 = Column(Float, nullable=True)
    ffu2_nema_sn_b2 = Column(Float, nullable=True)
    ffu2_nema_sn_b3 = Column(Float, nullable=True)
    ffu2_nema_int_unif1 = Column(Float, nullable=True)
    ffu2_nema_int_unif2 = Column(Float, nullable=True)
    ffu2_nema_int_unif3 = Column(Float, nullable=True)
    
    # Spatial measurements
    spatial_linearity_nema_perc_dif1 = Column(Float, nullable=True)
    
    # Slice profile measurements
    slice_profile_nema_fwhm1 = Column(Float, nullable=True)
    slice_profile_nema_fwhm2 = Column(Float, nullable=True)
    slice_profile_nema_fwhm3 = Column(Float, nullable=True)
    slice_profile_nema_slice_int1 = Column(Float, nullable=True)
    slice_profile_nema_slice_int2 = Column(Float, nullable=True)
    slice_profile_nema_slice_int3 = Column(Float, nullable=True)
    
    # Spatial resolution measurements
    spatial_resolution_nema_hor_pxl_size1 = Column(Float, nullable=True)
    spatial_resolution_nema_hor_pxl_size2 = Column(Float, nullable=True)
    spatial_resolution_nema_ver_pxl_size1 = Column(Float, nullable=True)
    spatial_resolution_nema_ver_pxl_size2 = Column(Float, nullable=True)
