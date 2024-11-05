import hashlib
import hmac
import json
import logging
from typing import Any, Dict, Optional

from github import Github
from github.GithubException import GithubException

from repopal.core.config import settings
from repopal.schemas.service_handler import ServiceProvider, StandardizedEvent

from .base import ResponseType, ServiceHandler


class GitHubHandler(ServiceHandler):
    def __init__(self, webhook_secret: str, github_token: Optional[str] = None):
        self.webhook_secret = webhook_secret
        self.github = Github(github_token or settings.GITHUB_TOKEN)

    def validate_webhook(
        self, headers: Dict[str, str], payload: Dict[str, Any]
    ) -> bool:
        if "X-Hub-Signature-256" not in headers:
            return False

        signature = headers["X-Hub-Signature-256"]
        payload_bytes = json.dumps(payload).encode()
        expected_signature = (
            "sha256="
            + hmac.new(
                self.webhook_secret.encode(), payload_bytes, hashlib.sha256
            ).hexdigest()
        )

        return hmac.compare_digest(signature, expected_signature)

    def process_webhook(self, payload: Dict[str, Any]) -> StandardizedEvent:
        # Determine base event type first
        if "pull_request" in payload:
            event_type = "pull_request"
        elif "comment" in payload:
            event_type = "comment"
        elif "issues" in payload or "issue" in payload:
            event_type = "issue"
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
        elif "comment" in payload:
            comment = payload["comment"]
            context = "issue" if "issue" in payload else "pull request"
            parent = payload.get("issue") or payload.get("pull_request", {})
            user_request = (
                f"Review {context} comment on: {parent.get('title', 'Untitled')}\n"
                f"Comment: {comment.get('body', 'No comment body')}\n"
                f"Author: {comment.get('user', {}).get('login', 'unknown')}"
            )
        elif "issue" in payload:
            issue = payload["issue"]
            user_request = (
                f"Check issue: {issue.get('title', 'Untitled Issue')}\n"
                f"Description: {issue.get('body', 'No description provided')}\n"
                f"Author: {issue.get('user', {}).get('login', 'unknown')}"
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
            "user": payload.get("pusher", {}).get("name")
            if "pusher" in payload
            else payload.get("sender", {}).get("login"),
            "repository": payload.get("repository", {}).get("full_name"),
            "url": payload.get("repository", {}).get("html_url"),
        }

        if "pull_request" in payload:
            pr = payload["pull_request"]
            standardized_payload.update(
                {
                    "title": pr.get("title"),
                    "description": pr.get("body"),
                }
            )
        elif "issue" in payload:
            issue = payload["issue"]
            standardized_payload.update(
                {
                    "title": issue.get("title"),
                    "description": issue.get("body"),
                }
            )

        return StandardizedEvent(
            provider=ServiceProvider.GITHUB,
            event_type=event_type,
            action=payload.get("action"),
            user_request=user_request,
            payload=standardized_payload,
            raw_payload=payload,
        )

    def send_response(
        self,
        payload: Dict[str, Any],
        message: str,
        response_type: ResponseType,
        thread_id: Optional[str] = None,
    ) -> str:
        """
        Send a response to GitHub based on the event type

        For issues/PRs, this creates or updates a comment
        For push events, this creates a commit status
        """
        # Determine event type from payload
        event_type = None
        if "pull_request" in payload:
            event_type = "pull_request"
        elif "comment" in payload:
            event_type = "comment" 
        elif "issues" in payload or "issue" in payload:
            event_type = "issue"
        else:
            event_type = "push"

        if event_type in ("issue", "pull_request", "comment"):
            try:
                # Extract repository and issue/PR number
                repo_name = payload["repository"]["full_name"]
                repo = self.github.get_repo(repo_name)
                
                if "issue" in payload:
                    number = payload["issue"]["number"]
                    issue_or_pr = repo.get_issue(number)
                elif "pull_request" in payload:
                    number = payload["pull_request"]["number"]
                    issue_or_pr = repo.get_pull(number)
                else:
                    raise ValueError("No issue or PR found in payload")

                if thread_id:
                    # Update existing comment
                    comment = repo.get_comment(int(thread_id))
                    comment.edit(message)
                    logging.info(f"Updated GitHub comment {thread_id}")
                    return thread_id
                else:
                    # Create new comment
                    comment = issue_or_pr.create_comment(message)
                    logging.info(f"Created GitHub comment {comment.id}")
                    return str(comment.id)

            except GithubException as e:
                logging.error(f"GitHub API error: {e}")
                raise
            except Exception as e:
                logging.error(f"Error sending GitHub response: {e}")
                raise

        else:
            raise ValueError(
                f"Unsupported event type for responses: {event_type}"
            )
