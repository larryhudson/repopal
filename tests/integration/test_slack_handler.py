import hashlib
import hmac
import json
from unittest.mock import patch

import pytest
from slack_sdk.errors import SlackApiError

from repopal.schemas.service_handler import ServiceProvider
from repopal.services.service_handlers.base import ResponseType
from repopal.services.service_handlers.slack import SlackHandler


@pytest.fixture
def slack_handler():
    return SlackHandler(signing_secret="test_secret", bot_token="test_token")

@pytest.fixture
def sample_message_payload():
    return {
        "type": "event_callback",
        "event": {
            "type": "message",
            "text": "Hello bot",
            "user": "U123456",
            "channel": "C123456",
            "ts": "1234567890.123456"
        },
        "team_id": "T123456",
        "event_id": "Ev123456",
        "event_time": 1234567890
    }

@pytest.fixture
def sample_slash_command_payload():
    return {
        "token": "verification_token",
        "team_id": "T123456",
        "team_domain": "team",
        "channel_id": "C123456",
        "channel_name": "test-channel",
        "user_id": "U123456",
        "user_name": "testuser",
        "command": "/testcommand",
        "text": "test parameters",
        "response_url": "https://hooks.slack.com/commands/xxx",
        "trigger_id": "trigger_id"
    }

def test_webhook_validation(slack_handler):
    timestamp = "1234567890"
    payload = {"test": "data"}

    # Create valid signature
    base_string = f"v0:{timestamp}:{json.dumps(payload)}"
    signature = 'v0=' + hmac.new(
        key=b"test_secret",
        msg=base_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()

    headers = {
        'X-Slack-Request-Timestamp': timestamp,
        'X-Slack-Signature': signature
    }

    assert slack_handler.validate_webhook(headers, payload) == True

def test_process_message_webhook(slack_handler, sample_message_payload):
    event = slack_handler.process_webhook(sample_message_payload)

    assert event.provider == ServiceProvider.SLACK
    assert event.event_type == "message"
    assert event.user_request == "Hello bot"
    assert event.payload["user"] == "U123456"

def test_process_slash_command_webhook(slack_handler, sample_slash_command_payload):
    event = slack_handler.process_webhook(sample_slash_command_payload)

    assert event.provider == ServiceProvider.SLACK
    assert event.event_type == "slash_command"
    assert event.payload["user"] == "testuser"
    assert event.payload["title"] == "/testcommand"

@pytest.mark.asyncio
async def test_send_response(slack_handler, sample_message_payload):
    with patch('slack_sdk.WebClient.chat_postMessage') as mock_post:
        mock_post.return_value = {"ts": "1234567890.123456"}

        thread_id = slack_handler.send_response(
            payload=sample_message_payload,
            message="Test response",
            response_type=ResponseType.COMMENT
        )

        assert thread_id == "1234567890.123456"
        mock_post.assert_called_once_with(
            channel="C123456",
            text="Test response",
            thread_ts=None
        )

@pytest.mark.asyncio
async def test_send_threaded_response(slack_handler, sample_message_payload):
    with patch('slack_sdk.WebClient.chat_postMessage') as mock_post:
        mock_post.return_value = {"ts": "1234567890.123457"}

        thread_id = slack_handler.send_response(
            payload=sample_message_payload,
            message="Test response",
            response_type=ResponseType.COMMENT,
            thread_id="1234567890.123456"
        )

        assert thread_id == "1234567890.123457"
        mock_post.assert_called_once_with(
            channel="C123456",
            text="Test response",
            thread_ts="1234567890.123456"
        )

def test_send_response_error(slack_handler, sample_message_payload):
    with patch('slack_sdk.WebClient.chat_postMessage') as mock_post:
        mock_post.side_effect = SlackApiError("Error", {"error": "channel_not_found"})

        with pytest.raises(SlackApiError):
            slack_handler.send_response(
                payload=sample_message_payload,
                message="Test response",
                response_type=ResponseType.COMMENT
            )

def test_url_verification(slack_handler):
    payload = {
        "type": "url_verification",
        "challenge": "test_challenge"
    }

    event = slack_handler.process_webhook(payload)
    assert event.event_type == "url_verification"
