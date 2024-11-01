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
    repository_url: str | None = None
    repository_name: str | None = None
    branch: str | None = None
    author: str | None = None
    commits: List[Dict[str, Any]] = []
