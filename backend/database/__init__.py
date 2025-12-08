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
    PIQTTest, PIQTResult
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
    'PIQTTest', 'PIQTResult',
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
