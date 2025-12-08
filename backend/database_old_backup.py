"""
Quality Control Test Database
LEGACY FILE - For backward compatibility only

This file redirects all imports to the new modular database structure.
All models are now organized in the 'database' package:
  - database/config.py - Core configuration
  - database/daily_tests.py - Daily test models
  - database/weekly_tests.py - Weekly test models
  - database/monthly_tests.py - Monthly test models
  - database/mlc_curie.py - MLC Curie test models

Please import from 'database' package instead:
    from database import SessionLocal, MVCenterConfig
"""

# Import everything from the new modular structure
from database import *  # noqa: F401, F403

# Maintain backward compatibility - expose all exports
from database import (
    Base, engine, SessionLocal, init_db,
    SafetySystemsTest, SafetySystemsResult,
    NiveauHeliumTest, NiveauHeliumResult,
    MLCLeafJawTest,
    MVICTest, MVICResult,
    PIQTTest, PIQTResult,
    PositionTableV2Test, PositionTableV2Result,
    AlignementLaserTest, AlignementLaserResult,
    QuasarTest, QuasarResult,
    IndiceQualityTest, IndiceQualityResult,
    MVCenterConfig,
    FieldCenterDetection, FieldEdgeDetection,
    LeafAlignment, CenterDetection,
    JawPosition, BladePositions, BladeStraightness
)

# ===== GUIDE: ADDING NEW TESTS =====
"""
HOW TO ADD A NEW TEST:

1. Create a new model class inheriting from Base:
   
   class NewTestName(Base):
       __tablename__ = "frequency_test_name"  # e.g., "daily_new_test"
       
       id = Column(Integer, primary_key=True, index=True)
       test_date = Column(DateTime, nullable=False, index=True)
       operator = Column(String, nullable=False)
       upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
       overall_result = Column(String, nullable=False)
       notes = Column(Text, nullable=True)

2. Add to appropriate section (DAILY/WEEKLY/MONTHLY)

3. Restart the application - SQLAlchemy will auto-create the new table

4. The table is persistent - it will NOT be overwritten on restart

That's it! The init_db() function handles table creation automatically.
"""

# ===== DATABASE CONFIGURATION =====
DB_PATH = Path(__file__).parent / "data" / "qc_tests.db"
DB_PATH.parent.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, echo=False)

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ===== DAILY TESTS =====

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


# ===== WEEKLY TESTS =====

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
    helium_level = Column(Float, nullable=False)  # Helium level in percentage


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

    # New columns for image-specific details
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

    # Detailed result categories
    ffu1_nema_sn_b1 = Column(Float, nullable=True)
    ffu1_nema_sn_b2 = Column(Float, nullable=True)
    ffu1_nema_sn_b3 = Column(Float, nullable=True)
    ffu1_nema_int_unif1 = Column(Float, nullable=True)
    ffu1_nema_int_unif2 = Column(Float, nullable=True)
    ffu1_nema_int_unif3 = Column(Float, nullable=True)
    ffu2_nema_sn_b1 = Column(Float, nullable=True)
    ffu2_nema_sn_b2 = Column(Float, nullable=True)
    ffu2_nema_sn_b3 = Column(Float, nullable=True)
    ffu2_nema_int_unif1 = Column(Float, nullable=True)
    ffu2_nema_int_unif2 = Column(Float, nullable=True)
    ffu2_nema_int_unif3 = Column(Float, nullable=True)
    spatial_linearity_nema_perc_dif1 = Column(Float, nullable=True)
    slice_profile_nema_fwhm1 = Column(Float, nullable=True)
    slice_profile_nema_fwhm2 = Column(Float, nullable=True)
    slice_profile_nema_fwhm3 = Column(Float, nullable=True)
    slice_profile_nema_slice_int1 = Column(Float, nullable=True)
    slice_profile_nema_slice_int2 = Column(Float, nullable=True)
    slice_profile_nema_slice_int3 = Column(Float, nullable=True)
    spatial_resolution_nema_hor_pxl_size1 = Column(Float, nullable=True)
    spatial_resolution_nema_hor_pxl_size2 = Column(Float, nullable=True)
    spatial_resolution_nema_ver_pxl_size1 = Column(Float, nullable=True)
    spatial_resolution_nema_ver_pxl_size2 = Column(Float, nullable=True)


