# DICOM Analysis System - API Specification

## Base URL
```
http://localhost:8080/api
```

## Authentication
All endpoints require JWT token authentication (except health checks).
Include token in Authorization header:
```
Authorization: Bearer <token>
```

## REST API Endpoints

### 1. DICOM File Upload

#### Upload Single DICOM File
```
POST /api/dicom/upload
```

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with file

**Request Example:**
```bash
curl -X POST http://localhost:8080/api/dicom/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/dicom/file.dcm"
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "DICOM file uploaded successfully",
  "data": {
    "instanceId": "1.2.840.113619.2.55.3.123456789",
    "studyId": "1.2.840.113619.2.55.3.123456",
    "seriesId": "1.2.840.113619.2.55.3.123456.1",
    "patientName": "DOE^JOHN",
    "studyDate": "2024-01-15",
    "modality": "CT",
    "fileName": "file.dcm",
    "fileSize": 524288,
    "uploadTimestamp": "2024-01-15T10:30:00Z"
  }
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "message": "Invalid DICOM file",
  "error": "File is not a valid DICOM format"
}
```

#### Upload Multiple DICOM Files
```
POST /api/dicom/upload/multiple
```

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with multiple files

**Response (200 OK):**
```json
{
  "success": true,
  "message": "3 files uploaded successfully",
  "data": {
    "totalFiles": 3,
    "successfulUploads": 3,
    "failedUploads": 0,
    "studies": [
      {
        "studyId": "1.2.840.113619.2.55.3.123456",
        "instanceCount": 3
      }
    ]
  }
}
```

### 2. Study Management

#### List All Studies
```
GET /api/dicom/studies
```

**Query Parameters:**
- `page` (optional): Page number (default: 0)
- `size` (optional): Page size (default: 20)
- `sortBy` (optional): Sort field (default: studyDate)
- `sortOrder` (optional): asc or desc (default: desc)
- `patientName` (optional): Filter by patient name
- `studyDate` (optional): Filter by study date (YYYY-MM-DD)
- `modality` (optional): Filter by modality

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "studies": [
      {
        "studyId": "1.2.840.113619.2.55.3.123456",
        "studyInstanceUID": "1.2.840.113619.2.55.3.123456",
        "patientId": "P12345",
        "patientName": "DOE^JOHN",
        "patientBirthDate": "1980-05-15",
        "patientSex": "M",
        "studyDate": "2024-01-15",
        "studyTime": "103000",
        "studyDescription": "CT Chest",
        "modalities": ["CT"],
        "numberOfSeries": 3,
        "numberOfInstances": 150,
        "uploadDate": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "currentPage": 0,
      "pageSize": 20,
      "totalPages": 5,
      "totalElements": 100
    }
  }
}
```

#### Get Study Details
```
GET /api/dicom/studies/{studyId}
```

**Path Parameters:**
- `studyId`: Study Instance UID or database ID

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "studyId": "1.2.840.113619.2.55.3.123456",
    "studyInstanceUID": "1.2.840.113619.2.55.3.123456",
    "patientId": "P12345",
    "patientName": "DOE^JOHN",
    "patientBirthDate": "1980-05-15",
    "patientSex": "M",
    "studyDate": "2024-01-15",
    "studyTime": "103000",
    "studyDescription": "CT Chest",
    "referringPhysicianName": "SMITH^JANE",
    "accessionNumber": "ACC12345",
    "numberOfSeries": 3,
    "numberOfInstances": 150,
    "series": [
      {
        "seriesId": "1.2.840.113619.2.55.3.123456.1",
        "seriesInstanceUID": "1.2.840.113619.2.55.3.123456.1",
        "seriesNumber": 1,
        "modality": "CT",
        "seriesDescription": "Chest Axial",
        "numberOfInstances": 50,
        "bodyPartExamined": "CHEST"
      }
    ]
  }
}
```

#### Get Series in Study
```
GET /api/dicom/studies/{studyId}/series
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "series": [
      {
        "seriesId": "1.2.840.113619.2.55.3.123456.1",
        "seriesInstanceUID": "1.2.840.113619.2.55.3.123456.1",
        "seriesNumber": 1,
        "modality": "CT",
        "seriesDescription": "Chest Axial",
        "numberOfInstances": 50,
        "bodyPartExamined": "CHEST",
        "sliceThickness": "5.0",
        "instances": [
          {
            "instanceId": "1.2.840.113619.2.55.3.123456789",
            "sopInstanceUID": "1.2.840.113619.2.55.3.123456789",
            "instanceNumber": 1,
            "rows": 512,
            "columns": 512,
            "bitsAllocated": 16,
            "thumbnailUrl": "/api/dicom/thumbnail/1.2.840.113619.2.55.3.123456789"
          }
        ]
      }
    ]
  }
}
```

