"""
Database module for storing MLC blade analysis results
Uses SQLite for local storage
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
from pathlib import Path

# Database file location
DB_PATH = Path(__file__).parent / "data" / "mlc_analysis.db"
DB_PATH.parent.mkdir(exist_ok=True)

# Create SQLAlchemy engine
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, echo=False)

# Create base class for models
Base = declarative_base()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class AnalysisTest(Base):
    """
    Represents a single test/analysis session
    """
    __tablename__ = "analysis_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_creation_date = Column(DateTime, nullable=True)  # Original DICOM file creation date
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_blades = Column(Integer, nullable=False)
    ok_blades = Column(Integer, nullable=False)
    out_of_tolerance = Column(Integer, nullable=False)
    closed_blades = Column(Integer, nullable=False)
    visualization_path = Column(String, nullable=True)
    
    # Relationship to blade results
    blade_results = relationship("BladeResult", back_populates="test", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        # Parse visualization paths (could be JSON array or single string)
        viz_paths = None
        if self.visualization_path:
            try:
                viz_paths = json.loads(self.visualization_path)  # Try to parse as JSON
            except:
                viz_paths = self.visualization_path  # Single string
        
        return {
            'id': self.id,
            'filename': self.filename,
            'file_creation_date': self.file_creation_date.isoformat() if self.file_creation_date else None,
            'upload_date': self.upload_date.isoformat(),
            'summary': {
                'total_blades': self.total_blades,
                'ok_blades': self.ok_blades,
                'out_of_tolerance': self.out_of_tolerance,
                'closed_blades': self.closed_blades
            },
            'visualization': viz_paths,
            'blade_count': len(self.blade_results)
        }
    
    def to_dict_full(self):
        """Convert to dictionary with full blade results"""
        # Parse visualization paths (could be JSON array or single string)
        viz_paths = None
        if self.visualization_path:
            try:
                viz_paths = json.loads(self.visualization_path)  # Try to parse as JSON
            except:
                viz_paths = self.visualization_path  # Single string
        
        return {
            'id': self.id,
            'filename': self.filename,
            'file_creation_date': self.file_creation_date.isoformat() if self.file_creation_date else None,
            'upload_date': self.upload_date.isoformat(),
            'summary': {
                'total_blades': self.total_blades,
                'ok_blades': self.ok_blades,
                'out_of_tolerance': self.out_of_tolerance,
                'closed_blades': self.closed_blades
            },
            'visualization': viz_paths,
            'results': [blade.to_dict() for blade in self.blade_results]
        }


class BladeResult(Base):
    """
    Represents individual blade measurement results
    """
    __tablename__ = "blade_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('analysis_tests.id'), nullable=False)
    blade_pair = Column(Integer, nullable=False)
    distance_sup_mm = Column(Float, nullable=True)
    distance_inf_mm = Column(Float, nullable=True)
    field_size_mm = Column(Float, nullable=True)
    status = Column(String, nullable=False)
    
    # Relationship back to test
    test = relationship("AnalysisTest", back_populates="blade_results")
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'blade_pair': self.blade_pair,
            'distance_sup_mm': round(self.distance_sup_mm, 3) if self.distance_sup_mm is not None else None,
            'distance_inf_mm': round(self.distance_inf_mm, 3) if self.distance_inf_mm is not None else None,
            'field_size_mm': round(self.field_size_mm, 3) if self.field_size_mm is not None else None,
            'status': self.status
        }


def init_db():
    """Initialize the database - create all tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session - use with context manager"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_analysis_result(filename: str, file_creation_date: datetime, results: list, summary: dict, visualization: str = None):
    """
    Save analysis results to database
    
    Args:
        filename: Name of the DICOM file
        file_creation_date: Creation date of the DICOM file
        results: List of blade result dictionaries
        summary: Summary statistics dictionary
        visualization: Path to visualization image or list of visualization paths (optional)
    
    Returns:
        test_id: ID of the saved test
    """
    db = SessionLocal()
    try:
        # Handle visualization as list or string
        viz_path = None
        if visualization:
            if isinstance(visualization, list):
                viz_path = json.dumps(visualization)  # Store as JSON array
            else:
                viz_path = visualization
        
        # Create test record
        test = AnalysisTest(
            filename=filename,
            file_creation_date=file_creation_date,
            total_blades=summary['total_blades'],
            ok_blades=summary['ok_blades'],
            out_of_tolerance=summary['out_of_tolerance'],
            closed_blades=summary['closed_blades'],
            visualization_path=viz_path
        )
        db.add(test)
        db.flush()  # Get the test ID
        
        # Create blade result records
        for result in results:
            blade = BladeResult(
                test_id=test.id,
                blade_pair=result['blade_pair'],
                distance_sup_mm=result.get('distance_sup_mm'),
                distance_inf_mm=result.get('distance_inf_mm'),
                field_size_mm=result.get('field_size_mm'),
                status=result['status']
            )
            db.add(blade)
        
        db.commit()
        return test.id
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def update_test_visualizations(test_id: int, visualization_files: list):
    """
    Update test with visualization file paths
    
    Args:
        test_id: ID of the test
        visualization_files: List of visualization file paths
    """
    db = SessionLocal()
    try:
        test = db.query(AnalysisTest).filter(AnalysisTest.id == test_id).first()
        if test:
            test.visualization_path = json.dumps(visualization_files)
            db.commit()
    finally:
        db.close()


