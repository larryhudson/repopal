from typing import Dict

from repopal.core.config import get_settings
from repopal.schemas.service_handler import ServiceProvider
from repopal.services.service_handlers.base import ServiceHandler
from repopal.services.service_handlers.github import GitHubHandler


class ServiceHandlerFactory:
    _handlers: Dict[ServiceProvider, ServiceHandler] = {}

    @classmethod
    def initialize(cls):
        settings = get_settings()
        # For testing, use a default secret if not configured
        github_secret = getattr(settings, "GITHUB_WEBHOOK_SECRET", "test_secret")
        cls._handlers = {
            ServiceProvider.GITHUB: GitHubHandler(github_secret),
            # Add other handlers here as they're implemented
        }

    @classmethod
    def get_handler(cls, provider: ServiceProvider) -> ServiceHandler:
        if provider not in cls._handlers:
            raise KeyError(f"No handler registered for provider: {provider}")
        return cls._handlers[provider]
