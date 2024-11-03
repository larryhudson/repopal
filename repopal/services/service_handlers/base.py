from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional

from repopal.schemas.service_handler import StandardizedEvent


class ResponseType(Enum):
    INITIAL = "initial"
    UPDATE = "update"
    FINAL = "final"


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

    @abstractmethod
    def send_response(
        self,
        event: StandardizedEvent,
        message: str,
        response_type: ResponseType,
        thread_id: Optional[str] = None,
    ) -> str:
        """
        Send a response to the service (GitHub/Slack/Linear)
        
        Args:
            event: The original event being responded to
            message: The response message content
            response_type: Type of response (initial/update/final) 
            thread_id: Optional ID of existing response thread to update
            
        Returns:
            String ID that can be used to update this response later
        """
        pass
