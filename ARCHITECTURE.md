# DICOM Analysis System Architecture

## Overview
This document outlines the architecture for a DICOM (Digital Imaging and Communications in Medicine) image analysis system built with Java Spring Boot backend and JavaScript/HTML frontend.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Browser (Client)                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  HTML5 + JavaScript Frontend                           │ │
│  │  - DICOM Viewer (Cornerstone.js / OHIF Viewer)        │ │
│  │  - Image Upload Interface                              │ │
│  │  - Analysis Results Display                            │ │
│  │  - REST API Client (Axios/Fetch)                       │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTPS/REST API
                   │
┌──────────────────▼──────────────────────────────────────────┐
│              Spring Boot Application                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Presentation Layer (Controllers)                      │ │
│  │  - REST Controllers                                    │ │
│  │  - Request/Response DTOs                               │ │
│  │  - Exception Handlers                                  │ │
│  └────────────────┬───────────────────────────────────────┘ │
│                   │                                          │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │  Service Layer                                         │ │
│  │  - DICOM Processing Service                           │ │
│  │  - Image Analysis Service                             │ │
│  │  - File Storage Service                               │ │
│  │  - Business Logic                                      │ │
│  └────────────────┬───────────────────────────────────────┘ │
│                   │                                          │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │  Data Access Layer                                     │ │
│  │  - Repositories                                        │ │
│  │  - Entity Models                                       │ │
│  │  - Database Access                                     │ │
│  └────────────────┬───────────────────────────────────────┘ │
│                   │                                          │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │  DICOM Library Integration                            │ │
│  │  - DCM4CHE Library                                     │ │
│  │  - DICOM Parser                                        │ │
│  │  - Metadata Extraction                                 │ │
│  │  - Image Processing                                    │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│              Data Storage Layer                              │
│  ┌─────────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │   PostgreSQL    │  │  File System   │  │    Redis     │ │
│  │   (Metadata)    │  │ (DICOM Files)  │  │   (Cache)    │ │
│  └─────────────────┘  └────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Backend Architecture (Java Spring Boot)

### 1. Project Structure

```
dicom-analysis/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/yourcompany/dicomanalysis/
│   │   │       ├── DicomAnalysisApplication.java
│   │   │       ├── config/
│   │   │       │   ├── SecurityConfig.java
│   │   │       │   ├── WebConfig.java
│   │   │       │   └── DicomConfig.java
│   │   │       ├── controller/
│   │   │       │   ├── DicomUploadController.java
│   │   │       │   ├── DicomAnalysisController.java
│   │   │       │   └── DicomMetadataController.java
│   │   │       ├── service/
│   │   │       │   ├── DicomParsingService.java
│   │   │       │   ├── DicomAnalysisService.java
│   │   │       │   ├── DicomStorageService.java
│   │   │       │   └── ImageProcessingService.java
│   │   │       ├── repository/
│   │   │       │   ├── DicomStudyRepository.java
│   │   │       │   ├── DicomSeriesRepository.java
│   │   │       │   └── AnalysisResultRepository.java
│   │   │       ├── model/
│   │   │       │   ├── entity/
│   │   │       │   │   ├── DicomStudy.java
│   │   │       │   │   ├── DicomSeries.java
│   │   │       │   │   ├── DicomInstance.java
│   │   │       │   │   └── AnalysisResult.java
│   │   │       │   └── dto/
│   │   │       │       ├── DicomMetadataDTO.java
│   │   │       │       ├── AnalysisRequestDTO.java
│   │   │       │       └── AnalysisResponseDTO.java
│   │   │       ├── exception/
│   │   │       │   ├── DicomParsingException.java
│   │   │       │   ├── DicomNotFoundException.java
│   │   │       │   └── GlobalExceptionHandler.java
│   │   │       └── util/
│   │   │           ├── DicomUtils.java
│   │   │           └── ImageUtils.java
│   │   └── resources/
│   │       ├── application.properties
│   │       ├── application-dev.properties
│   │       ├── application-prod.properties
│   │       └── static/
│   │           └── (Frontend files will go here)
│   └── test/
│       └── java/
│           └── com/yourcompany/dicomanalysis/
│               ├── controller/
│               ├── service/
│               └── integration/
└── pom.xml
```

### 2. Key Components

#### 2.1 Controllers (REST API)

