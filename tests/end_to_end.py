import pytest
import logging
import json
import hmac
import hashlib
from pathlib import Path
from git import Repo
from repopal.schemas.webhook import StandardizedEvent, WebhookProvider
from repopal.services.commands.find_replace import FindReplaceArgs, FindReplaceCommand
from repopal.schemas.environment import EnvironmentConfig
from repopal.services.command_selector import CommandSelectorService
from repopal.services.environment_manager import EnvironmentManager
from repopal.services.webhook_handlers.github import GitHubWebhookHandler
from repopal.services.webhook_factory import WebhookHandlerFactory
from tests.integration.test_environment_manager_integration import test_repo

pytestmark = pytest.mark.integration

@pytest.mark.asyncio
async def test_end_to_end_workflow(test_repo, webhook_signature):
    """Integration test that simulates full workflow from webhook to command execution"""
    import asyncio
    # Create new event loop for this test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Setup services
        webhook_secret = "test_secret"
        handler = GitHubWebhookHandler(webhook_secret=webhook_secret)
        selector = CommandSelectorService()
        manager = EnvironmentManager()

        # Create a test issue payload
        issue_payload = {
            "action": "opened",
            "issue": {
                "title": "Update greeting",
                "body": "Please replace all occurrences of 'world' with 'everyone' in test.txt",
                "user": {"login": "user1"}
            },
            "repository": {
                "full_name": str(test_repo),
                "html_url": f"https://github.com/{test_repo}"
            },
            "sender": {"login": "user1"}
        }

        # Generate webhook signature
        headers, payload_bytes = webhook_signature(webhook_secret, issue_payload)

        # Validate webhook
        assert handler.validate_webhook(headers, issue_payload) is True

        # Process webhook to get standardized event
        event = handler.process_webhook(issue_payload)
        assert isinstance(event, StandardizedEvent)
        assert event.event_type == "issue"
        assert event.action == "opened"

        # Select command and generate arguments
        command, args = await selector.select_and_prepare_command(event)
        assert command is not None, "Should select a command"
        assert args is not None, "Should generate arguments"

        # Set up environment
        config = EnvironmentConfig(
            repo_url=str(test_repo),
            branch="main",
            environment_vars={},
        )

        # Set up repository and container
        work_dir = manager.setup_repository(config.repo_url, config.branch)
        assert work_dir.exists()
        manager.setup_container(command)
        assert manager.container is not None

        # Use args directly since they're already properly typed from command.convert_args()
        command_args = args

        # Execute the selected command
        result = await manager.execute_command(command, command_args, config)

        # Log the result for debugging
        logging.debug(f"Command execution result: {result}")

        # Verify command executed successfully
        assert result.success
        
        # Verify the changes were made
        changes = manager.get_repository_changes()
        assert changes, "Should have detected changes in the repository"
        
        # For find/replace command, verify the specific changes
        if isinstance(command, FindReplaceCommand):
            # Check the diff content
            diff_changes = next((c for c in changes if c["type"] == "diff"), None)
            assert diff_changes, "Should have diff changes"
            assert "everyone" in diff_changes["content"]
            assert "-Hello world!" in diff_changes["content"]
            assert "+Hello everyone!" in diff_changes["content"]

    finally:
        manager.cleanup()
        # Clean up the event loop
        loop.close()
