import logging

import pytest

from repopal.schemas.environment import EnvironmentConfig
from repopal.schemas.service_handler import StandardizedEvent
from repopal.services.command_selector import CommandSelectorService
from repopal.services.commands.find_replace import FindReplaceCommand
from repopal.services.environment_manager import EnvironmentManager
from repopal.services.llm import LLMService
from repopal.services.service_handlers.base import ResponseType
from repopal.services.service_handlers.github import GitHubHandler

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
        service_handler = GitHubHandler(webhook_secret=webhook_secret)
        llm_service = LLMService()
        command_selector = CommandSelectorService(llm=llm_service)
        environment_manager = EnvironmentManager()

        # Create a test issue payload
        issue_payload = {
            "action": "opened",
            "issue": {
                "title": "Update greeting",
                "body": "Please replace all occurrences of 'world' with 'everyone' in test.txt",
                "user": {"login": "user1"},
            },
            "repository": {
                "full_name": str(test_repo),
                "html_url": f"https://github.com/{test_repo}",
            },
            "sender": {"login": "user1"},
        }

        # Generate webhook signature
        headers, payload_bytes = webhook_signature(webhook_secret, issue_payload)

        # Validate webhook
        assert service_handler.validate_webhook(headers, issue_payload) is True

        # Process webhook to get standardized event
        event = service_handler.process_webhook(issue_payload)
        assert isinstance(event, StandardizedEvent)
        assert event.event_type == "issue"
        assert event.action == "opened"

        # Select command and generate arguments
        command, args = await command_selector.select_and_prepare_command(event)
        assert command is not None, "Should select a command"
        assert args is not None, "Should generate arguments"

        # Set up environment
        environment_config = EnvironmentConfig(
            repo_url=str(test_repo),
            branch="main",
            environment_vars={},
        )

        # Set up repository and container
        work_dir = environment_manager.setup_repository(
            environment_config.repo_url, environment_config.branch
        )
        assert work_dir.exists()
        environment_manager.setup_container(command)
        assert environment_manager.container is not None

        # Use args directly since they're already properly typed from command.convert_args()
        command_args = args

        # Send initial received status
        thread_id = service_handler.send_response(
            payload=issue_payload,
            message=await llm_service.generate_status_message(
                "received", {"user_request": event.user_request}
            ),
            response_type=ResponseType.INITIAL,
        )

        # Send command selected status
        thread_id = service_handler.send_response(
            payload=issue_payload,
            message=await llm_service.generate_status_message(
                "selected",
                {
                    "user_request": event.user_request,
                    "command_name": command.__class__.__name__,
                    "command_args": args,
                },
            ),
            response_type=ResponseType.UPDATE,
            thread_id=thread_id,
        )

        # Execute the command
        result = await environment_manager.execute_command(
            command, command_args, environment_config
        )

        # Log the result for debugging
        logging.debug(f"Command execution result: {result}")

        # Get changes summary
        changes = environment_manager.get_repository_changes()
        changes_summary = await llm_service.generate_change_summary(
            event.user_request, command.__class__.__name__, result.data["output"], changes
        )

        # Send final status with changes
        service_handler.send_response(
            payload=issue_payload,
            message=await llm_service.generate_status_message(
                "completed",
                {
                    "user_request": event.user_request,
                    "changes_summary": changes_summary,
                },
            ),
            response_type=ResponseType.FINAL,
            thread_id=thread_id,
        )

        # Verify command executed successfully
        assert result.success

        # Verify the changes were made
        changes = environment_manager.get_repository_changes()
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
        environment_manager.cleanup()
        # Clean up the event loop
        loop.close()
