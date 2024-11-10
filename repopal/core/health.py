"""Service connection health checking"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

from repopal.services.github import get_github_client
# TODO: Implement slack service module
# from repopal.services.slack import get_slack_client

class HealthStatus(str, Enum):
    """Health check status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"

class HealthCheckResult:
    """Result of a health check"""
    def __init__(
        self,
        status: HealthStatus,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        last_check: Optional[datetime] = None
    ):
        self.status = status
        self.message = message
        self.details = details or {}
        self.last_check = last_check or datetime.utcnow()

class ServiceHealthCheck(ABC):
    """Base class for service-specific health checks"""
    
    @abstractmethod
    async def check_health(self, connection_id: str) -> HealthCheckResult:
        """Run health check for a service connection"""
        pass

class GitHubHealthCheck(ServiceHealthCheck):
    """Health check for GitHub App connections"""
    
    async def check_health(self, connection_id: str) -> HealthCheckResult:
        """Check GitHub App connection health"""
        try:
            # Get GitHub client for this connection
            github = await get_github_client(connection_id)
            
            # Check installation access
            installation = await github.get_app_installation()
            if not installation:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message="GitHub App installation not found"
                )
            
            # Check rate limits
            rate_limits = await github.get_rate_limit()
            remaining = rate_limits.core.remaining
            if remaining < 100:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    message=f"Rate limit low: {remaining} remaining",
                    details={"rate_limit": rate_limits.dict()}
                )
                
            # Verify webhook configuration
            hooks = await github.get_app_webhooks()
            if not any(h.active for h in hooks):
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    message="No active webhooks found"
                )
                
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="GitHub connection healthy",
                details={
                    "installation_id": installation.id,
                    "rate_limit_remaining": remaining
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}"
            )

# TODO: Implement SlackHealthCheck when slack service is ready
# class SlackHealthCheck(ServiceHealthCheck):
#     """Health check for Slack workspace connections"""
#     
#     async def check_health(self, connection_id: str) -> HealthCheckResult:
#         """Check Slack workspace connection health"""
#         try:
#             # Get Slack client for this connection
#             slack = await get_slack_client(connection_id)
#             
#             # Test auth
#             auth_test = await slack.auth_test()
#             if not auth_test["ok"]:
#                 return HealthCheckResult(
#                     status=HealthStatus.UNHEALTHY,
#                     message="Invalid Slack credentials"
#                 )
#                 
#             # Check required scopes
#             required_scopes = {"chat:write", "channels:read", "channels:join"}
#             actual_scopes = set(auth_test["scopes"])
#             missing_scopes = required_scopes - actual_scopes
#             
#             if missing_scopes:
#                 return HealthCheckResult(
#                     status=HealthStatus.DEGRADED,
#                     message=f"Missing required scopes: {missing_scopes}",
#                     details={"missing_scopes": list(missing_scopes)}
#                 )
#                 
#             # Test basic API operation
#             try:
#                 await slack.conversations_list(limit=1)
#             except Exception as e:
#                 return HealthCheckResult(
#                     status=HealthStatus.UNHEALTHY,
#                     message=f"API test failed: {str(e)}"
#                 )
#                 
#             return HealthCheckResult(
#                 status=HealthStatus.HEALTHY,
#                 message="Slack connection healthy",
#                 details={
#                     "bot_id": auth_test["bot_id"],
#                     "team_id": auth_test["team_id"]
#                 }
#             )
#             
#         except Exception as e:
#             return HealthCheckResult(
#                 status=HealthStatus.UNHEALTHY,
#                 message=f"Health check failed: {str(e)}"
#             )

class HealthCheckFactory:
    """Creates appropriate health checker for service type"""
    
    _checkers = {
        "github_app": GitHubHealthCheck,
        # TODO: Add back when slack service is implemented
        # "slack": SlackHealthCheck
    }
    
    @classmethod
    def get_checker(cls, service_type: str) -> ServiceHealthCheck:
        """Get health checker for service type"""
        checker_class = cls._checkers.get(service_type)
        if not checker_class:
            raise ValueError(f"No health checker for service type: {service_type}")
        return checker_class()
