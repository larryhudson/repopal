from enum import Enum
from pydantic import BaseModel
from typing import Any, Dict

class WebhookProvider(str, Enum):
    GITHUB = "github"
    SLACK = "slack"
    LINEAR = "linear"

class StandardizedEvent(BaseModel):
    provider: WebhookProvider
    event_type: str
    user_request: str
    payload: Dict[str, Any]
    raw_payload: Dict[str, Any]