#### Get Instances in Series
```
GET /api/dicom/studies/{studyId}/series/{seriesId}/instances
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "instances": [
      {
        "instanceId": "1.2.840.113619.2.55.3.123456789",
        "sopInstanceUID": "1.2.840.113619.2.55.3.123456789",
        "instanceNumber": 1,
        "rows": 512,
        "columns": 512,
        "bitsAllocated": 16,
        "pixelSpacing": "0.5\\0.5",
        "sliceLocation": "100.0",
        "imagePosition": "-250.0\\-250.0\\100.0",
        "imageOrientation": "1\\0\\0\\0\\1\\0"
      }
    ]
  }
}
```

### 3. DICOM Metadata

#### Get DICOM Metadata
```
GET /api/dicom/metadata/{instanceId}
```

**Path Parameters:**
- `instanceId`: SOP Instance UID or database ID

**Query Parameters:**
- `format` (optional): json or dicom (default: json)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "instanceId": "1.2.840.113619.2.55.3.123456789",
    "patientInfo": {
      "patientName": "DOE^JOHN",
      "patientId": "P12345",
      "patientBirthDate": "1980-05-15",
      "patientSex": "M",
      "patientAge": "043Y"
    },
    "studyInfo": {
      "studyInstanceUID": "1.2.840.113619.2.55.3.123456",
      "studyDate": "2024-01-15",
      "studyTime": "103000",
      "studyDescription": "CT Chest",
      "accessionNumber": "ACC12345"
    },
    "seriesInfo": {
      "seriesInstanceUID": "1.2.840.113619.2.55.3.123456.1",
      "seriesNumber": 1,
      "modality": "CT",
      "seriesDescription": "Chest Axial",
      "bodyPartExamined": "CHEST"
    },
    "imageInfo": {
      "sopInstanceUID": "1.2.840.113619.2.55.3.123456789",
      "sopClassUID": "1.2.840.10008.5.1.4.1.1.2",
      "instanceNumber": 1,
      "rows": 512,
      "columns": 512,
      "bitsAllocated": 16,
      "bitsStored": 12,
      "photometricInterpretation": "MONOCHROME2",
      "samplesPerPixel": 1,
      "pixelSpacing": "0.5\\0.5",
      "sliceThickness": "5.0",
      "windowCenter": "40",
      "windowWidth": "400"
    },
    "equipmentInfo": {
      "manufacturer": "GE MEDICAL SYSTEMS",
      "manufacturerModelName": "LightSpeed VCT",
      "stationName": "CT01",
      "softwareVersions": "1.0"
    }
  }
}
```

### 4. Image Retrieval

#### Get DICOM Image
```
GET /api/dicom/image/{instanceId}
```

**Query Parameters:**
- `format` (optional): dicom, png, jpeg (default: dicom)
- `windowCenter` (optional): Window center for display
- `windowWidth` (optional): Window width for display
- `quality` (optional): JPEG quality 1-100 (default: 90)

**Response (200 OK):**
- Content-Type: `application/dicom`, `image/png`, or `image/jpeg`
- Body: Binary image data

**Request Example:**
```bash
curl -X GET "http://localhost:8080/api/dicom/image/1.2.840.113619.2.55.3.123456789?format=png&windowCenter=40&windowWidth=400" \
  -H "Authorization: Bearer <token>" \
  --output image.png
