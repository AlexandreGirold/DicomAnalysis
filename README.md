# DicomAnalysis
For Curie

cd c:\Users\agirold\Desktop\DicomAnalysis\backend
.\env\Scripts\Activate.ps1
pip install -r requirements.txt


Package	Purpose	Needed?
fastapi	Web framework for building REST API	✅ YES - Core backend
uvicorn	ASGI server to run FastAPI	✅ YES - Required to run the app
pydicom	Read and parse DICOM medical image files	✅ YES - Core functionality
opencv-python	Image processing (filters, analysis, transformations)	✅ YES - Analyze DICOM images
numpy	Numerical computing, array operations	✅ YES - Required by OpenCV & image processing
pillow	Image manipulation (resize, convert formats)	✅ YES - Display/convert images
sqlalchemy	ORM for SQLite database operations	✅ YES - Store analysis results
python-multipart	Handle file uploads in FastAPI	✅ YES - Upload DICOM files via form
pydantic	Data validation for API requests/responses	✅ YES - Validate input data

api/dicom.py (endpoint receives file)
    ↓
services/dicom_service.py (reads DICOM file)
    ↓
services/preprocessing_service.py (preprocessing: normalize, resize, denoise, etc.)
    ↓
services/analysis_service.py (run analysis on preprocessed image)
    ↓
database.py (store results)