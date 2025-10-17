# DICOM Analysis System - Quick Start Guide

## Overview
This guide provides a quick reference for getting started with the DICOM Analysis System based on the architecture document.

## Prerequisites

### Backend Development
- Java 17 or higher
- Maven 3.6+ or Gradle 7+
- PostgreSQL 13+
- Redis (optional, for caching)
- IDE (IntelliJ IDEA, Eclipse, or VS Code with Java extensions)

### Frontend Development
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Text editor or IDE (VS Code recommended)
- Basic knowledge of HTML, CSS, and JavaScript

## Project Initialization Steps

### 1. Create Spring Boot Project

Use Spring Initializr (https://start.spring.io/) with the following configuration:

**Project Settings:**
- Project: Maven
- Language: Java
- Spring Boot: 3.2.x (latest stable)
- Java Version: 17
- Packaging: Jar

**Dependencies:**
- Spring Web
- Spring Data JPA
- PostgreSQL Driver
- Validation
- Spring Boot DevTools

**Project Metadata:**
- Group: com.yourcompany
- Artifact: dicom-analysis
- Name: DicomAnalysis
- Package name: com.yourcompany.dicomanalysis

### 2. Add DICOM Dependencies to pom.xml

```xml
<!-- DCM4CHE for DICOM processing -->
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

<!-- Apache Commons for file operations -->
<dependency>
    <groupId>commons-io</groupId>
    <artifactId>commons-io</artifactId>
    <version>2.11.0</version>
</dependency>
```

### 3. Configure Application Properties

Create `src/main/resources/application.properties`:

```properties
# Application
spring.application.name=dicom-analysis
server.port=8080

# File Upload
spring.servlet.multipart.enabled=true
spring.servlet.multipart.max-file-size=500MB
spring.servlet.multipart.max-request-size=500MB

# Database
spring.datasource.url=jdbc:postgresql://localhost:5432/dicomdb
spring.datasource.username=dicom_user
spring.datasource.password=change_me
spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=true

# DICOM Storage
dicom.storage.path=./dicom-storage
```

### 4. Set Up Database

```sql
-- Create PostgreSQL database
CREATE DATABASE dicomdb;

-- Create user
CREATE USER dicom_user WITH PASSWORD 'change_me';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE dicomdb TO dicom_user;
```

### 5. Create Basic Package Structure

```
src/main/java/com/yourcompany/dicomanalysis/
├── DicomAnalysisApplication.java
├── config/
├── controller/
├── service/
├── repository/
├── model/
│   ├── entity/
│   └── dto/
├── exception/
└── util/
```

### 6. Set Up Frontend Files

Create the following structure in `src/main/resources/static/`:

```
static/
├── index.html
├── css/
│   └── main.css
├── js/
│   ├── main.js
│   ├── api-client.js
│   └── dicom-viewer.js
└── lib/
    └── (download libraries here)
```

### 7. Download Frontend Libraries

Required libraries to download and place in `static/lib/`:

1. **Cornerstone.js** (DICOM viewing)
   - Download from: https://github.com/cornerstonejs/cornerstone
   - Files: cornerstone-core.min.js

2. **dicom-parser** (DICOM parsing)
   - Download from: https://github.com/cornerstonejs/dicomParser
   - Files: dicomParser.min.js

3. **Cornerstone WADO Image Loader**
   - Download from: https://github.com/cornerstonejs/cornerstoneWADOImageLoader
   - Files: cornerstoneWADOImageLoader.min.js

4. **Axios** (HTTP client)
   - Download from: https://github.com/axios/axios
   - Files: axios.min.js

Or use CDN links in your HTML:
```html
<script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
<script src="https://unpkg.com/cornerstone-core@2.6.1/dist/cornerstone.min.js"></script>
<script src="https://unpkg.com/dicom-parser@1.8.13/dist/dicomParser.min.js"></script>
<script src="https://unpkg.com/cornerstone-wado-image-loader@4.1.1/dist/cornerstoneWADOImageLoader.bundle.min.js"></script>
```

## Basic Implementation Checklist

### Backend (Spring Boot)

- [ ] Create main application class with `@SpringBootApplication`
- [ ] Create `DicomUploadController` with file upload endpoint
- [ ] Create `DicomParsingService` to read DICOM files with DCM4CHE
- [ ] Create `DicomStorageService` to save files to disk
- [ ] Create entity classes (DicomStudy, DicomSeries, DicomInstance)
- [ ] Create repository interfaces extending JpaRepository
- [ ] Implement basic exception handling
- [ ] Test with Postman or curl

### Frontend (HTML/JavaScript)

- [ ] Create basic HTML structure with upload form
- [ ] Create CSS for styling
- [ ] Implement file upload with FormData
- [ ] Create API client using Axios or Fetch
- [ ] Initialize Cornerstone viewport
- [ ] Load and display DICOM images
- [ ] Add basic viewer controls (zoom, pan)
- [ ] Test in browser

## Testing the System

### 1. Get Sample DICOM Files
Download free DICOM samples from:
- https://www.rubomedical.com/dicom_files/
- https://barre.dev/medical/samples/

### 2. Run the Application
```bash
# Start PostgreSQL
# Start Redis (if using)

# Run Spring Boot
mvn spring-boot:run

# Or if using Gradle
gradle bootRun
```

### 3. Access the Application
- Frontend: http://localhost:8080/
- API docs (if Swagger added): http://localhost:8080/swagger-ui.html

### 4. Test Upload
1. Open browser to http://localhost:8080/
2. Select a DICOM file
3. Click upload
4. Verify file is saved and metadata is extracted

### 5. Test Viewing
1. Select uploaded study
2. Verify image displays in Cornerstone viewer
3. Test zoom, pan, and window/level controls

## Common REST API Endpoints

```
POST   /api/dicom/upload                  - Upload DICOM file
GET    /api/dicom/studies                 - List all studies
GET    /api/dicom/studies/{id}            - Get study details
GET    /api/dicom/studies/{id}/series     - Get series in study
GET    /api/dicom/metadata/{instanceId}   - Get DICOM metadata
GET    /api/dicom/image/{instanceId}      - Get DICOM image
POST   /api/dicom/analyze/{studyId}       - Analyze study
GET    /api/dicom/analysis/{analysisId}   - Get analysis results
```

## Docker Setup (Optional)

### docker-compose.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: dicomdb
      POSTGRES_USER: dicom_user
      POSTGRES_PASSWORD: change_me
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/dicomdb
      SPRING_REDIS_HOST: redis
    depends_on:
      - postgres
      - redis
    volumes:
      - ./dicom-storage:/app/dicom-storage

volumes:
  postgres-data:
```

### Dockerfile
```dockerfile
FROM eclipse-temurin:17-jdk-alpine
WORKDIR /app
COPY target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

## Development Workflow

1. **Start Database**: Ensure PostgreSQL is running
2. **Run Backend**: Start Spring Boot application
3. **Open Browser**: Navigate to http://localhost:8080/
4. **Upload DICOM**: Test file upload functionality
5. **View Images**: Test DICOM viewer
6. **Run Analysis**: Test analysis functionality
7. **Check Logs**: Monitor console for errors
8. **Iterate**: Make changes and refresh browser

## Troubleshooting

### Backend Issues

**Problem**: Cannot connect to database
- **Solution**: Check PostgreSQL is running and credentials are correct

**Problem**: File upload fails
- **Solution**: Check `spring.servlet.multipart.max-file-size` setting

**Problem**: Out of memory
- **Solution**: Increase JVM heap size: `java -Xmx2G -jar app.jar`

### Frontend Issues

**Problem**: CORS errors
- **Solution**: Add CORS configuration in Spring Boot

**Problem**: Images not loading
- **Solution**: Check browser console for errors, verify API endpoints

**Problem**: Cornerstone not working
- **Solution**: Ensure all libraries are loaded in correct order

## Next Steps

After basic setup:

1. **Add Authentication**: Implement Spring Security with JWT
2. **Implement Analysis**: Add image processing algorithms
3. **Add Charts**: Use Chart.js to display analysis results
4. **Optimize Performance**: Add caching and async processing
5. **Add Tests**: Write unit and integration tests
6. **Deploy**: Deploy to cloud (AWS, Azure, GCP)

## Resources

- **Full Architecture**: See ARCHITECTURE.md
- **Spring Boot Docs**: https://spring.io/projects/spring-boot
- **DCM4CHE Docs**: https://github.com/dcm4che/dcm4che
- **Cornerstone Docs**: https://cornerstonejs.org/
- **DICOM Standard**: https://www.dicomstandard.org/

## Support

For questions or issues:
1. Check the ARCHITECTURE.md document
2. Review Spring Boot and DCM4CHE documentation
3. Search Stack Overflow for similar issues
4. Open an issue in the project repository
