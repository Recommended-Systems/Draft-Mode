# API Documentation - User Management Service

## Overview

This service provides endpoints for managing user accounts, authentication, and profiles.

## Authentication

All endpoints require authentication via Bearer token in the Authorization header.

```
Authorization: Bearer YOUR_TOKEN_HERE
```

## Endpoints

### Create User

Creates a new user account.

**Endpoint:** `POST /api/users`

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "created_at": "timestamp"
}
```

### Get User

Retreive user information by ID.

**Endpoint:** `GET /api/users/:id`

**Response:**
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "created_at": "timestamp"
}
```

### Update User

Updates user profile information.

**Endpoint:** `PUT /api/users/:id`

**Request Body:**
```json
{
  "username": "string",
  "email": "string"
}
```

### Delete User

Deletes a user account permanently.

**Endpoint:** `DELETE /api/users/:id`

**Response:**
```json
{
  "success": true
}
```

## Error Codes

- `400` - Bad Request: Invalid input data
- `401` - Unauthorized: Missing or invalid token
- `404` - Not Found: User does not exist
- `500` - Internal Server Error: Something went wrong

## Rate Limiting

API requests are limited to 100 requests per hour per user.

## Examples

### Creating a user with cURL:

```bash
curl -X POST https://api.example.com/api/users \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@example.com","password":"secret123"}'
```

## Best Practices

- Always validate input on the client side
- Store tokens securly
- Use HTTPS for all requests
- Implement proper error handling
