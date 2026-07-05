# Internal Platform API Reference

## Overview

The Internal Platform API provides RESTful endpoints for managing users, projects, and billing across all internal services. All endpoints require Bearer token authentication.

**Base URL:** `https://api.internal.acmecorp.com/v2`

**Rate Limits:** 1,000 requests/minute per API key for standard tier, 10,000/minute for enterprise tier.

## Authentication

### Obtaining an API Key

Request an API key through the Developer Portal at `https://devportal.internal.acmecorp.com`. Keys are scoped to specific services:

- `user:read` — Read user profiles and preferences
- `user:write` — Create and update user records
- `project:admin` — Full project management access
- `billing:read` — View invoices and usage
- `billing:write` — Create charges, issue refunds

### Token Format

All requests must include the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

Tokens expire after 3600 seconds (1 hour). Use the `/auth/refresh` endpoint to obtain a new token before expiry.

## Users API

### GET /users

List all users with pagination.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number (1-indexed) |
| per_page | integer | No | 25 | Items per page (max 100) |
| department | string | No | — | Filter by department slug |
| status | string | No | active | Filter: active, inactive, suspended |
| sort | string | No | created_at | Sort field: name, email, created_at |
| order | string | No | desc | Sort order: asc, desc |

**Response:**

```json
{
  "data": [
    {
      "id": "usr_a1b2c3d4",
      "email": "nguyen.van.a@acmecorp.com",
      "name": "Nguyen Van A",
      "department": "engineering",
      "role": "senior_engineer",
      "status": "active",
      "created_at": "2024-01-15T08:30:00Z",
      "last_login": "2025-06-28T14:22:00Z",
      "permissions": ["user:read", "project:admin"]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 487,
    "total_pages": 20
  }
}
```

### GET /users/:id

Retrieve a single user by ID.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | User ID (format: `usr_[a-z0-9]{8}`) |

**Response:** Same as individual user object above.

**Error Responses:**

```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "No user found with ID usr_invalid123",
    "status": 404
  }
}
```

### POST /users

Create a new user. Requires `user:write` scope.

**Request Body:**

```json
{
  "email": "new.user@acmecorp.com",
  "name": "New User",
  "department": "finance",
  "role": "analyst",
  "send_welcome_email": true
}
```

**Validation Rules:**
- `email`: Must be a valid `@acmecorp.com` address, unique across all users
- `name`: 2-100 characters, Unicode supported
- `department`: Must match an existing department slug
- `role`: Must be a valid role within the specified department

**Response (201 Created):**

```json
{
  "data": {
    "id": "usr_x7y8z9w0",
    "email": "new.user@acmecorp.com",
    "name": "New User",
    "department": "finance",
    "role": "analyst",
    "status": "pending_verification",
    "created_at": "2025-07-01T10:00:00Z"
  }
}
```

### PATCH /users/:id

Update user fields. Only provided fields are updated (partial update).

```json
{
  "department": "engineering",
  "role": "tech_lead"
}
```

### DELETE /users/:id

Soft-delete a user. Sets status to `inactive` and revokes all API keys. The user record is retained for 90 days before permanent deletion per data retention policy.

## Projects API

### GET /projects

List projects the authenticated user has access to.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| status | string | No | active | Filter: active, archived, draft |
| owner_id | string | No | — | Filter by project owner |
| tag | string | No | — | Filter by tag (comma-separated for multiple) |

**Response:**

```json
{
  "data": [
    {
      "id": "prj_m1n2o3p4",
      "name": "Customer Analytics Pipeline",
      "description": "ETL pipeline for customer behavior analytics",
      "owner": {
        "id": "usr_a1b2c3d4",
        "name": "Nguyen Van A"
      },
      "status": "active",
      "tags": ["data-pipeline", "analytics", "production"],
      "created_at": "2024-06-01T00:00:00Z",
      "updated_at": "2025-06-15T16:30:00Z",
      "members_count": 8,
      "budget_allocated": 150000000,
      "budget_used": 89000000
    }
  ]
}
```

### POST /projects

Create a new project. The authenticated user becomes the owner.

**Request Body:**

```json
{
  "name": "New ML Model Serving",
  "description": "Deploy ML models with auto-scaling inference endpoints",
  "tags": ["ml", "infrastructure"],
  "budget_allocated": 200000000,
  "members": ["usr_a1b2c3d4", "usr_e5f6g7h8"]
}
```

### PUT /projects/:id/members

Replace the entire member list for a project.

### POST /projects/:id/archive

Archive a project. Archived projects retain data but stop all scheduled jobs and revoke member access.

## Billing API

### GET /billing/invoices

List invoices for the authenticated organization.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| from | date | No | Start date (ISO 8601) |
| to | date | No | End date (ISO 8601) |
| status | string | No | Filter: paid, pending, overdue |

**Response:**

```json
{
  "data": [
    {
      "id": "inv_q1r2s3t4",
      "period": "2025-06",
      "amount": 45000000,
      "currency": "VND",
      "status": "paid",
      "line_items": [
        {
          "service": "compute",
          "description": "GPU instances (A100 x 4, 720 hours)",
          "amount": 32000000
        },
        {
          "service": "storage",
          "description": "Object storage (2.4 TB)",
          "amount": 8000000
        },
        {
          "service": "network",
          "description": "Data transfer (850 GB egress)",
          "amount": 5000000
        }
      ],
      "issued_at": "2025-07-01T00:00:00Z",
      "due_date": "2025-07-31T23:59:59Z",
      "paid_at": "2025-07-15T09:30:00Z"
    }
  ]
}
```

### GET /billing/usage

Real-time usage metrics for the current billing period.

**Response:**

```json
{
  "period": "2025-07",
  "services": {
    "compute": {
      "gpu_hours": 340,
      "cpu_hours": 12500,
      "estimated_cost": 28000000
    },
    "storage": {
      "total_gb": 2800,
      "estimated_cost": 9200000
    },
    "api_calls": {
      "total": 4500000,
      "estimated_cost": 2250000
    }
  },
  "total_estimated": 39450000,
  "budget_remaining": 110550000
}
```

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "status": 400,
    "details": {}
  }
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| UNAUTHORIZED | 401 | Missing or invalid authentication token |
| FORBIDDEN | 403 | Valid token but insufficient permissions |
| NOT_FOUND | 404 | Resource does not exist |
| VALIDATION_ERROR | 422 | Request body validation failed |
| RATE_LIMITED | 429 | Too many requests, retry after `Retry-After` header |
| INTERNAL_ERROR | 500 | Server error, contact platform team |

## Webhooks

Configure webhooks to receive real-time notifications about events.

### Supported Events

- `user.created` — New user registered
- `user.deactivated` — User account deactivated
- `project.created` — New project created
- `project.archived` — Project archived
- `billing.invoice.created` — New invoice generated
- `billing.payment.received` — Payment processed

### Webhook Payload

```json
{
  "event": "user.created",
  "timestamp": "2025-07-01T10:00:00Z",
  "data": {
    "id": "usr_x7y8z9w0",
    "email": "new.user@acmecorp.com"
  },
  "signature": "sha256=a1b2c3d4e5f6..."
}
```

Verify webhook signatures using HMAC-SHA256 with your webhook secret. Reject any payload where the computed signature does not match the `signature` field.