```

#### Get Thumbnail
```
GET /api/dicom/thumbnail/{instanceId}
```

**Query Parameters:**
- `size` (optional): Thumbnail size (default: 128)

**Response (200 OK):**
- Content-Type: `image/jpeg`
- Body: Binary thumbnail data

### 5. DICOM Analysis

#### Start Analysis
```
POST /api/dicom/analyze/{studyId}
```

**Path Parameters:**
- `studyId`: Study Instance UID or database ID

**Request Body:**
```json
{
  "analysisType": "basic_stats",
  "parameters": {
    "includeHistogram": true,
    "calculateHU": true,
    "regionOfInterest": {
      "x": 100,
      "y": 100,
      "width": 50,
      "height": 50
    }
  }
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Analysis started",
  "data": {
    "analysisId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "PROCESSING",
    "startTime": "2024-01-15T10:35:00Z",
    "estimatedCompletionTime": "2024-01-15T10:40:00Z"
  }
}
```

#### Get Analysis Status
```
GET /api/dicom/analysis/{analysisId}
```

**Response (200 OK) - Processing:**
```json
{
  "success": true,
  "data": {
    "analysisId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "PROCESSING",
    "progress": 45,
    "startTime": "2024-01-15T10:35:00Z",
    "currentStep": "Calculating statistics"
  }
}
```

**Response (200 OK) - Completed:**
```json
{
  "success": true,
  "data": {
    "analysisId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "COMPLETED",
    "progress": 100,
    "startTime": "2024-01-15T10:35:00Z",
    "completionTime": "2024-01-15T10:38:00Z",
    "results": {
      "statistics": {
        "mean": 120.5,
        "median": 115.0,
        "stdDev": 45.2,
        "min": -1024,
        "max": 3071,
        "histogram": {
          "bins": [0, 10, 20, 30, 40, 50],
          "counts": [1500, 3000, 4500, 3500, 2000, 1000]
        }
      },
      "huStatistics": {
        "meanHU": -850.5,
        "minHU": -1024,
        "maxHU": 3071
      },
      "regionOfInterest": {
        "area": 2500,
        "mean": 125.3,
        "stdDev": 15.5
      }
    }
  }
}
```

#### Get Analysis Report
```
GET /api/dicom/analysis/{analysisId}/report
```

**Query Parameters:**
- `format` (optional): json, pdf, csv (default: json)

**Response (200 OK):**
- Content-Type: `application/json`, `application/pdf`, or `text/csv`
- Body: Report data

### 6. Health and Status

#### Health Check
```
GET /api/health
```

**Response (200 OK):**
```json
{
  "status": "UP",
  "components": {
    "database": {
      "status": "UP"
    },
    "diskSpace": {
      "status": "UP",
      "details": {
        "total": 500000000000,
        "free": 250000000000,
        "threshold": 10485760
      }
    },
    "redis": {
      "status": "UP"
    }
  }
}
```

#### System Info
```
GET /api/info
```

**Response (200 OK):**
```json
{
  "application": {
    "name": "DICOM Analysis System",
    "version": "1.0.0",
    "description": "DICOM image analysis and viewing system"
  },
  "statistics": {
    "totalStudies": 150,
    "totalSeries": 450,
    "totalInstances": 15000,
    "storageUsed": "25 GB"
  }
}
```

## Error Responses

### Standard Error Format
```json
{
  "success": false,
  "message": "Error description",
  "error": "Detailed error message",
  "timestamp": "2024-01-15T10:35:00Z",
  "path": "/api/dicom/upload"
}
```

### HTTP Status Codes

- **200 OK**: Request succeeded
- **201 Created**: Resource created successfully
- **202 Accepted**: Request accepted for processing
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource already exists
- **413 Payload Too Large**: File size exceeds limit
- **415 Unsupported Media Type**: Invalid file format
- **422 Unprocessable Entity**: Invalid DICOM file
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily unavailable

## Rate Limiting

API requests are limited to:
- **100 requests per minute** for standard endpoints
- **10 requests per minute** for upload endpoints
- **50 requests per minute** for analysis endpoints

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 75
X-RateLimit-Reset: 1642248000
```

## Pagination

Endpoints that return lists support pagination:

**Query Parameters:**
- `page`: Page number (0-based)
- `size`: Items per page (max 100)
- `sort`: Sort field and direction (e.g., `studyDate,desc`)

**Response Pagination Info:**
```json
{
  "pagination": {
    "currentPage": 0,
    "pageSize": 20,
    "totalPages": 5,
    "totalElements": 100,
    "first": true,
    "last": false
  }
}
```

## WebSocket Endpoints (Optional)

For real-time updates:

### Connect to WebSocket
```
ws://localhost:8080/ws
```

### Subscribe to Analysis Progress
```
STOMP SUBSCRIBE
destination: /topic/analysis/{analysisId}/progress
```

**Progress Messages:**
```json
{
  "analysisId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "progress": 45,
  "currentStep": "Calculating statistics",
  "timestamp": "2024-01-15T10:36:00Z"
}
```

### Subscribe to Analysis Completion
```
STOMP SUBSCRIBE
destination: /topic/analysis/{analysisId}/complete
```

**Completion Message:**
```json
{
  "analysisId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "COMPLETED",
  "timestamp": "2024-01-15T10:38:00Z"
}
```

## API Versioning

The API uses URL versioning:
```
/api/v1/dicom/upload
/api/v2/dicom/upload
```

Current version is v1 (default, can omit version number).

## CORS Configuration

Allowed origins for CORS:
- `http://localhost:3000` (development)
- `http://localhost:8080` (same origin)
- Production domain (configure in properties)

Allowed methods:
- GET, POST, PUT, DELETE, OPTIONS

## Content Types

**Request Content Types:**
- `application/json` - JSON data
- `multipart/form-data` - File uploads

**Response Content Types:**
- `application/json` - JSON responses
- `application/dicom` - DICOM files
- `image/png` - PNG images
- `image/jpeg` - JPEG images
- `application/pdf` - PDF reports
- `text/csv` - CSV exports

## Security Headers

All responses include security headers:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

## Best Practices

1. **Always authenticate**: Include JWT token in Authorization header
2. **Handle errors**: Check response status and error messages
3. **Use pagination**: For large result sets
4. **Cache responses**: Cache metadata when appropriate
5. **Compress requests**: Use gzip compression for large payloads
6. **Use appropriate formats**: Request images in web-friendly formats (PNG/JPEG) for display
7. **Monitor rate limits**: Check rate limit headers and implement backoff
8. **Use WebSocket**: For real-time updates on long-running operations
