import logging

import pytest

from repopal.schemas.environment import EnvironmentConfig
from repopal.services.commands.find_replace import FindReplaceArgs, FindReplaceCommand
from repopal.services.commands.hello_world import HelloWorldArgs, HelloWorldCommand
from repopal.services.environment_manager import EnvironmentManager

pytestmark = pytest.mark.integration



@pytest.mark.asyncio
async def test_environment_manager_setup(test_repo):
    """Test that environment manager can set up a repository and run commands"""
    manager = EnvironmentManager()
    command = FindReplaceCommand()

    config = EnvironmentConfig(
        repo_url=str(test_repo),
        branch="main",
        environment_vars={"TEST_VAR": "test_value"},
    )

    try:
        # Set up repository
        work_dir = manager.setup_repository(
            config.repo_url, config.branch if config.branch else "master"
        )
        assert work_dir.exists()
        assert (work_dir / "test.txt").exists()

        # Set up container
        manager.setup_container(command, config.environment_vars)
        assert manager.container is not None

        # Execute find/replace command
        args = FindReplaceArgs(
            find_pattern="world",
            replace_text="everyone",
            file_pattern="*.txt",
            working_dir=str(work_dir),
        )
        result = await manager.execute_command(command, args, config)

        # Log the result for debugging
        logging.debug(f"Command execution result: {result}")

        # Verify command success and check file contents
        assert result.success

        # Verify file was modified
        modified_content = (work_dir / "test.txt").read_text()
        assert "Hello everyone!" in modified_content
        assert "world" not in modified_content

        # Verify changes were captured correctly
        changes = manager.get_repository_changes()
        assert len(changes) > 0
        
        # Should have diff changes
        diff_changes = next((c for c in changes if c.type == "diff"), None)
        assert diff_changes is not None
        assert "test.txt" in diff_changes.content
        assert "+Hello everyone" in diff_changes.content
        assert "-Hello world" in diff_changes.content

        return result
    finally:
        pass


@pytest.mark.asyncio
async def test_hello_world_command(test_repo):
    """Test that hello world command works correctly"""
    manager = EnvironmentManager()
    command = HelloWorldCommand()

    config = EnvironmentConfig(
        repo_url=str(test_repo),
        branch="main",
        environment_vars={},
    )

    try:
        # Set up repository
        work_dir = manager.setup_repository(config.repo_url, config.branch)
        assert work_dir.exists()

        # Set up container
        manager.setup_container(command)
        assert manager.container is not None

        # Execute hello world command
        args = HelloWorldArgs()
        result = await manager.execute_command(command, args, config)

        # Log the result for debugging
        logging.debug(f"Command execution result: {result}")

        # Verify command success and check file contents
        assert result.success

        # Verify file was created with correct content
        hello_file = work_dir / "hello.txt"
        logging.debug(f"hello_file path: {hello_file}")
        assert hello_file.exists(), f"File not found at {hello_file}"
        content = hello_file.read_text().strip()
        logging.debug(f"File contents: {content}")
        assert content == "Hello world"

        return result
    finally:
        pass
    #     # Only cleanup after we've verified the results
    #     if hello_file.exists():
    #         manager.cleanup()