**DicomUploadController**
- `POST /api/dicom/upload` - Upload DICOM files
- `POST /api/dicom/upload/multiple` - Upload multiple DICOM files
- Handles multipart file upload
- Returns upload status and file metadata

**DicomAnalysisController**
- `POST /api/dicom/analyze/{studyId}` - Analyze DICOM study
- `GET /api/dicom/analysis/{analysisId}` - Get analysis results
- `GET /api/dicom/analysis/{analysisId}/report` - Get analysis report
- Triggers analysis pipeline
- Returns analysis results and statistics

**DicomMetadataController**
- `GET /api/dicom/studies` - List all studies
- `GET /api/dicom/studies/{studyId}` - Get study details
- `GET /api/dicom/studies/{studyId}/series` - Get series in study
- `GET /api/dicom/studies/{studyId}/series/{seriesId}/instances` - Get instances
- `GET /api/dicom/metadata/{instanceId}` - Get DICOM metadata
- `GET /api/dicom/image/{instanceId}` - Get DICOM image (converted to PNG/JPEG)

#### 2.2 Service Layer

**DicomParsingService**
- Parse DICOM files using DCM4CHE library
- Extract metadata (patient info, study details, etc.)
- Validate DICOM file structure
- Extract pixel data

**DicomAnalysisService**
- Perform image analysis algorithms
- Calculate image statistics (mean, std, histogram)
- Detect regions of interest
- Apply image filters and transformations
- Generate analysis reports

**DicomStorageService**
- Store DICOM files on file system or cloud storage
- Organize files by Study/Series/Instance hierarchy
- Handle file compression
- Manage file retention policies

**ImageProcessingService**
- Convert DICOM to web-friendly formats (PNG, JPEG)
- Apply windowing (W/L adjustments)
- Generate thumbnails
- Apply image enhancements

#### 2.3 Data Models

**Entity Models**
- `DicomStudy` - Represents a DICOM study (Patient, Study Date, etc.)
- `DicomSeries` - Represents a series within a study
- `DicomInstance` - Represents a single DICOM file
- `AnalysisResult` - Stores analysis results and measurements

**DTOs (Data Transfer Objects)**
- `DicomMetadataDTO` - Cleaned metadata for frontend
- `AnalysisRequestDTO` - Analysis parameters
- `AnalysisResponseDTO` - Analysis results

### 3. Required Dependencies (pom.xml)

```xml
<!-- Core Spring Boot -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>

<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>

<!-- DICOM Processing -->
<dependency>
    <groupId>org.dcm4che</groupId>
    <artifactId>dcm4che-core</artifactId>
    <version>5.29.0</version>
</dependency>

<dependency>
    <groupId>org.dcm4che</groupId>
    <artifactId>dcm4che-imageio</artifactId>
    <version>5.29.0</version>
</dependency>

<!-- Image Processing -->
<dependency>
    <groupId>org.imgscalr</groupId>
    <artifactId>imgscalr-lib</artifactId>
    <version>4.2</version>
</dependency>

<!-- Database -->
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
</dependency>

<!-- File Upload -->
<dependency>
    <groupId>commons-io</groupId>
    <artifactId>commons-io</artifactId>
    <version>2.11.0</version>
</dependency>

<!-- Caching -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-cache</artifactId>
</dependency>

<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>

<!-- Validation -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>

<!-- Testing -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <scope>test</scope>
</dependency>
```

### 4. Configuration

**application.properties**
```properties
# Server Configuration
server.port=8080
spring.application.name=dicom-analysis

# File Upload Configuration
spring.servlet.multipart.enabled=true
spring.servlet.multipart.max-file-size=500MB
spring.servlet.multipart.max-request-size=500MB

# DICOM Storage
dicom.storage.path=/var/dicom/storage
dicom.cache.enabled=true

# Database Configuration
spring.datasource.url=jdbc:postgresql://localhost:5432/dicomdb
spring.datasource.username=dicom_user
spring.datasource.password=secure_password
spring.jpa.hibernate.ddl-auto=update

# Redis Cache
spring.redis.host=localhost
spring.redis.port=6379

# CORS Configuration
cors.allowed.origins=http://localhost:3000,http://localhost:8080
```

## Frontend Architecture (JavaScript/HTML)

### 1. Project Structure

