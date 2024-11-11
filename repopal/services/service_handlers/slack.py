import hashlib
import hmac
import json
import logging
import time
from typing import Any, Dict, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from repopal.core.config import settings
from repopal.schemas.service_handler import ServiceProvider, StandardizedEvent

from .base import ResponseType, ServiceHandler

# TODO: need to handle app installation events (create service connection)

class SlackHandler(ServiceHandler):
    def __init__(self, signing_secret: str, bot_token: Optional[str] = None):
        self.signing_secret = signing_secret
        self.client = WebClient(token=bot_token or settings.SLACK_BOT_TOKEN)

    def validate_webhook(
        self, headers: Dict[str, str], payload: Dict[str, Any]
    ) -> bool:
        """
        Validate Slack webhook using signing secret
        https://api.slack.com/authentication/verifying-requests-from-slack
        """
        # Check for required headers
        if not all(key in headers for key in ['X-Slack-Request-Timestamp', 'X-Slack-Signature']):
            return False

        # URL verification is always valid
        if payload.get('type') == 'url_verification':
            return True

        # Reconstruct the signature base string
        timestamp = headers['X-Slack-Request-Timestamp']
        signature = headers['X-Slack-Signature']

        # Check timestamp is not too old (5 minutes max)
        if abs(int(time.time()) - int(timestamp)) > 60 * 5:
            return False

        # Prepare the base string for HMAC
        base_string = f"v0:{timestamp}:{json.dumps(payload)}"

        # Compute the expected signature
        expected_signature = 'v0=' + hmac.new(
            key=self.signing_secret.encode(),
            msg=base_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        # Compare signatures
        return hmac.compare_digest(signature, expected_signature)

    def process_webhook(self, payload: Dict[str, Any]) -> StandardizedEvent:
        """
        Process Slack events and slash commands into StandardizedEvent
        """
        # URL verification for Slack Events API
        if payload.get('type') == 'url_verification':
            return StandardizedEvent(
                provider=ServiceProvider.SLACK,
                event_type='url_verification',
                action=None,
                user_request='Slack Events API verification',
                payload={},
                raw_payload=payload
            )

        # Determine event type
        event_type = 'unknown'
        user_request = ''
        standardized_payload = {
            'title': None,
            'description': None,
            'user': None,
            'repository': None,
            'url': None
        }

        # Handle slash commands
        if 'command' in payload:
            event_type = 'slash_command'
            user_request = payload.get('text', '')
            standardized_payload.update({
                'user': payload.get('user_name'),
                'title': payload.get('command'),
                'description': user_request
            })

        # Handle message events
        elif payload.get('type') == 'event_callback' and payload.get('event', {}).get('type') == 'message':
            event_type = 'message'
            event = payload.get('event', {})
            user_request = event.get('text', '')
            standardized_payload.update({
                'user': event.get('user'),
                'description': user_request
            })

        return StandardizedEvent(
            provider=ServiceProvider.SLACK,
            event_type=event_type,
            action=payload.get('event', {}).get('type'),
            user_request=user_request,
            payload=standardized_payload,
            raw_payload=payload
        )

    def send_response(
        self,
        payload: Dict[str, Any],
        message: str,
        response_type: ResponseType,
        thread_id: Optional[str] = None,
    ) -> str:
        """
        Send response back to Slack channel/thread
        """
        try:
            # Determine channel for response
            channel = None
            if 'channel' in payload:
                channel = payload['channel']
            elif 'event' in payload and 'channel' in payload['event']:
                channel = payload['event']['channel']

            if not channel:
                raise ValueError("No channel found in payload")

            # Send message with optional threading
            response = self.client.chat_postMessage(
                channel=channel,
                text=message,
                thread_ts=thread_id
            )

            # Return the timestamp which can be used as a thread ID
            return response['ts']

        except SlackApiError as e:
            logging.error(f"Slack API error: {e}")
            raise
        except Exception as e:
            logging.error(f"Error sending Slack response: {e}")
            raise
