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
    helium_level = Column(Float, nullable=False)  # Helium level stored directly in test table
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    filenames = Column(Text, nullable=True)


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
    filenames = Column(Text, nullable=True)
    visualization_paths = Column(Text, nullable=True)  # JSON array of visualization file paths
    # Test-specific data columns
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
    """Weekly MVIC (MV Imaging Check) Test - 5 Images"""
    __tablename__ = "weekly_mvic"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    filenames = Column(Text, nullable=True)  # Comma-separated list of filenames
    visualization_paths = Column(Text, nullable=True)  # JSON array of visualization file paths
    file_results = Column(Text, nullable=True)  # JSON string containing detailed measurement results
    # Image 1 measurements
    image1_width_mm = Column(Float, nullable=True)
    image1_height_mm = Column(Float, nullable=True)
    image1_avg_angle = Column(Float, nullable=True)
    image1_angle_std_dev = Column(Float, nullable=True)
    # Image 2 measurements
    image2_width_mm = Column(Float, nullable=True)
    image2_height_mm = Column(Float, nullable=True)
    image2_avg_angle = Column(Float, nullable=True)
    image2_angle_std_dev = Column(Float, nullable=True)
    # Image 3 measurements
    image3_width_mm = Column(Float, nullable=True)
    image3_height_mm = Column(Float, nullable=True)
    image3_avg_angle = Column(Float, nullable=True)
    image3_angle_std_dev = Column(Float, nullable=True)
    # Image 4 measurements
    image4_width_mm = Column(Float, nullable=True)
    image4_height_mm = Column(Float, nullable=True)
    image4_avg_angle = Column(Float, nullable=True)
    image4_angle_std_dev = Column(Float, nullable=True)
    # Image 5 measurements
    image5_width_mm = Column(Float, nullable=True)
    image5_height_mm = Column(Float, nullable=True)
    image5_avg_angle = Column(Float, nullable=True)
    image5_angle_std_dev = Column(Float, nullable=True)


class MVICResult(Base):
    """Results table for MVIC Test - stores data for each of 5 images"""
    __tablename__ = "weekly_mvic_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('weekly_mvic.id'), nullable=False)
    image_number = Column(Integer, nullable=False)  # 1-5
    filename = Column(String, nullable=True)
    # Corner angles
    top_left_angle = Column(Float, nullable=False)
    top_right_angle = Column(Float, nullable=False)
    bottom_left_angle = Column(Float, nullable=False)
    bottom_right_angle = Column(Float, nullable=False)
    # Field dimensions
    height = Column(Float, nullable=False)  # mm
    width = Column(Float, nullable=False)   # mm


class MVICFenteV2Test(Base):
    """Weekly MVIC Fente V2 Test - MLC Slit Analysis"""
    __tablename__ = "weekly_mvic_fente_v2"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    filenames = Column(Text, nullable=True)  # Comma-separated list of filenames
    visualization_paths = Column(Text, nullable=True)  # JSON array of visualization file paths
    file_results = Column(Text, nullable=True)  # JSON string containing measurement results


class MVICFenteV2Result(Base):
    """Results table for MVIC Fente V2 - stores slit data per image"""
    __tablename__ = "weekly_mvic_fente_v2_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('weekly_mvic_fente_v2.id'), nullable=False)
    image_number = Column(Integer, nullable=False)  # Which image
    filename = Column(String, nullable=True)
    slit_number = Column(Integer, nullable=False)  # Which slit in this image
    # Slit measurements
    width_mm = Column(Float, nullable=False)  # Slit width in mm
    height_pixels = Column(Float, nullable=False)  # Slit height in pixels
    center_u = Column(Float, nullable=True)  # U coordinate of slit center
    center_v = Column(Float, nullable=True)  # V coordinate of slit center


class PIQTTest(Base):
    """Weekly PIQT (Philips Image Quality Test)"""
    __tablename__ = "weekly_piqt"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    filenames = Column(Text, nullable=True)
    # Test result values
    snr_value = Column(Float, nullable=True)
    uniformity_value = Column(Float, nullable=True)
    ghosting_value = Column(Float, nullable=True)
    # Store full results as JSON
    results_json = Column(Text, nullable=True)


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


class LeafPositionTest(Base):
    """Weekly Leaf Position Test - MLC Blade Position and Length Analysis"""
    __tablename__ = "weekly_leaf_position"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(DateTime, nullable=False, index=True)
    operator = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    overall_result = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    filenames = Column(Text, nullable=True)  # Comma-separated list of filenames
    visualization_paths = Column(Text, nullable=True)  # JSON array of visualization file paths
    file_results = Column(Text, nullable=True)  # JSON string containing detailed measurement results


class LeafPositionResult(Base):
    """Results table for Leaf Position Test - stores data for each blade"""
    __tablename__ = "weekly_leaf_position_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('weekly_leaf_position.id'), nullable=False)
    image_number = Column(Integer, nullable=False)  # Which image/file
    filename = Column(String, nullable=True)
    blade_pair = Column(Integer, nullable=False)  # Blade pair number (27-54)
    
    # Position coordinates
    position_u_px = Column(Float, nullable=True)  # Horizontal position in pixels
    v_sup_px = Column(Float, nullable=True)  # Top edge V coordinate in pixels
    v_inf_px = Column(Float, nullable=True)  # Bottom edge V coordinate in pixels
    
    # Distance measurements
    distance_sup_mm = Column(Float, nullable=True)  # Distance from center to top edge in mm
    distance_inf_mm = Column(Float, nullable=True)  # Distance from center to bottom edge in mm
    length_mm = Column(Float, nullable=True)  # Total blade length in mm
    
    # Validation
    field_size_mm = Column(Float, nullable=True)  # Detected field size (20, 30, or 40mm expected)
    is_valid = Column(String, nullable=False)  # 'OK', 'OUT_OF_TOLERANCE', or 'CLOSED'
    status_message = Column(Text, nullable=True)  # Detailed status message
