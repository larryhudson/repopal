import pytest

from repopal.schemas.webhook import StandardizedEvent, WebhookProvider
from repopal.services.command_selector import CommandSelectorService
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
