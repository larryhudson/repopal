import logging

import pytest

from repopal.schemas.environment import EnvironmentConfig
from repopal.schemas.service_handler import StandardizedEvent
from repopal.services.command_selector import CommandSelectorService
from repopal.services.commands.find_replace import FindReplaceCommand
from repopal.services.environment_manager import EnvironmentManager
from repopal.services.git_repo_manager import GitRepoManager
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
        # TODO: move these modules into fixtures / dependency injection
        service_handler = GitHubHandler(webhook_secret=webhook_secret)
        llm_service = LLMService()
        command_selector = CommandSelectorService(llm=llm_service)
        environment_manager = EnvironmentManager()
        git_repo_manager = GitRepoManager()

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
        work_dir = git_repo_manager.clone_repo(
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
        service_handler.send_response(
            payload=issue_payload,
            message=await llm_service.generate_status_message(
                "selected",
                {
                    "user_request": event.user_request,
                    "command_name": command.metadata.name,
                    "command_args": args,
                },
            ),
            response_type=ResponseType.UPDATE,
            thread_id=thread_id,
        )

        # Execute the command
        command_result = await environment_manager.execute_command(
            command, command_args, environment_config
        )

        # Log the result for debugging
        logging.debug(f"Command execution result: {command_result}")

        # Get changes and generate summary
        repository_changes = environment_manager.get_repository_changes()
        changes_summary = await llm_service.generate_change_summary(
            event.user_request, command.metadata.name, command_result.output, repository_changes
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
        assert command_result.success

        # Verify the changes were made
        changes = environment_manager.get_repository_changes()
        assert changes, "Should have detected changes in the repository"

        # For find/replace command, verify the specific changes
        if isinstance(command, FindReplaceCommand):
            # Check the diff content
            diff_changes = next((c for c in changes.tracked_changes), None)
            assert diff_changes, "Should have tracked changes"
            assert "everyone" in diff_changes.diff
            assert "-Hello world!" in diff_changes.diff
            assert "+Hello everyone!" in diff_changes.diff

        if changes:

            commit_message = llm_service.generate_commit_message(
                event.user_request, command.metadata.name, command_result.output
            )

            # TODO: generate this branch name based on the request. e.g. repopal-issue-50 for GitHub issue
            branch_name = "test-branch"

            git_repo_manager.push_changes_to_new_branch(
                branch_name=branch_name,
                commit_message=commit_message
            )

            pr_description = llm_service.generate_pr_description(
                event.user_request, command.metadata.name, command_result.output, changes_summary
            )

            created_pr = github_api.create_pull_request(
                branch_name,
                pr_description
            )


            # Send final update with link to created PR
            service_handler.send_response(
                payload=issue_payload,
                message=await llm_service.generate_status_message(
                    "created_pr",
                    {
                        "user_request": event.user_request,
                        "created_pr": created_pr,
                    },
                ),
                response_type=ResponseType.FINAL,
                thread_id=thread_id,
            )

    finally:
        environment_manager.cleanup()
        # Clean up the event loop
        loop.close()