# ===== MONTHLY TESTS =====

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



# ===== MLC CURIE CONFIGURATION =====

class MVCenterConfig(Base):
    """Configuration table for MV center point (u, v) for MLC Curie tests"""
    __tablename__ = "mlc_curie_mv_center_config"
    id = Column(Integer, primary_key=True, index=True)
    u = Column(Float, nullable=False, default=511.03)
    v = Column(Float, nullable=False, default=652.75)

# ===== MLC LEAF AND JAW WEEKLY TESTS =====

class FieldCenterDetection(Base):
    """Field Center Detection Results"""
    __tablename__ = "weekly_mlc_field_center_detection"

    id = Column(Integer, primary_key=True, index=True)
    mlc_test_id = Column(Integer, ForeignKey('weekly_mlc_leaf_jaw.id'), nullable=False)
    image_id = Column(Integer, nullable=False)
    x_center = Column(Float, nullable=False)
    y_center = Column(Float, nullable=False)


class FieldEdgeDetection(Base):
    """Field Edge Detection Results"""
    __tablename__ = "weekly_mlc_field_edge_detection"

    id = Column(Integer, primary_key=True, index=True)
    mlc_test_id = Column(Integer, ForeignKey('weekly_mlc_leaf_jaw.id'), nullable=False)
    image_id = Column(Integer, nullable=False)
    edge_position = Column(Float, nullable=False)


class LeafAlignment(Base):
    """Leaf Alignment Results"""
    __tablename__ = "weekly_mlc_leaf_alignment"

    id = Column(Integer, primary_key=True, index=True)
    mlc_test_id = Column(Integer, ForeignKey('weekly_mlc_leaf_jaw.id'), nullable=False)
    image_id = Column(Integer, nullable=False)
    leaf_position = Column(Float, nullable=False)
    alignment_error = Column(Float, nullable=False)


class CenterDetection(Base):
    """Center Detection Results (Image 1)"""
    __tablename__ = "weekly_mlc_center_detection"

    id = Column(Integer, primary_key=True, index=True)
    mlc_test_id = Column(Integer, ForeignKey('weekly_mlc_leaf_jaw.id'), nullable=False)
    image_id = Column(Integer, nullable=False)
    x_center = Column(Float, nullable=False)
    y_center = Column(Float, nullable=False)


class JawPosition(Base):
    """Jaw Position Results (Image 2)"""
    __tablename__ = "weekly_mlc_jaw_position"

    id = Column(Integer, primary_key=True, index=True)
    mlc_test_id = Column(Integer, ForeignKey('weekly_mlc_leaf_jaw.id'), nullable=False)
    image_id = Column(Integer, nullable=False)
    jaw_position = Column(Float, nullable=False)


class BladePositions(Base):
    """Blade Positions Results (Images 3 & 4)"""
    __tablename__ = "weekly_mlc_blade_positions"

    id = Column(Integer, primary_key=True, index=True)
    mlc_test_id = Column(Integer, ForeignKey('weekly_mlc_leaf_jaw.id'), nullable=False)
    image_id = Column(Integer, nullable=False)
    blade_type = Column(String, nullable=False)  # "top" or "bottom"
    leaf_number = Column(Integer, nullable=False)
    position = Column(Float, nullable=False)
    field_size = Column(Float, nullable=False)  # Field size for each leaf
    moyenne = Column(Float, nullable=False)  # Average value for the leaf
    ecart_type = Column(Float, nullable=False)  # Standard deviation for the leaf


class BladeStraightness(Base):
    """Blade Straightness Results (Image 5)"""
    __tablename__ = "weekly_mlc_blade_straightness"

    id = Column(Integer, primary_key=True, index=True)
    mlc_test_id = Column(Integer, ForeignKey('weekly_mlc_leaf_jaw.id'), nullable=False)
    image_id = Column(Integer, nullable=False)
    straightness_value = Column(Float, nullable=False)


# ===== DATABASE INITIALIZATION =====

def init_db():
    """
    Initialize database: creates all tables if they don't exist
    Safe to call multiple times only creates missing tables (useful for adding new tests)
    """
    Base.metadata.create_all(bind=engine)


# Initialize database on module import
init_db()