```
src/main/resources/static/
├── index.html
├── css/
│   ├── main.css
│   ├── viewer.css
│   └── bootstrap.min.css
├── js/
│   ├── main.js
│   ├── dicom-viewer.js
│   ├── dicom-uploader.js
│   ├── analysis-display.js
│   ├── api-client.js
│   └── utils.js
├── lib/
│   ├── cornerstone-core.min.js
│   ├── cornerstone-wado-image-loader.min.js
│   ├── cornerstone-tools.min.js
│   ├── dicom-parser.min.js
│   └── axios.min.js
└── assets/
    ├── images/
    └── icons/
```

### 2. Key Components

#### 2.1 HTML Structure (index.html)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DICOM Analysis System</title>
    <!-- CSS libraries -->
</head>
<body>
    <!-- Navigation -->
    <nav id="navbar">
        <!-- Navigation menu -->
    </nav>

    <!-- Main Container -->
    <div id="app-container">
        <!-- Upload Section -->
        <section id="upload-section">
            <div id="upload-area">
                <!-- Drag & Drop upload interface -->
            </div>
        </section>

        <!-- Study List Section -->
        <section id="study-list-section">
            <div id="study-list">
                <!-- List of uploaded studies -->
            </div>
        </section>

        <!-- DICOM Viewer Section -->
        <section id="viewer-section">
            <div id="dicom-viewport">
                <!-- Cornerstone viewport for DICOM viewing -->
            </div>
            <div id="viewer-tools">
                <!-- Viewer tools (zoom, pan, window/level) -->
            </div>
        </section>

        <!-- Analysis Section -->
        <section id="analysis-section">
            <div id="analysis-controls">
                <!-- Analysis configuration -->
            </div>
            <div id="analysis-results">
                <!-- Display analysis results -->
            </div>
        </section>
    </div>

    <!-- JavaScript libraries -->
</body>
</html>
```

#### 2.2 JavaScript Modules

**api-client.js**
- REST API client using Axios or Fetch
- Handles all backend communication
- Manages authentication tokens
- Error handling and retry logic

```javascript
// Example API methods:
- uploadDicomFiles(files)
- getStudyList()
- getStudyMetadata(studyId)
- analyzeDicomStudy(studyId, parameters)
- getAnalysisResults(analysisId)
- getDicomImage(instanceId)
```

**dicom-uploader.js**
- File upload interface
- Drag and drop functionality
- Upload progress tracking
- Batch upload support
- File validation

**dicom-viewer.js**
- Initialize Cornerstone viewport
- Load and display DICOM images
- Implement viewer tools:
  - Zoom/Pan
  - Window/Level adjustment
  - Measurements (length, angle)
  - Multi-planar reconstruction (MPR)
- Image manipulation controls

**analysis-display.js**
- Display analysis results
- Generate charts and graphs
- Show image overlays
- Export results (PDF, CSV)

**main.js**
- Application initialization
- Route handling (if using SPA approach)
- Event coordination
- State management

**utils.js**
- Helper functions
- Data formatting
- Date/time utilities
- DICOM tag parsing

### 3. Required Frontend Libraries

**DICOM Viewing**
- **Cornerstone.js** - Core DICOM image rendering engine
- **Cornerstone Tools** - Interactive tools for measurements and annotations
- **Cornerstone WADO Image Loader** - Load DICOM images via WADO
- **dicom-parser** - Parse DICOM files in browser

**Alternative: OHIF Viewer**
- Complete open-source DICOM viewer
- Can be integrated as standalone component
- Provides comprehensive viewing capabilities

**UI Framework**
- **Bootstrap 5** or **Tailwind CSS** - UI components
- **jQuery** (optional) - DOM manipulation (if not using modern frameworks)

**HTTP Client**
- **Axios** - Promise-based HTTP client
- Alternative: Native Fetch API

**Charting**
- **Chart.js** - Display analysis results as charts
- **D3.js** - Advanced visualizations

**Utilities**
- **Moment.js** or **date-fns** - Date/time handling
- **Lodash** - Utility functions

### 4. Frontend-Backend Integration

#### 4.1 API Communication Flow

```
1. Upload Flow:
   User selects DICOM files
   → JavaScript captures files
   → FormData with files sent to POST /api/dicom/upload
   → Backend processes and stores files
   → Returns study metadata
   → Frontend updates study list

2. Viewing Flow:
   User selects study
   → GET /api/dicom/studies/{studyId}/series
   → Get list of series
   → GET /api/dicom/image/{instanceId} for each image
   → Cornerstone loads and displays images
   → User interacts with viewer tools