def get_all_tests(limit: int = 100, offset: int = 0, start_date: str = None, end_date: str = None):
    """
    Get list of all tests (summary only), ordered by file creation date (oldest first)
    
    Args:
        limit: Maximum number of tests to return
        offset: Number of tests to skip
        start_date: Filter tests from this date onwards (ISO format: YYYY-MM-DD)
        end_date: Filter tests up to this date (ISO format: YYYY-MM-DD)
    
    Returns:
        List of test dictionaries
    """
    db = SessionLocal()
    try:
        query = db.query(AnalysisTest)
        
        # Apply date filters if provided
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(AnalysisTest.file_creation_date >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            # Add one day to include the entire end date
            from datetime import timedelta
            end_dt = end_dt + timedelta(days=1)
            query = query.filter(AnalysisTest.file_creation_date < end_dt)
        
        tests = query.order_by(AnalysisTest.file_creation_date.asc())\
                     .limit(limit)\
                     .offset(offset)\
                     .all()
        return [test.to_dict() for test in tests]
    finally:
        db.close()


def get_test_by_id(test_id: int):
    """
    Get a specific test with all blade results
    
    Args:
        test_id: ID of the test
    
    Returns:
        Test dictionary with full results, or None if not found
    """
    db = SessionLocal()
    try:
        test = db.query(AnalysisTest).filter(AnalysisTest.id == test_id).first()
        if test:
            return test.to_dict_full()
        return None
    finally:
        db.close()


def delete_test(test_id: int):
    """
    Delete a test and all its blade results
    
    Args:
        test_id: ID of the test to delete
    
    Returns:
        True if deleted, False if not found
    """
    db = SessionLocal()
    try:
        test = db.query(AnalysisTest).filter(AnalysisTest.id == test_id).first()
        if test:
            db.delete(test)
            db.commit()
            return True
        return False
    finally:
        db.close()


def delete_all_tests():
    """
    Delete ALL tests from the database
    WARNING: This cannot be undone!
    
    Returns:
        Number of tests deleted
    """
    db = SessionLocal()
    try:
        count = db.query(AnalysisTest).count()
        db.query(AnalysisTest).delete()
        db.commit()
        return count
    finally:
        db.close()


def get_test_count():
    """
    Get total number of tests in database
    
    Returns:
        Count of tests
    """
    db = SessionLocal()
    try:
        return db.query(AnalysisTest).count()
    finally:
        db.close()


def get_blade_trend(blade_pair: str, limit: int = 50):
    """
    Get historical data for a specific blade pair to track trends over time
    
    Args:
        blade_pair: Blade pair number (e.g., "Blade_27-28")
        limit: Maximum number of records to return
    
    Returns:
        List of measurements ordered by file creation date (oldest first)
    """
    db = SessionLocal()
    try:
        results = db.query(BladeResult, AnalysisTest.file_creation_date, AnalysisTest.filename)\
                    .join(AnalysisTest)\
                    .filter(BladeResult.blade_pair == blade_pair)\
                    .order_by(AnalysisTest.file_creation_date.asc())\
                    .limit(limit)\
                    .all()
        
        trend_data = []
        for blade_result, file_date, filename in results:
            trend_data.append({
                'date': file_date.isoformat() if file_date else None,
                'filename': filename,
                'distance_sup_mm': blade_result.distance_sup_mm,
                'distance_inf_mm': blade_result.distance_inf_mm,
                'field_size_mm': blade_result.field_size_mm,
                'status': blade_result.status
            })
        
        return trend_data
        
    finally:
        db.close()


def get_database_stats():
    """
    Get database statistics
    
    Returns:
        Dictionary with database statistics
    """
    db = SessionLocal()
    try:
        total_tests = db.query(AnalysisTest).count()
        total_blades = db.query(BladeResult).count()
        
        # Get date range
        oldest_test = db.query(AnalysisTest).order_by(AnalysisTest.file_creation_date.asc()).first()
        newest_test = db.query(AnalysisTest).order_by(AnalysisTest.file_creation_date.desc()).first()
        
        return {
            'total_tests': total_tests,
            'total_blade_measurements': total_blades,
            'oldest_test_date': oldest_test.file_creation_date.isoformat() if oldest_test and oldest_test.file_creation_date else None,
            'newest_test_date': newest_test.file_creation_date.isoformat() if newest_test and newest_test.file_creation_date else None
        }
    finally:
        db.close()


# Initialize database on module import
init_db()
