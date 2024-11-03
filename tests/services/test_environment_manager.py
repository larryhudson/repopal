import pytest

from repopal.schemas.environment import EnvironmentConfig
from repopal.services.commands.find_replace import FindReplaceCommand
from repopal.services.environment_manager import EnvironmentManager


@pytest.fixture
def test_repo(tmp_path):
    """Create a test git repository"""
    from git import Repo

    repo_dir = tmp_path / "test-repo"
    repo_dir.mkdir()

    # Initialize git repo
    repo = Repo.init(repo_dir)

    # Create a test file
    test_file = repo_dir / "test.txt"
    test_file.write_text("test content")

    # Commit the file
    repo.index.add(["test.txt"])
    repo.index.commit("Initial commit")

    return repo_dir


@pytest.mark.asyncio
async def test_environment_manager_setup(test_repo):
    """Test that environment manager can set up a repository and run commands"""
    manager = EnvironmentManager()
    command = FindReplaceCommand()

    commit_config = CommitConfig(
        enabled=True,
        message_format="test: {command_name} changes",
        commit_all=True
    )

    config = EnvironmentConfig(
        repo_url=str(test_repo),
        branch="main",
        environment_vars={"TEST_VAR": "test_value"},
        commit_config=commit_config
    )

    try:
        # Set up repository
        work_dir = manager.setup_repository(config.repo_url, config.branch)
        assert work_dir.exists()
        assert (work_dir / "test.txt").exists()

        # Set up container
        manager.setup_container(command, config.environment_vars)
        assert manager.container is not None

        # Run a test command
        exit_code, output = manager.run_in_container("echo $TEST_VAR")
        assert exit_code == 0
        assert output.strip() == "test_value"

        # Execute the find-replace command through the environment manager
        args = {
            "find_pattern": "test content",
            "replace_text": "new content",
            "working_dir": str(work_dir)
        }
        result = await manager.execute_command(command, args, config)
        assert result.success
        assert "completed successfully" in result.message

    finally:
        manager.cleanup()

@pytest.mark.asyncio
async def test_get_repository_changes(test_repo):
    """Test that we can detect changes in the repository"""
    manager = EnvironmentManager()

    config = EnvironmentConfig(
        repo_url=str(test_repo),
        branch="main",
        environment_vars={}
    )

    try:
        # Set up repository
        work_dir = manager.setup_repository(config.repo_url, config.branch)

        # Initially there should be no changes
        changes = manager.get_repository_changes()
        assert len(changes) == 0

        # Modify existing file
        test_file = work_dir / "test.txt"
        test_file.write_text("modified content")

        # Create new untracked file
        new_file = work_dir / "new.txt"
        new_file.write_text("new file content")

        # Check changes
        changes = manager.get_repository_changes()
        assert len(changes) == 2

        # Verify diff content
        diff_entry = next(change for change in changes if change["type"] == "diff")
        assert "modified content" in diff_entry["content"]
        assert "-test content" in diff_entry["content"]

        # Verify untracked files
        untracked_entry = next(change for change in changes if change["type"] == "untracked")
        assert "new.txt" in untracked_entry["files"]

    finally:
        manager.cleanup()
