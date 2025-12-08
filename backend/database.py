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

__all__ = [
    'Base', 'engine', 'SessionLocal', 'init_db',
    'SafetySystemsTest', 'SafetySystemsResult',
    'NiveauHeliumTest', 'NiveauHeliumResult',
    'MLCLeafJawTest',
    'MVICTest', 'MVICResult',
    'PIQTTest', 'PIQTResult',
    'PositionTableV2Test', 'PositionTableV2Result',
    'AlignementLaserTest', 'AlignementLaserResult',
    'QuasarTest', 'QuasarResult',
    'IndiceQualityTest', 'IndiceQualityResult',
    'MVCenterConfig',
    'FieldCenterDetection', 'FieldEdgeDetection',
    'LeafAlignment', 'CenterDetection',
    'JawPosition', 'BladePositions', 'BladeStraightness'
]