3. Analysis Flow:
   User clicks "Analyze"
   → POST /api/dicom/analyze/{studyId} with parameters
   → Backend processes images
   → Returns analysis ID (202 Accepted for async)
   → Frontend polls GET /api/dicom/analysis/{analysisId}
   → When complete, display results
```

#### 4.2 WebSocket Support (Optional Enhancement)

For real-time analysis progress updates:
```
Backend: Spring WebSocket + STOMP
Frontend: SockJS + STOMP.js

Topics:
- /topic/analysis/{analysisId}/progress
- /topic/analysis/{analysisId}/complete
```

## Data Flow

### Upload and Analysis Workflow

```
┌─────────┐
│ Browser │
└────┬────┘
     │ 1. Upload DICOM file
     ▼
┌─────────────────────┐
│ DicomUploadController│
└────┬────────────────┘
     │ 2. Process upload
     ▼
┌─────────────────────┐
│DicomParsingService  │ ◄── DCM4CHE Library
└────┬────────────────┘
     │ 3. Extract metadata
     ▼
┌─────────────────────┐
│DicomStorageService  │
└────┬────────────────┘
     │ 4. Save to file system
     │ 5. Save metadata to DB
     ▼
┌─────────────────────┐
│   Database          │
└─────────────────────┘
     │ 6. Return study ID
     ▼
┌─────────┐
│ Browser │ ◄── Display success
└─────────┘
     │ 7. Request analysis
     ▼
┌─────────────────────┐
│DicomAnalysisController│
└────┬────────────────┘
     │ 8. Start analysis
     ▼
┌─────────────────────┐
│DicomAnalysisService │
└────┬────────────────┘
     │ 9. Process image
     ▼
┌─────────────────────┐
│ImageProcessingService│
└────┬────────────────┘
     │ 10. Calculate results
     │ 11. Save results
     ▼
┌─────────────────────┐
│   Database          │
└─────────────────────┘
     │ 12. Return results
     ▼
┌─────────┐
│ Browser │ ◄── Display results
└─────────┘
```

## Security Considerations

### Backend Security
- **Authentication**: Spring Security with JWT tokens
- **Authorization**: Role-based access control (RBAC)
- **File Upload Validation**: 
  - File type validation (DICOM only)
  - File size limits
  - Malware scanning
- **CORS Configuration**: Restrict allowed origins
- **Input Validation**: Validate all API inputs
- **SQL Injection Protection**: Use parameterized queries (JPA)
- **HTTPS**: Enforce TLS for all communications
- **Rate Limiting**: Prevent API abuse

### Frontend Security
- **XSS Protection**: Sanitize user inputs
- **Content Security Policy**: Restrict resource loading
- **Secure Token Storage**: Store JWT in httpOnly cookies or secure storage
- **CSRF Protection**: Use CSRF tokens for state-changing operations

### HIPAA Compliance (if handling real patient data)
- **Data Encryption**: Encrypt data at rest and in transit
- **Audit Logging**: Log all data access
- **PHI Protection**: Remove or pseudonymize patient identifiable information
- **Access Controls**: Strict user access management
- **Data Retention**: Implement retention and deletion policies

## Deployment Architecture

### Development Environment
```
Docker Compose:
- Spring Boot Application (Port 8080)
- PostgreSQL Database (Port 5432)
- Redis Cache (Port 6379)
```

### Production Environment
```
Cloud Architecture (AWS/Azure/GCP):

┌──────────────────────────────────────────────────────┐
│                   Load Balancer                       │
│                   (AWS ALB / Azure LB)               │
└──────────────────┬───────────────────────────────────┘
                   │
      ┌────────────┴────────────┐
      │                         │
┌─────▼──────┐          ┌──────▼──────┐
│ App Server │          │ App Server  │
│  Instance  │          │  Instance   │
│ (Spring    │          │ (Spring     │
│  Boot)     │          │  Boot)      │
└─────┬──────┘          └──────┬──────┘
      │                        │
      └────────────┬────────────┘
                   │
      ┌────────────┴────────────┐
      │                         │
┌─────▼──────┐          ┌──────▼──────┐
│ PostgreSQL │          │    Redis    │
│   (RDS)    │          │  (Managed)  │
└────────────┘          └─────────────┘
      │
