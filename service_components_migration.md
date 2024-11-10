# Service Connection Components Migration Guide

This document outlines the key components for migrating service connection and authentication code from the Flask-based implementation to FastAPI.

## Core Database Models

### Service Connection Models (`repopal/models/service_connection.py`)
- Contains essential models:
  - `ServiceConnection`: Core connection details
  - `Repository`: Repository information
  - `ServiceCredential`: Encrypted credential storage
- Minimal changes needed for FastAPI, mainly SQLAlchemy syntax updates

## Service Management

### Service Manager (`repopal/core/service_manager.py`)
- `ServiceConnectionManager` class handles:
  - Connection lifecycle management
  - Status updates
  - Health checks
- Core business logic can be reused
- Updates needed:
  - Replace Flask dependency injection with FastAPI
  - Update async/await patterns

## Security & Encryption

### Credential Encryption (`repopal/utils/crypto.py`)
- `CredentialEncryption` class for secure storage
- Framework-agnostic implementation
- Can be used as-is in FastAPI

## GitHub Integration

### GitHub Client (`repopal/services/github.py`)
- Features:
  - API operations via `GitHubClient`
  - Rate limit handling
  - Installation management
- Minimal changes needed:
  - Update async client initialization
  - Adapt error handling

### GitHub Installation (`repopal/services/github_installation.py`)
- Handles GitHub App installations
- Updates needed:
  - Convert route handlers to FastAPI
  - Update webhook processing
  - Adapt authentication flow

## Error Handling

### Core Exceptions (`repopal/core/exceptions.py`)
- Custom exceptions for:
  - Service connections
  - Pipeline operations
  - Authentication
- Migration needs:
  - Map to FastAPI exception handlers
  - Update error response formats

## Health Monitoring

### Health Checks (`repopal/core/health.py`)
- Service health monitoring system
- Updates needed:
  - Adapt to FastAPI dependency injection
  - Update async health check handlers
  - Convert response formats

## Migration Steps

1. **Database Layer**
   - Update SQLAlchemy models for latest syntax
   - Adapt database session management for FastAPI

2. **Authentication Flow**
   - Implement FastAPI security schemes
   - Update OAuth handlers
   - Convert middleware

3. **API Routes**
   - Convert Flask routes to FastAPI path operations
   - Update dependency injection
   - Implement FastAPI response models

4. **Error Handling**
   - Create FastAPI exception handlers
   - Update error response schemas

5. **Testing**
   - Update test fixtures for FastAPI
   - Convert test clients
   - Update mocking patterns

## Technical Considerations

- Replace Flask-specific patterns with FastAPI equivalents
- Update to modern Python async patterns
- Implement FastAPI's dependency injection
- Use Pydantic models for request/response validation
- Consider FastAPI's background tasks vs Celery
