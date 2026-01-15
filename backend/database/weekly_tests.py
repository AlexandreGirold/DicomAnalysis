"""
Weekly QC Test Models
Database models for weekly quality control tests
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .config import Base


class NiveauHeliumTest(Base):
    """Weekly Niveau d'Hélium Test"""
    __tablename__ = "weekly_niveau_helium"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    helium_level = Column(Float, nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    filenames = Column(Text, nullable=True)


class NiveauHeliumResult(Base):
    __tablename__ = "weekly_niveau_helium_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('weekly_niveau_helium.id'), nullable=False)
    helium_level = Column(Float, nullable=False)


class MLCLeafJawTest(Base):
    __tablename__ = "weekly_mlc_leaf_jaw"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    filenames = Column(Text, nullable=True)
    visualization_paths = Column(Text, nullable=True)
    center_u = Column(Float, nullable=True)
    center_v = Column(Float, nullable=True)
    jaw_x1_mm = Column(Float, nullable=True)
    jaw_x2_mm = Column(Float, nullable=True)
    blade_top_average = Column(Float, nullable=True)
    blade_top_std_dev = Column(Float, nullable=True)
    blade_bottom_average = Column(Float, nullable=True)
    blade_bottom_std_dev = Column(Float, nullable=True)
    blade_average_angle = Column(Float, nullable=True)


class MVICTest(Base):
    __tablename__ = "weekly_mvic"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    filenames = Column(Text, nullable=True)
    visualization_paths = Column(Text, nullable=True)
    file_results = Column(Text, nullable=True)
    image1_width_mm = Column(Float, nullable=True)
    image1_height_mm = Column(Float, nullable=True)
    image1_avg_angle = Column(Float, nullable=True)
    image1_angle_std_dev = Column(Float, nullable=True)
    image2_width_mm = Column(Float, nullable=True)
    image2_height_mm = Column(Float, nullable=True)
    image2_avg_angle = Column(Float, nullable=True)
    image2_angle_std_dev = Column(Float, nullable=True)
    image3_width_mm = Column(Float, nullable=True)
    image3_height_mm = Column(Float, nullable=True)
    image3_avg_angle = Column(Float, nullable=True)
    image3_angle_std_dev = Column(Float, nullable=True)
    image4_width_mm = Column(Float, nullable=True)
    image4_height_mm = Column(Float, nullable=True)
    image4_avg_angle = Column(Float, nullable=True)
    image4_angle_std_dev = Column(Float, nullable=True)
    image5_width_mm = Column(Float, nullable=True)
    image5_height_mm = Column(Float, nullable=True)
    image5_avg_angle = Column(Float, nullable=True)
    image5_angle_std_dev = Column(Float, nullable=True)


class MVICResult(Base):
    __tablename__ = "weekly_mvic_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('weekly_mvic.id'), nullable=False)
    image_number = Column(Integer, nullable=False)
    filename = Column(String, nullable=True)
    top_left_angle = Column(Float, nullable=False)
    top_right_angle = Column(Float, nullable=False)
    bottom_left_angle = Column(Float, nullable=False)
    bottom_right_angle = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    width = Column(Float, nullable=False)


class MVICFenteV2Test(Base):
    __tablename__ = "weekly_mvic_fente_v2"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    filenames = Column(Text, nullable=True)
    visualization_paths = Column(Text, nullable=True)
    file_results = Column(Text, nullable=True)


class MVICFenteV2Result(Base):
    __tablename__ = "weekly_mvic_fente_v2_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('weekly_mvic_fente_v2.id'), nullable=False)
    image_number = Column(Integer, nullable=False)
    filename = Column(String, nullable=True)
    slit_number = Column(Integer, nullable=False)
    width_mm = Column(Float, nullable=False)
    height_pixels = Column(Float, nullable=False)
    center_u = Column(Float, nullable=True)
    center_v = Column(Float, nullable=True)


class PIQTTest(Base):
    __tablename__ = "weekly_piqt"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    filenames = Column(Text, nullable=True)
    snr_value = Column(Float, nullable=True)
    uniformity_value = Column(Float, nullable=True)
    ghosting_value = Column(Float, nullable=True)
    results_json = Column(Text, nullable=True)


class PIQTResult(Base):
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


class LeafPositionTest(Base):
    __tablename__ = "weekly_leaf_position"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    filenames = Column(Text, nullable=True)
    visualization_paths = Column(Text, nullable=True)
    file_results = Column(Text, nullable=True)
    
    blade_results = relationship("LeafPositionResult", backref="test", lazy="joined")
    images = relationship("LeafPositionImage", back_populates="test", lazy="joined")


class LeafPositionResult(Base):
    __tablename__ = "weekly_leaf_position_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('weekly_leaf_position.id'), nullable=False)
    image_number = Column(Integer, nullable=False)
    filename = Column(String, nullable=True)
    blade_pair = Column(Integer, nullable=False)
    position_u_px = Column(Float, nullable=True)
    v_sup_px = Column(Float, nullable=True)
    v_inf_px = Column(Float, nullable=True)
    distance_sup_mm = Column(Float, nullable=True)
    distance_inf_mm = Column(Float, nullable=True)
    length_mm = Column(Float, nullable=True)
    field_size_mm = Column(Float, nullable=True)
    is_valid = Column(String, nullable=False)
    status_message = Column(Text, nullable=True)
    blade_top_average = Column(Float, nullable=True)
    blade_bottom_average = Column(Float, nullable=True)
    blade_top_average = Column(Float, nullable=True)
    blade_bottom_average = Column(Float, nullable=True)