import json
import pytest
from unittest.mock import Mock, patch
from github.GithubException import GithubException

from repopal.services.service_handlers.github import GitHubHandler
from repopal.services.service_handlers.base import ResponseType
from repopal.schemas.service_handler import ServiceProvider

@pytest.fixture
def github_handler():
    return GitHubHandler(webhook_secret="test_secret", github_token="test_token")

@pytest.fixture
def mock_github_repo():
    with patch('github.Github') as mock_github:
        mock_repo = Mock()
        mock_github.return_value.get_repo.return_value = mock_repo
        yield mock_repo

@pytest.fixture
def sample_issue_payload():
    return {
        "action": "opened",
        "issue": {
            "number": 1,
            "title": "Test Issue",
            "body": "Test Description",
            "user": {"login": "test-user"}
        },
        "repository": {
            "full_name": "test/repo",
            "html_url": "https://github.com/test/repo"
        },
        "sender": {"login": "test-user"}
    }

@pytest.fixture
def sample_pull_request_payload():
    return {
        "action": "opened",
        "pull_request": {
            "number": 1,
            "title": "Test Pull Request",
            "body": "Test PR Description",
            "user": {"login": "test-user"}
        },
        "repository": {
            "full_name": "test/repo",
            "html_url": "https://github.com/test/repo"
        },
        "sender": {"login": "test-user"}
    }

@pytest.fixture
def sample_comment_payload():
    return {
        "action": "created",
        "comment": {
            "body": "Test Comment",
            "user": {"login": "test-user"}
        },
        "issue": {
            "number": 1,
            "title": "Test Issue",
            "body": "Test Description"
        },
        "repository": {
            "full_name": "test/repo",
            "html_url": "https://github.com/test/repo"
        },
        "sender": {"login": "test-user"}
    }

@pytest.fixture
def sample_push_payload():
    return {
        "pusher": {"name": "test-user"},
        "repository": {
            "full_name": "test/repo",
            "html_url": "https://github.com/test/repo"
        }
    }

def test_webhook_validation(github_handler):
    payload = {"test": "data"}
    headers = {
        "X-Hub-Signature-256": "sha256=e963f47c6ffc36ae3362892b6c61d9211ff39452d0d28410bd046c3b011e4d8d"
    }
    
    assert github_handler.validate_webhook(headers, payload) == True
    
    # Test invalid signature
    headers["X-Hub-Signature-256"] = "sha256=invalid"
    assert github_handler.validate_webhook(headers, payload) == False

def test_process_issue_webhook(github_handler, sample_issue_payload):
    event = github_handler.process_webhook(sample_issue_payload)
    
    assert event.provider == ServiceProvider.GITHUB
    assert event.event_type == "issue"
    assert event.action == "opened"
    assert "Test Issue" in event.user_request
    assert event.payload["title"] == "Test Issue"
    assert event.payload["description"] == "Test Description"
    assert event.payload["user"] == "test-user"

def test_process_pull_request_webhook(github_handler, sample_pull_request_payload):
    event = github_handler.process_webhook(sample_pull_request_payload)
    
    assert event.provider == ServiceProvider.GITHUB
    assert event.event_type == "pull_request"
    assert event.action == "opened"
    assert "Test Pull Request" in event.user_request
    assert event.payload["title"] == "Test Pull Request"
    assert event.payload["description"] == "Test PR Description"
    assert event.payload["user"] == "test-user"

def test_process_comment_webhook(github_handler, sample_comment_payload):
    event = github_handler.process_webhook(sample_comment_payload)
    
    assert event.provider == ServiceProvider.GITHUB
    assert event.event_type == "comment"
    assert event.action == "created"
    assert "Test Comment" in event.user_request
    assert event.payload["title"] == "Test Issue"
    assert event.payload["description"] == "Test Description"
    assert event.payload["user"] == "test-user"

def test_process_push_webhook(github_handler, sample_push_payload):
    event = github_handler.process_webhook(sample_push_payload)
    
    assert event.provider == ServiceProvider.GITHUB
    assert event.event_type == "push"
    assert event.payload["user"] == "test-user"

