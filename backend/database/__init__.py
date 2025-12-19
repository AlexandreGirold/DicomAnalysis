"""
Quality Control Test Database
Modular database structure for Daily, Weekly, and Monthly QC tests
"""

from .config import Base, engine, SessionLocal, init_db
from .daily_tests import SafetySystemsTest, SafetySystemsResult
from .weekly_tests import (
    NiveauHeliumTest, NiveauHeliumResult,
    MLCLeafJawTest,
    MVICTest, MVICResult,
    MVICFenteV2Test, MVICFenteV2Result,
    PIQTTest, PIQTResult,
    LeafPositionTest, LeafPositionResult
)
from .monthly_tests import (
    PositionTableV2Test, PositionTableV2Result,
    AlignementLaserTest, AlignementLaserResult,
    QuasarTest, QuasarResult,
    IndiceQualityTest, IndiceQualityResult
)
from .mlc_curie import (
    MVCenterConfig,
    FieldCenterDetection,
    FieldEdgeDetection,
    LeafAlignment,
    CenterDetection,
    JawPosition,
    BladePositions,
    BladeStraightness
)
from .queries import (
    get_all_safety_systems_tests, get_safety_systems_test_by_id, delete_safety_systems_test,
    get_all_niveau_helium_tests, get_niveau_helium_test_by_id, delete_niveau_helium_test,
    get_all_mlc_test_sessions, get_mlc_test_session_by_id, delete_mlc_test_session,
    get_all_mvic_test_sessions, get_mvic_test_session_by_id, delete_mvic_test_session,
    get_all_mvic_fente_v2_tests, get_mvic_fente_v2_test_by_id, delete_mvic_fente_v2_test,
    get_all_piqt_tests, get_piqt_test_by_id, delete_piqt_test,
    get_all_position_table_tests, get_position_table_test_by_id, delete_position_table_test,
    get_all_alignement_laser_tests, get_alignement_laser_test_by_id, delete_alignement_laser_test,
    get_all_quasar_tests, get_quasar_test_by_id, delete_quasar_test,
    get_all_indice_quality_tests, get_indice_quality_test_by_id, delete_indice_quality_test,
    get_all_leaf_position_tests, get_leaf_position_test_by_id, delete_leaf_position_test
)

# Initialize database on import
init_db()

__all__ = [
    # Core
    'Base', 'engine', 'SessionLocal', 'init_db',
    # Daily
    'SafetySystemsTest', 'SafetySystemsResult',
    # Weekly
    'NiveauHeliumTest', 'NiveauHeliumResult',
    'MLCLeafJawTest',
    'MVICTest', 'MVICResult',
    'MVICFenteV2Test', 'MVICFenteV2Result',
    'PIQTTest', 'PIQTResult',
    'LeafPositionTest', 'LeafPositionResult',
    # Monthly
    'PositionTableV2Test', 'PositionTableV2Result',
    'AlignementLaserTest', 'AlignementLaserResult',
    'QuasarTest', 'QuasarResult',
    'IndiceQualityTest', 'IndiceQualityResult',
    # MLC Curie
    'MVCenterConfig',
    'FieldCenterDetection', 'FieldEdgeDetection',
    'LeafAlignment', 'CenterDetection',
    'JawPosition', 'BladePositions', 'BladeStraightness'
]
