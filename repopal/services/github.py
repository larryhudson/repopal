"""GitHub service integration"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from github import Github, GithubIntegration
from github.Installation import Installation
from github.RateLimit import RateLimit

from repopal.models.service_connection import ServiceConnection
from repopal.core.exceptions import ServiceConnectionError

@dataclass
class GitHubRateLimits:
    """Rate limit information for GitHub API"""
    core: RateLimit
    search: RateLimit
    graphql: RateLimit
    integration_manifest: RateLimit
    source_import: RateLimit
    code_scanning_upload: RateLimit
    
    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> 'GitHubRateLimits':
        """Create from GitHub API response"""
        return cls(
            core=response.core,
            search=response.search,
            graphql=response.graphql,
            integration_manifest=response.integration_manifest,
            source_import=response.source_import,
            code_scanning_upload=response.code_scanning_upload
        )

class GitHubClient:
    """Client for GitHub API operations"""
    
    def __init__(self, connection: ServiceConnection):
        self.connection = connection
        self._client = None
        self._integration = None
        
    async def _init_client(self) -> None:
        """Initialize GitHub client if needed"""
        if not self._client:
            creds = self.connection.get_credentials()
            
            # Initialize GitHub App integration
            self._integration = GithubIntegration(
                creds["app_id"],
                creds["private_key"]
            )
            
            # Get installation token
            installation_id = creds["installation_id"]
            access_token = self._integration.get_access_token(installation_id)
            
            # Create client with installation token
            self._client = Github(access_token.token)
    
    async def get_app_installation(self) -> Optional[Installation]:
        """Get GitHub App installation details"""
        await self._init_client()
        try:
            installation_id = self.connection.get_credentials()["installation_id"]
            return self._integration.get_installation(installation_id)
        except Exception as e:
            raise ServiceConnectionError(f"Failed to get installation: {str(e)}")
    
    async def get_rate_limit(self) -> GitHubRateLimits:
        """Get current rate limit status"""
        await self._init_client()
        try:
            limits = self._client.get_rate_limit()
            return GitHubRateLimits.from_response(limits)
        except Exception as e:
            raise ServiceConnectionError(f"Failed to get rate limits: {str(e)}")
    
    async def get_app_webhooks(self) -> list:
        """Get configured webhooks for the app installation"""
        await self._init_client()
        try:
            installation = await self.get_app_installation()
            return list(installation.get_hooks())
        except Exception as e:
            raise ServiceConnectionError(f"Failed to get webhooks: {str(e)}")

async def get_github_client(connection_id: str) -> GitHubClient:
    """Get GitHub client for a service connection"""
    # TODO: Add caching of clients
    try:
        # Get connection from database
        connection = ServiceConnection.get_by_id(connection_id)
        if not connection:
            raise ServiceConnectionError(f"Connection not found: {connection_id}")
            
        return GitHubClient(connection)
        
    except Exception as e:
        raise ServiceConnectionError(f"Failed to create GitHub client: {str(e)}")
