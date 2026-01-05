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

#ecverything hahaha
from database import * 

#backward compatibility
from database import (
    Base, engine, SessionLocal, init_db,
    SafetySystemsTest, SafetySystemsResult,
    NiveauHeliumTest, NiveauHeliumResult,
    MLCLeafJawTest,
    MVICTest, MVICResult,
    MVICFenteV2Test, MVICFenteV2Result,
    PIQTTest, PIQTResult,
    LeafPositionTest, LeafPositionResult,
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
    'MVICFenteV2Test', 'MVICFenteV2Result',
    'PIQTTest', 'PIQTResult',
    'LeafPositionTest', 'LeafPositionResult',
    'PositionTableV2Test', 'PositionTableV2Result',
    'AlignementLaserTest', 'AlignementLaserResult',
    'QuasarTest', 'QuasarResult',
    'IndiceQualityTest', 'IndiceQualityResult',
    'MVCenterConfig',
    'FieldCenterDetection', 'FieldEdgeDetection',
    'LeafAlignment', 'CenterDetection',
    'JawPosition', 'BladePositions', 'BladeStraightness'
]
