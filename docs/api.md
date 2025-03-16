 # RecruitX API Documentation

## Overview
The RecruitX API provides programmatic access to the recruitment matching system. It follows RESTful principles and uses JWT for authentication.

## Base URL
```
https://api.recruitx.io/v1
```

## Authentication
All API requests require authentication using JWT tokens.

### Headers
```http
Authorization: Bearer <your_jwt_token>
```

### Rate Limiting
- 100 requests per minute per API key
- 1000 requests per hour per API key
- Status codes:
  - 429: Rate limit exceeded
  - 403: Invalid/expired token

## Endpoints

### Resume Matching
Match a resume against a job description.

```http
POST /match
Content-Type: multipart/form-data
```

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| resume | File | Yes | Resume file (PDF/DOCX) |
| job_description | File | Yes | Job description file |
| threshold | float | No | Minimum match score (0-1) |

#### Response
```json
{
  "match_id": "m123456",
  "score": 0.85,
  "insights": {
    "skills_match": 0.9,
    "experience_match": 0.8,
    "education_match": 0.85
  },
  "recommendations": [
    "Candidate has strong technical skills",
    "Additional project management experience recommended"
  ]
}
```

### Batch Processing
Process multiple resumes against multiple job descriptions.

```http
POST /match/batch
Content-Type: multipart/form-data
```

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| resumes[] | File[] | Yes | Array of resume files |
| jobs[] | File[] | Yes | Array of job descriptions |
| config | JSON | No | Processing configuration |

#### Response
```json
{
  "batch_id": "b789012",
  "matches": [
    {
      "resume_id": "r1",
      "job_id": "j1",
      "score": 0.75
    }
  ],
  "status": "completed",
  "timestamp": "2024-04-10T15:30:00Z"
}
```

### Analytics
Retrieve matching analytics and insights.

```http
GET /analytics
```

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| start_date | string | No | Start date (ISO 8601) |
| end_date | string | No | End date (ISO 8601) |
| metrics | string[] | No | Specific metrics to retrieve |

#### Response
```json
{
  "period": {
    "start": "2024-04-01T00:00:00Z",
    "end": "2024-04-10T23:59:59Z"
  },
  "metrics": {
    "total_matches": 150,
    "average_score": 0.82,
    "processing_time": "1.2s"
  },
  "trends": {
    "daily_matches": [...],
    "score_distribution": [...]
  }
}
```

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "invalid_file_format",
    "message": "Unsupported file format. Please upload PDF or DOCX.",
    "details": {
      "allowed_formats": ["pdf", "docx"],
      "received_format": "txt"
    }
  }
}
```

### Common Error Codes
| Code | Description |
|------|-------------|
| invalid_token | Authentication token is invalid or expired |
| rate_limit_exceeded | API rate limit has been exceeded |
| invalid_file_format | Unsupported file format |
| processing_error | Error processing the request |
| invalid_parameters | Invalid request parameters |

## Webhooks
RecruitX can send webhook notifications for asynchronous operations.

### Configuration
```http
POST /webhooks/configure
```

```json
{
  "url": "https://your-domain.com/webhook",
  "events": ["match.completed", "batch.completed"],
  "secret": "your_webhook_secret"
}
```

### Event Types
| Event | Description |
|-------|-------------|
| match.completed | Single match processing completed |
| batch.completed | Batch processing completed |
| error.occurred | Processing error occurred |

### Webhook Payload
```json
{
  "event": "match.completed",
  "timestamp": "2024-04-10T15:30:00Z",
  "data": {
    "match_id": "m123456",
    "score": 0.85
  }
}
```

## SDKs and Libraries
Official SDKs are available for:
- Python
- JavaScript/TypeScript
- Java
- Go

### Python Example
```python
from recruitx import RecruitX

# Initialize client
rx = RecruitX(api_key="your_api_key")

# Match resume
result = rx.match_resume(
    resume_path="resume.pdf",
    job_description_path="job.pdf"
)

print(f"Match score: {result.score}")
```

### JavaScript Example
```javascript
import { RecruitX } from '@recruitx/sdk';

// Initialize client
const rx = new RecruitX({ apiKey: 'your_api_key' });

// Match resume
const result = await rx.matchResume({
  resume: resumeFile,
  jobDescription: jobFile
});

console.log(`Match score: ${result.score}`);
```

## Best Practices

### Performance
1. Use batch processing for multiple matches
2. Implement caching for frequent requests
3. Compress files before upload
4. Use webhook notifications for async operations

### Security
1. Rotate API keys regularly
2. Use HTTPS for all requests
3. Validate webhook signatures
4. Implement request timeouts

### Error Handling
1. Implement exponential backoff
2. Handle rate limiting gracefully
3. Log all API errors
4. Validate input before sending

## Support
- Documentation: https://docs.recruitx.io
- API Status: https://status.recruitx.io
- Support Email: api@recruitx.io
- GitHub Issues: https://github.com/recruitx/api/issues

## Changelog

### v1.3.0 (2024-04-10)
- Added batch processing endpoint
- Improved error handling
- Enhanced analytics metrics
- Added webhook support

### v1.2.0 (2024-03-15)
- Added rate limiting headers
- Improved authentication
- Enhanced error responses
- Added SDK support

### v1.1.0 (2024-02-20)
- Added analytics endpoint
- Improved matching algorithm
- Enhanced documentation
- Bug fixes

### v1.0.0 (2024-01-15)
- Initial API release
- Basic matching functionality
- Authentication system
- Error handling