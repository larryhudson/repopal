import pytest
import logging
from git import Repo
from repopal.schemas.webhook import StandardizedEvent, WebhookProvider
from tests.integration.test_environment_manager_integration import test_repo
from repopal.schemas.environment import EnvironmentConfig
from repopal.services.command_selector import CommandSelectorService
from repopal.services.environment_manager import EnvironmentManager
from repopal.services.commands.aider import AiderCommand
from repopal.services.commands.find_replace import FindReplaceCommand

pytestmark = pytest.mark.integration


async def test_command_selector_with_real_llm():
    """Integration test using real LLM to test command selection and argument generation"""
    # Setup
    selector = CommandSelectorService()

    # Create a test event that should trigger Aider command
    event = StandardizedEvent(
        provider=WebhookProvider.GITHUB,
        event_type="pull_request",
        action="opened",
        user_request="Please help me refactor this code to use better variable names",
        payload={
            "repository": "test-repo",
            "branch": "main",
            "files_changed": ["main.py"],
            "diff_content": "def x(a, b): return a + b",
        },
        raw_payload={
            "repository": {"full_name": "test-repo"},
            "pull_request": {
                "head": {"ref": "main"},
                "base": {"ref": "main"},
                "diff_url": "https://github.com/test/diff",
            },
        },
    )

    # Test command selection and argument generation
    command, args = await selector.select_and_prepare_command(event)

    # Verify the results
    assert isinstance(
        command, (AiderCommand, FindReplaceCommand)
    ), "Should select either Aider or FindReplace command for code refactoring"
    assert isinstance(args, dict), "Should return a dictionary of arguments"
    assert len(args) > 0, "Should generate some arguments"

    # Print results for manual inspection
    print(f"\nSelected command: {command.metadata.name}")
    print(f"Generated arguments: {args}")


@pytest.mark.asyncio
async def test_end_to_end_command_execution(test_repo):
    """Integration test that combines command selection and execution in container"""
    import asyncio
    # Create new event loop for this test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Setup services
        selector = CommandSelectorService()
        manager = EnvironmentManager()

        # Create a test event for a simple find/replace operation
        event = StandardizedEvent(
        provider=WebhookProvider.GITHUB,
        event_type="issue",
        action="opened",
        user_request="Please replace all occurrences of 'world' with 'everyone' in test.txt",
        payload={
            "repository": "test-repo",
            "branch": "main",
            "files_changed": ["test.txt"],
        },
        raw_payload={
            "repository": {"full_name": "test-repo"},
            "issue": {"number": 1},
        },
    )

    try:
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

        # Execute the selected command
        result = await manager.execute_command(command, args, config)

        # Log the result for debugging
        logging.debug(f"Command execution result: {result}")

        # Verify command executed successfully
        assert result.success
        
        # Verify the changes were made (if it was a find/replace command)
        if isinstance(command, FindReplaceCommand):
            modified_content = (work_dir / "test.txt").read_text()
            assert "Hello everyone!" in modified_content
            assert "world" not in modified_content

    finally:
        manager.cleanup()
        # Clean up the event loop
        loop.close()
