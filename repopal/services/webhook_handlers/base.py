from abc import ABC, abstractmethod
from typing import Dict, Any
from repopal.schemas.webhook import StandardizedEvent

class WebhookHandler(ABC):
    @abstractmethod
    def validate_webhook(self, headers: Dict[str, str], payload: Dict[str, Any]) -> bool:
        """Validate the webhook signature/authenticity"""
        pass

    @abstractmethod
    def process_webhook(self, payload: Dict[str, Any]) -> StandardizedEvent:
        """Convert webhook payload to standardized event"""
        pass
