# DICOM Analysis System

A comprehensive web-based DICOM image analysis system built with Java Spring Boot and JavaScript/HTML.

## Overview

This project provides a complete architecture for building a DICOM (Digital Imaging and Communications in Medicine) image analysis and viewing system. The system allows users to:

- Upload and store DICOM medical images
- View DICOM images in a web browser
- Extract and display DICOM metadata
- Perform image analysis and measurements
- Generate analysis reports

## Architecture

The system consists of two main components:

1. **Backend**: Java Spring Boot application with RESTful API
   - DICOM file parsing using DCM4CHE library
   - Image processing and analysis
   - PostgreSQL database for metadata storage
   - File system or cloud storage for DICOM files

2. **Frontend**: JavaScript/HTML web application
   - DICOM viewer using Cornerstone.js
   - Drag-and-drop file upload
   - Interactive image viewing tools
   - Analysis results visualization

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete system architecture documentation
  - High-level architecture overview
  - Backend structure and components
  - Frontend structure and components
  - Data flow and integration
  - Security considerations
  - Deployment architecture
  - Scalability considerations

- **[QUICK_START.md](QUICK_START.md)** - Quick start guide for developers
  - Prerequisites and setup
  - Project initialization steps
  - Basic implementation checklist
  - Testing instructions
  - Docker setup

- **[API_SPECIFICATION.md](API_SPECIFICATION.md)** - REST API documentation
  - Complete API endpoint reference
  - Request/response examples
  - Authentication and security
  - Error handling
  - WebSocket support

## Technology Stack

### Backend
- **Java 17+**
- **Spring Boot 3.x** - Application framework
- **Spring Data JPA** - Database access
- **PostgreSQL** - Metadata storage
- **DCM4CHE 5.x** - DICOM parsing library
- **Redis** (optional) - Caching

### Frontend
- **HTML5** - Page structure
- **CSS3** - Styling
- **JavaScript (ES6+)** - Application logic
- **Cornerstone.js** - DICOM image rendering
- **Axios** - HTTP client
- **Bootstrap** (optional) - UI framework

## Key Features

### DICOM Processing
- Parse and validate DICOM files
- Extract comprehensive metadata
- Support for multiple modalities (CT, MR, X-Ray, etc.)
- Batch file processing

### Image Viewing
- Web-based DICOM viewer
- Zoom, pan, and window/level controls
- Multi-planar reconstruction (MPR)
- Measurements and annotations
- Thumbnail generation

### Image Analysis
- Image statistics (mean, median, std dev)
- Histogram generation
- Region of interest (ROI) analysis
- Hounsfield Unit (HU) calculations
- Custom analysis algorithms

### Data Management
- Hierarchical storage (Study/Series/Instance)
- Metadata search and filtering
- File compression and retention
- Export to standard formats

## Getting Started

See the [QUICK_START.md](QUICK_START.md) guide for detailed setup instructions.

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/AlexandreGirold/DicomAnalysis.git
   cd DicomAnalysis
   ```

2. **Set up database**
   ```bash
   # Create PostgreSQL database
   createdb dicomdb
   ```

3. **Configure application**
   ```bash
   # Edit src/main/resources/application.properties
   # Set database credentials and storage path
   ```

4. **Build and run**
   ```bash
   mvn clean install
   mvn spring-boot:run
   ```

5. **Access application**
   ```
   http://localhost:8080
   ```

## Project Structure

```
DicomAnalysis/
├── src/
│   ├── main/
│   │   ├── java/               # Java source code
│   │   └── resources/
│   │       ├── static/         # Frontend files (HTML, CSS, JS)
│   │       └── application.properties
│   └── test/                   # Test files
├── ARCHITECTURE.md             # Architecture documentation
├── QUICK_START.md             # Setup guide
├── API_SPECIFICATION.md       # API documentation
├── pom.xml                    # Maven dependencies
└── README.md                  # This file
```

## Development Workflow

1. Start PostgreSQL database
2. Run Spring Boot application: `mvn spring-boot:run`
3. Open browser to `http://localhost:8080`
4. Upload DICOM files and test functionality
5. Make changes and iterate

## Testing

### Sample DICOM Files

Download free sample DICOM files for testing:
- [Rubo Medical](https://www.rubomedical.com/dicom_files/)
- [Medical Connections](https://www.medicalconnections.co.uk/FreeNema)

### Testing the API

Use tools like Postman, curl, or the built-in API documentation (if Swagger is enabled):
```bash
# Upload a DICOM file
curl -X POST http://localhost:8080/api/dicom/upload \
  -F "file=@sample.dcm"

# List studies
curl http://localhost:8080/api/dicom/studies
```

## Deployment

### Docker Deployment

```bash
# Build the application
mvn clean package

# Build Docker image
docker build -t dicom-analysis .

# Run with Docker Compose
docker-compose up -d
```

### Cloud Deployment

The application can be deployed to:
- AWS (EC2, RDS, S3)
- Azure (App Service, PostgreSQL, Blob Storage)
- Google Cloud Platform (Compute Engine, Cloud SQL, Cloud Storage)

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed deployment architectures.

## Security Considerations

- **Authentication**: JWT-based authentication
- **Authorization**: Role-based access control
- **HTTPS**: TLS encryption for all communications
- **Input Validation**: Strict validation of all inputs
- **File Validation**: DICOM format validation
- **HIPAA Compliance**: Consider when handling real patient data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## License

[Specify your license here]

## Support

For questions or issues:
- Check the documentation in the docs/ directory
- Review the [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Consult the [API_SPECIFICATION.md](API_SPECIFICATION.md) for API details
- Open an issue in the repository

## Acknowledgments

- **DCM4CHE** - DICOM library for Java
- **Cornerstone.js** - DICOM image rendering for web
- **Spring Boot** - Application framework
- **DICOM Community** - Standards and support

## Resources

- [DICOM Standard](https://www.dicomstandard.org/)
- [DCM4CHE Documentation](https://github.com/dcm4che/dcm4che)
- [Cornerstone.js Documentation](https://cornerstonejs.org/)
- [Spring Boot Documentation](https://spring.io/projects/spring-boot)

---

**For Curie** ❤️
