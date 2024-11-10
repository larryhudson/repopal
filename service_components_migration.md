# Service Connection Components Migration Guide

This document outlines the key components for migrating service connection and authentication code from the Flask-based implementation to FastAPI.

## Core Database Models

### Service Connection Models (`repopal/models/service_connection.py`)
- Contains essential models:
  - `ServiceConnection`: Core connection details
  - `Repository`: Repository information (primary model for repository management)
  - `ServiceCredential`: Encrypted credential storage
- Integration with BaseRepository pattern:
  - ServiceConnectionRepository for managing connections
  - RepositoryRepository for repository operations
  - ServiceCredentialRepository for credential management
- Repository model serves as the primary model for repository tracking
  - Includes GitHub-specific fields
  - Supports Slack channel mapping
  - Maintains connection to parent ServiceConnection

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
- ⚠️ CONFLICT: Needs integration with existing UserService and CommandSelectorService

## Security & Encryption

### Credential Encryption (`repopal/utils/crypto.py`)
- `CredentialEncryption` class for secure storage
- Framework-agnostic implementation
- Can be used as-is in FastAPI
- ✓ No conflicts - clean implementation

## GitHub Integration

### GitHub Client (`repopal/services/github.py`)
- Features:
  - API operations via `GitHubClient`
  - Rate limit handling
  - Installation management
- ⚠️ CONFLICT: Overlaps with existing GitHub-related code in services/service_handlers/github.py
- ⚠️ CONFLICT: Need to merge GitHubHandler and GitHubClient functionality

### GitHub Installation (`repopal/services/github_installation.py`)
- Handles GitHub App installations
- Updates needed:
  - Convert route handlers to FastAPI
  - Update webhook processing
  - Adapt authentication flow
- ⚠️ CONFLICT: Needs coordination with existing SlackHandler implementation

## Error Handling

### Core Exceptions (`repopal/core/exceptions.py`)
- Custom exceptions for:
  - Service connections
  - Pipeline operations
  - Authentication
- ✓ Compatible with existing exception hierarchy
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
- ✓ No conflicts - new functionality

## Migration Steps

1. **Database Layer**
   - Update SQLAlchemy models for latest syntax
   - Adapt database session management for FastAPI
   - ⚠️ Ensure compatibility with existing BaseRepository pattern

2. **Authentication Flow**
   - Implement FastAPI security schemes
   - Update OAuth handlers
   - Convert middleware
   - ⚠️ Coordinate with existing user authentication system

3. **API Routes**
   - Convert Flask routes to FastAPI path operations
   - Update dependency injection
   - Implement FastAPI response models
   - ⚠️ Align with existing command and change tracking endpoints

4. **Error Handling**
   - Create FastAPI exception handlers
   - Update error response schemas
   - ✓ Build on existing exception hierarchy

5. **Testing**
   - Update test fixtures for FastAPI
   - Convert test clients
   - Update mocking patterns
   - ⚠️ Integrate with existing test patterns (see tests/services/test_command_selector.py)

## Technical Considerations

- Replace Flask-specific patterns with FastAPI equivalents
- Update to modern Python async patterns
- Implement FastAPI's dependency injection
- Use Pydantic models for request/response validation
- Consider FastAPI's background tasks vs Celery
- ⚠️ Ensure consistent async/await usage across old and new code
- ⚠️ Standardize on common patterns for service handlers
