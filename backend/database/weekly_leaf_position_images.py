"""
New table to store image-level data for LeafPosition tests
Each row represents one of the 6 images with its averages
"""
from sqlalchemy import Column, Integer, Float, ForeignKey, String
from sqlalchemy.orm import relationship
from .config import Base


class LeafPositionImage(Base):
    """Stores average measurements for each image in a LeafPosition test"""
    __tablename__ = 'weekly_leaf_position_images'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey('weekly_leaf_position.id'), nullable=False)
    image_number = Column(Integer, nullable=False)  # 1-6 in upload order
    identified_image_number = Column(Integer)  # 1-6 based on position identification
    filename = Column(String)
    top_average = Column(Float)  # Average of all blade top positions for this image
    bottom_average = Column(Float)  # Average of all blade bottom positions for this image
    
    # Relationship back to parent test
    test = relationship("LeafPositionTest", back_populates="images")
