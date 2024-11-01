from typing import Dict, Any
import hmac
import hashlib
from .base import WebhookHandler
from repopal.schemas.webhook import StandardizedEvent, WebhookProvider

class GitHubWebhookHandler(WebhookHandler):
    def __init__(self, webhook_secret: str):
        self.webhook_secret = webhook_secret

    def validate_webhook(self, headers: Dict[str, str], payload: Dict[str, Any]) -> bool:
        if "X-Hub-Signature-256" not in headers:
            return False
        
        signature = headers["X-Hub-Signature-256"]
        expected_signature = "sha256=" + hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)

    def process_webhook(self, payload: Dict[str, Any]) -> StandardizedEvent:
        event_type = payload.get("action", "unknown")
        if "pull_request" in payload:
            event_type = f"pull_request_{event_type}"
        elif "issues" in payload:
            event_type = f"issue_{event_type}"
            
        return StandardizedEvent(
            provider=WebhookProvider.GITHUB,
            event_type=event_type,
            payload={
                "repository": payload.get("repository", {}).get("full_name"),
                "sender": payload.get("sender", {}).get("login"),
                "action": payload.get("action"),
            },
            raw_payload=payload
        )