┌─────▼──────────────────┐
│   S3 / Blob Storage    │
│   (DICOM Files)        │
└────────────────────────┘
```

## Scalability Considerations

### Backend Scalability
- **Horizontal Scaling**: Multiple app server instances behind load balancer
- **Async Processing**: Use message queues (RabbitMQ/SQS) for long-running analysis
- **Caching**: Redis for frequently accessed metadata
- **Database Optimization**: 
  - Indexing on frequently queried fields
  - Connection pooling
  - Read replicas for read-heavy operations
- **File Storage**: 
  - Cloud object storage (S3, Azure Blob, GCS)
  - CDN for image delivery

### Frontend Optimization
- **Lazy Loading**: Load images on demand
- **Image Thumbnails**: Use thumbnails for list views
- **Progressive Loading**: Load low-quality images first
- **Client-side Caching**: Cache study metadata in browser
- **Compression**: Use GZIP compression for API responses

## Development Tools and Best Practices

### Backend Development
- **IDE**: IntelliJ IDEA or Eclipse
- **Build Tool**: Maven or Gradle
- **Code Quality**: 
  - SonarQube for code analysis
  - Checkstyle for code style
  - JUnit 5 for unit tests
  - Mockito for mocking
- **API Documentation**: Swagger/OpenAPI
- **Logging**: SLF4J with Logback
- **Monitoring**: Spring Boot Actuator + Prometheus + Grafana

### Frontend Development
- **IDE**: VS Code
- **Package Manager**: npm or yarn
- **Code Quality**:
  - ESLint for JavaScript linting
  - Prettier for code formatting
  - Jest for unit tests
- **Bundling**: Webpack or Vite (if using modern build)
- **Browser DevTools**: Chrome DevTools for debugging

## Testing Strategy

### Backend Testing
- **Unit Tests**: Test individual services and utilities
- **Integration Tests**: Test API endpoints
- **DICOM Processing Tests**: Test with sample DICOM files
- **Performance Tests**: Load testing with JMeter

### Frontend Testing
- **Unit Tests**: Test JavaScript modules
- **E2E Tests**: Selenium or Cypress for full workflow testing
- **Cross-browser Testing**: Test on Chrome, Firefox, Safari, Edge

## Alternative Architectures

### Microservices Architecture (Advanced)
Split into separate services:
- **API Gateway**: Route requests
- **Upload Service**: Handle file uploads
- **Processing Service**: DICOM parsing and analysis
- **Viewer Service**: Serve images
- **Metadata Service**: Manage study/series/instance data

### Serverless Architecture
- Use AWS Lambda or Azure Functions for processing
- API Gateway for REST endpoints
- S3/Blob Storage for DICOM files
- DynamoDB/Cosmos DB for metadata

## Getting Started - Implementation Order

1. **Phase 1: Basic Infrastructure**
   - Set up Spring Boot project with Maven/Gradle
   - Configure database and basic entities
   - Create simple REST controllers
   - Set up basic HTML/CSS/JS frontend

2. **Phase 2: DICOM Integration**
   - Integrate DCM4CHE library
   - Implement DICOM file upload
   - Parse and extract metadata
   - Store DICOM files

3. **Phase 3: Viewer Integration**
   - Integrate Cornerstone.js
   - Implement image loading
   - Add basic viewer tools
   - Connect to backend API

4. **Phase 4: Analysis Features**
   - Implement basic image analysis algorithms
   - Create analysis pipeline
   - Display analysis results
   - Add export functionality

5. **Phase 5: Enhancement**
   - Add authentication/authorization
   - Implement caching
   - Optimize performance
   - Add monitoring and logging

## Resources and Documentation

### DICOM Standards
- DICOM Standard: https://www.dicomstandard.org/
- DICOM Tags Reference: https://dicom.innolitics.com/

### Libraries Documentation
- DCM4CHE: https://github.com/dcm4che/dcm4che
- Cornerstone.js: https://cornerstonejs.org/
- OHIF Viewer: https://ohif.org/
- Spring Boot: https://spring.io/projects/spring-boot

### Sample DICOM Files
- Medical Connections: https://www.medicalconnections.co.uk/FreeNema
- TCIA (Cancer Imaging Archive): https://www.cancerimagingarchive.net/

## Conclusion

This architecture provides a solid foundation for building a DICOM image analysis system with Java Spring Boot and JavaScript/HTML. The design is modular, scalable, and follows industry best practices. Start with the basic implementation and gradually add advanced features as needed.
