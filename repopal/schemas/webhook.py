from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, List

class WebhookProvider(str, Enum):
    GITHUB = "github"
    SLACK = "slack"
    LINEAR = "linear"

class StandardizedEvent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    provider: WebhookProvider
    event_type: str  # e.g. "pull_request", "issue", "push"
    action: str | None = None  # e.g. "opened", "closed", "updated"
    user_request: str  # Human readable description of the event
    payload: Dict[str, Any]  # Standardized payload with common fields
    raw_payload: Dict[str, Any]  # Original provider-specific payload
