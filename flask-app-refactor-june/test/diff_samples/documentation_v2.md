# API Documentation - User Management Service v2.0

## Overview

This service provides comprehensive endpoints for managing user accounts, authentication, authorization, and user profiles.

**Base URL:** `https://api.example.com/v2`

## Authentication

All endpoints require authentication via Bearer token in the Authorization header:

```
Authorization: Bearer YOUR_TOKEN_HERE
```

Tokens expire after 24 hours and must be refreshed using the `/auth/refresh` endpoint.

## Rate Limiting

API requests are limited to:
- 100 requests per hour for standard users
- 1000 requests per hour for premium users
- 10000 requests per hour for enterprise customers

Rate limit information is included in response headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Time when the rate limit resets (Unix timestamp)

## Endpoints

### Create User

Creates a new user account with email verification.

**Endpoint:** `POST /api/users`

**Request Body:**
```json
{
  "username": "string (3-30 characters)",
  "email": "string (valid email format)",
  "password": "string (minimum 8 characters)",
  "full_name": "string (optional)"
}
```

**Response (201 Created):**
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "email_verified": false,
  "created_at": "timestamp"
}
```

### Get User

Retrieve detailed user information by ID.

**Endpoint:** `GET /api/users/:id`

**Response (200 OK):**
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "email_verified": "boolean",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Update User

Updates user profile information. Only provided fields will be updated.

**Endpoint:** `PATCH /api/users/:id`

**Request Body:**
```json
{
  "username": "string (optional)",
  "email": "string (optional)",
  "full_name": "string (optional)"
}
```

**Response (200 OK):**
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "updated_at": "timestamp"
}
```

### Delete User

Permanently deletes a user account. This action cannot be undone.

**Endpoint:** `DELETE /api/users/:id`

**Response (204 No Content):**
```json
{}
```

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object (optional)"
  }
}
```

### HTTP Status Codes

- `400` - Bad Request: Invalid or missing input data
- `401` - Unauthorized: Missing or invalid authentication token
- `403` - Forbidden: Authenticated but not authorized for this action
- `404` - Not Found: Requested user does not exist
- `429` - Too Many Requests: Rate limit exceeded
- `500` - Internal Server Error: Something went wrong on our end

## Examples

### Creating a user with cURL:

```bash
curl -X POST https://api.example.com/v2/api/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

### Updating a user with Python:

```python
import requests

headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
}

data = {
    "full_name": "John Smith"
}

response = requests.patch(
    "https://api.example.com/v2/api/users/123",
    headers=headers,
    json=data
)

print(response.json())
```

## Best Practices

- Always use HTTPS for all API requests
- Validate input on both client and server side
- Store tokens securely (never in local storage for web apps)
- Implement proper error handling and retry logic with exponential backoff
- Cache responses when appropriate to reduce API calls
- Use webhook notifications instead of polling when possible

## Changelog

### Version 2.0 (Current)
- Changed Update endpoint from PUT to PATCH
- Added full_name field to user model
- Added email_verified status
- Improved rate limiting with tiered access
- Enhanced error response format