@pytest.mark.asyncio
async def test_send_response_issue(github_handler, mock_github_repo, sample_issue_payload):
    # Mock the issue and comment objects
    mock_issue = Mock()
    mock_comment = Mock()
    mock_comment.id = 123
    
    mock_github_repo.get_issue.return_value = mock_issue
    mock_issue.create_comment.return_value = mock_comment
    
    # Test creating a new comment
    comment_id = github_handler.send_response(
        payload=sample_issue_payload,
        message="Test response",
        response_type=ResponseType.COMMENT
    )
    
    assert comment_id == "123"
    mock_github_repo.get_issue.assert_called_once_with(1)
    mock_issue.create_comment.assert_called_once_with("Test response")

@pytest.mark.asyncio
async def test_send_response_pull_request(github_handler, mock_github_repo, sample_pull_request_payload):
    # Mock the pull request and comment objects
    mock_pull_request = Mock()
    mock_comment = Mock()
    mock_comment.id = 456
    
    mock_github_repo.get_pull.return_value = mock_pull_request
    mock_pull_request.create_comment.return_value = mock_comment
    
    # Test creating a new comment on a pull request
    comment_id = github_handler.send_response(
        payload=sample_pull_request_payload,
        message="Test PR response",
        response_type=ResponseType.COMMENT
    )
    
    assert comment_id == "456"
    mock_github_repo.get_pull.assert_called_once_with(1)
    mock_pull_request.create_comment.assert_called_once_with("Test PR response")

@pytest.mark.asyncio
async def test_send_response_update_existing(github_handler, mock_github_repo, sample_issue_payload):
    # Mock the comment object
    mock_comment = Mock()
    mock_github_repo.get_comment.return_value = mock_comment
    
    # Test updating an existing comment
    github_handler.send_response(
        payload=sample_issue_payload,
        message="Updated response",
        response_type=ResponseType.COMMENT,
        thread_id="456"
    )
    
    mock_github_repo.get_comment.assert_called_once_with(456)
    mock_comment.edit.assert_called_once_with("Updated response")

def test_send_response_error_handling(github_handler, mock_github_repo, sample_issue_payload):
    # Mock GitHub API error
    mock_github_repo.get_issue.side_effect = GithubException(
        status=404,
        data={"message": "Not Found"}
    )
    
    with pytest.raises(GithubException):
        github_handler.send_response(
            payload=sample_issue_payload,
            message="Test response",
            response_type=ResponseType.COMMENT
        )

def test_send_response_unsupported_event(github_handler, sample_push_payload):
    with pytest.raises(ValueError):
        github_handler.send_response(
            payload=sample_push_payload,
            message="Test response",
            response_type=ResponseType.COMMENT
        )

def test_webhook_validation_missing_signature(github_handler):
    headers = {}  # No signature header
    payload = {"test": "data"}
    assert github_handler.validate_webhook(headers, payload) == False

@pytest.fixture
def sample_pr_comment_payload():
    return {
        "action": "created",
        "comment": {
            "body": "Test Comment",
            "user": {"login": "test-user"}
        },
        "pull_request": {
            "number": 1,
            "title": "Test PR",
            "body": "Test Description"
        },
        "repository": {
            "full_name": "test/repo",
            "html_url": "https://github.com/test/repo"
        },
        "sender": {"login": "test-user"}
    }

def test_process_pr_comment_webhook(github_handler, sample_pr_comment_payload):
    event = github_handler.process_webhook(sample_pr_comment_payload)
    
    assert event.provider == ServiceProvider.GITHUB
    assert event.event_type == "comment"
    assert event.action == "created"
    assert "Test Comment" in event.user_request
    assert "pull request" in event.user_request.lower()  # Verify it mentions PR context
    assert event.payload["user"] == "test-user"

def test_process_malformed_webhook(github_handler):
    malformed_payload = {
        "action": "opened",
        "repository": {
            "full_name": "test/repo",
            "html_url": "https://github.com/test/repo"
        },
        "sender": {"login": "test-user"}
    }
    
    event = github_handler.process_webhook(malformed_payload)
    assert event.event_type == "push"  # Default fallback
    assert event.payload["user"] == "test-user"

def test_send_response_invalid_type(github_handler, sample_issue_payload):
    with pytest.raises(ValueError):
        github_handler.send_response(
            payload=sample_issue_payload,
            message="Test response",
            response_type="INVALID_TYPE"  # Invalid response type
        )
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
