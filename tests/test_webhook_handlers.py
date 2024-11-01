import pytest
from unittest.mock import Mock
import hmac
import hashlib
import json
from repopal.schemas.webhook import WebhookProvider, StandardizedEvent
from repopal.services.webhook_handlers.github import GitHubWebhookHandler
from repopal.services.webhook_factory import WebhookHandlerFactory

@pytest.fixture
def github_handler():
    return GitHubWebhookHandler(webhook_secret="test_secret")

@pytest.fixture
def github_push_payload():
    return {
        "ref": "refs/heads/main",
        "repository": {
            "full_name": "octocat/Hello-World",
            "html_url": "https://github.com/octocat/Hello-World"
        },
        "pusher": {
            "name": "octocat",
            "email": "octocat@github.com"
        },
        "commits": [{
            "id": "7fd1a60b01f91b314f59955a4e4d4e80d8edf11d",
            "message": "Update README.md",
            "timestamp": "2024-01-01T00:00:00Z",
            "url": "https://github.com/octocat/Hello-World/commit/7fd1a60b01f91b314f59955a4e4d4e80d8edf11d",
            "author": {
                "name": "octocat",
                "email": "octocat@github.com"
            }
        }]
    }

def test_github_webhook_validation_success(github_handler, github_push_payload):
    payload_bytes = json.dumps(github_push_payload).encode()
    signature = hmac.new(
        key=b"test_secret",
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    headers = {
        "X-Hub-Signature-256": f"sha256={signature}"
    }
    
    assert github_handler.validate_webhook(headers, github_push_payload) is True

def test_github_webhook_validation_failure(github_handler, github_push_payload):
    headers = {
        "X-Hub-Signature-256": "sha256=invalid_signature"
    }
    
    assert github_handler.validate_webhook(headers, github_push_payload) is False

def test_github_webhook_process_push_event(github_handler, github_push_payload):
    result = github_handler.process_webhook(github_push_payload)
    
    assert isinstance(result, StandardizedEvent)
    assert result.repository_url == "https://github.com/octocat/Hello-World"
    assert result.repository_name == "octocat/Hello-World"
    assert result.event_type == "push"
    assert result.branch == "main"
    assert result.author == "octocat"
    assert len(result.commits) == 1
    assert result.commits[0].id == "7fd1a60b01f91b314f59955a4e4d4e80d8edf11d"
    assert result.commits[0].message == "Update README.md"

def test_webhook_factory_returns_correct_handler():
    handler = WebhookHandlerFactory.get_handler(WebhookProvider.GITHUB)
    assert isinstance(handler, GitHubWebhookHandler)

def test_webhook_factory_raises_for_unknown_provider():
    with pytest.raises(KeyError):
        WebhookHandlerFactory.get_handler("unknown_provider")

@pytest.fixture
def pull_request_payload():
    return {
        "action": "opened",
        "pull_request": {
            "title": "Add new feature",
            "body": "This PR adds an awesome new feature",
            "user": {"login": "developer1"}
        },
        "repository": {"full_name": "org/repo"},
        "sender": {"login": "developer1"}
    }

@pytest.fixture
def issue_payload():
    return {
        "action": "opened",
        "issue": {
            "title": "Bug report",
            "body": "Something is broken",
            "user": {"login": "user1"}
        },
        "repository": {"full_name": "org/repo"},
        "sender": {"login": "user1"}
    }

@pytest.fixture
def issue_comment_payload():
    return {
        "action": "created",
        "comment": {
            "body": "Great idea!",
            "user": {"login": "reviewer1"}
        },
        "issue": {
            "title": "Feature request"
        },
        "repository": {"full_name": "org/repo"},
        "sender": {"login": "reviewer1"}
    }

def test_github_webhook_pr_user_request(github_handler, pull_request_payload):
    result = github_handler.process_webhook(pull_request_payload)
    expected_request = (
        "Review pull request: Add new feature\n"
        "Description: This PR adds an awesome new feature\n"
        "Author: developer1"
    )
    assert result.user_request == expected_request
    assert result.event_type == "pull_request_opened"

def test_github_webhook_issue_user_request(github_handler, issue_payload):
    result = github_handler.process_webhook(issue_payload)
    expected_request = (
        "Check issue: Bug report\n"
        "Description: Something is broken\n"
        "Author: user1"
    )
    assert result.user_request == expected_request
    assert result.event_type == "issue_opened"

def test_github_webhook_comment_user_request(github_handler, issue_comment_payload):
    result = github_handler.process_webhook(issue_comment_payload)
    expected_request = (
        "Review issue comment on: Feature request\n"
        "Comment: Great idea!\n"
        "Author: reviewer1"
    )
    assert result.user_request == expected_request