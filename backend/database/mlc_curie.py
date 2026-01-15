"""
MLC Curie Test Models
Database models for MLC (Multi-Leaf Collimator) Curie tests
Includes configuration and all MLC-related result tables
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from .config import Base


class MVCenterConfig(Base):
    """Configuration table for MV center point (u, v) coordinates"""
    __tablename__ = "mlc_curie_mv_center_config"
    
    id = Column(Integer, primary_key=True, index=True)
    u = Column(Float, nullable=False, default=511.03)
    v = Column(Float, nullable=False, default=652.75)


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
    field_size = Column(Float, nullable=False)
    moyenne = Column(Float, nullable=False)  # Average
    ecart_type = Column(Float, nullable=False)  # Standard deviation


class BladeStraightness(Base):
    """Blade Straightness Results (Image 5)"""
    __tablename__ = "weekly_mlc_blade_straightness"

    id = Column(Integer, primary_key=True, index=True)
    mlc_test_id = Column(Integer, ForeignKey('weekly_mlc_leaf_jaw.id'), nullable=False)
    image_id = Column(Integer, nullable=False)
    straightness_value = Column(Float, nullable=False)
