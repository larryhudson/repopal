from typing import Dict, Any
import json
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
        payload_bytes = json.dumps(payload).encode()
        expected_signature = "sha256=" + hmac.new(
            self.webhook_secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)

    def process_webhook(self, payload: Dict[str, Any]) -> StandardizedEvent:
        # Determine base event type first
        if "pull_request" in payload:
            event_type = "pull_request"
        elif "issues" in payload or "issue" in payload:
            event_type = "issue"
        elif "comment" in payload:
            event_type = "comment"
        else:
            event_type = "push"
            
        # Generate detailed user request string based on event type
        user_request = ""
        if "pull_request" in payload:
            pr = payload["pull_request"]
            user_request = (
                f"Review pull request: {pr.get('title', 'Untitled PR')}\n"
                f"Description: {pr.get('body', 'No description provided')}\n"
                f"Author: {pr.get('user', {}).get('login', 'unknown')}"
            )
        elif "issues" in payload and "issue" in payload:
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
            if "pusher" in payload:
                user_request = (
                    f"Process push event\n"
                    f"Author: {payload.get('pusher', {}).get('name', 'unknown')}"
                )
            else:
                user_request = f"Handle {event_type} event from {payload.get('sender', {}).get('login', 'unknown')}"


        # Extract common fields into standardized payload
        standardized_payload = {
            "title": None,
            "description": None,
            "user": payload.get("pusher", {}).get("name") if "pusher" in payload else payload.get("sender", {}).get("login"),
            "repository": payload.get("repository", {}).get("full_name"),
            "url": payload.get("repository", {}).get("html_url"),
        }

        if "pull_request" in payload:
            pr = payload["pull_request"]
            standardized_payload.update({
                "title": pr.get("title"),
                "description": pr.get("body"),
            })
        elif "issue" in payload:
            issue = payload["issue"]
            standardized_payload.update({
                "title": issue.get("title"),
                "description": issue.get("body"),
            })

        return StandardizedEvent(
            provider=WebhookProvider.GITHUB,
            event_type=event_type,
            action=payload.get("action"),
            user_request=user_request,
            payload=standardized_payload,
            raw_payload=payload
        )
