from abc import ABC, abstractmethod
from typing import Any, Dict

from repopal.schemas.service_handler import StandardizedEvent


class ServiceHandler(ABC):
    @abstractmethod
    def validate_webhook(
        self, headers: Dict[str, str], payload: Dict[str, Any]
    ) -> bool:
        """Validate the webhook signature/authenticity"""
        pass

    @abstractmethod
    def process_webhook(self, payload: Dict[str, Any]) -> StandardizedEvent:
        """Convert webhook payload to standardized event"""
        pass
