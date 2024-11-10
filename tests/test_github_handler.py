import pytest
from unittest.mock import Mock, patch

from repopal.services.service_handlers.github import GitHubHandler
from repopal.services.service_handlers.base import ResponseType

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
