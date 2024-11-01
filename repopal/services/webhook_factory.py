from typing import Dict, Type
from .webhook_handlers.base import WebhookHandler
from .webhook_handlers.github import GitHubWebhookHandler
from repopal.schemas.webhook import WebhookProvider
from repopal.core.config import get_settings

class WebhookHandlerFactory:
    _handlers: Dict[WebhookProvider, WebhookHandler] = {}

    @classmethod
    def initialize(cls):
        settings = get_settings()
        # For testing, use a default secret if not configured
        github_secret = getattr(settings, "GITHUB_WEBHOOK_SECRET", "test_secret")
        cls._handlers = {
            WebhookProvider.GITHUB: GitHubWebhookHandler(github_secret),
            # Add other handlers here as they're implemented
        }

    @classmethod
    def get_handler(cls, provider: WebhookProvider) -> WebhookHandler:
        if provider not in cls._handlers:
            raise ValueError(f"No handler registered for provider: {provider}")
        return cls._handlers[provider]
