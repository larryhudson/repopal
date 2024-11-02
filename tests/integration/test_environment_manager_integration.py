import pytest

from repopal.schemas.environment import EnvironmentConfig
from repopal.services.commands.find_replace import FindReplaceCommand, FindReplaceArgs
from repopal.services.environment_manager import EnvironmentManager

pytestmark = pytest.mark.integration


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
    test_file.write_text("Hello world! This is a test file.")

    # Commit the file
    repo.index.add(["test.txt"])
    repo.index.commit("Initial commit")

    return repo_dir


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
            working_dir=str(work_dir)
        )
        result = await manager.execute_command(command, args, config)
        
        # Verify command success
        assert result["success"]
        
        # Verify file was modified
        modified_content = (work_dir / "test.txt").read_text()
        assert "Hello everyone!" in modified_content
        assert "world" not in modified_content

    finally:
        manager.cleanup()
