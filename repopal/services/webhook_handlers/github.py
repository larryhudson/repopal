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
            
        # Generate detailed user request string based on event type
        user_request = ""
        if "pull_request" in payload:
            pr = payload["pull_request"]
            user_request = (
                f"Review pull request: {pr.get('title', 'Untitled PR')}\n"
                f"Description: {pr.get('body', 'No description provided')}\n"
                f"Author: {pr.get('user', {}).get('login', 'unknown')}"
            )
        elif "issues" in payload:
            issue = payload["issue"]
            user_request = (
                f"Check issue: {issue.get('title', 'Untitled Issue')}\n"
                f"Description: {issue.get('body', 'No description provided')}\n"
                f"Author: {issue.get('user', {}).get('login', 'unknown')}"
            )
        elif "comment" in payload:
            comment = payload["comment"]
            context = "issue" if "issue" in payload else "pull request"
            parent = payload.get("issue", payload.get("pull_request", {}))
            user_request = (
                f"Review {context} comment on: {parent.get('title', 'Untitled')}\n"
                f"Comment: {comment.get('body', 'No comment body')}\n"
                f"Author: {comment.get('user', {}).get('login', 'unknown')}"
            )
        else:
            user_request = f"Handle {event_type} event from {payload.get('sender', {}).get('login', 'unknown')}"

        return StandardizedEvent(
            provider=WebhookProvider.GITHUB,
            event_type=event_type,
            user_request=user_request,
            payload={
                "repository": payload.get("repository", {}).get("full_name"),
                "sender": payload.get("sender", {}).get("login"),
                "action": payload.get("action"),
            },
            raw_payload=payload
        )