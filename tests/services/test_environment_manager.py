import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from repopal.services.environment_manager import EnvironmentManager
from repopal.schemas.command import CommandResult
from repopal.schemas.environment import EnvironmentConfig

@pytest.fixture
def env_manager():
    with patch('docker.from_env'):
        manager = EnvironmentManager()
        yield manager
        manager.cleanup()

def test_setup_repository(env_manager):
    with patch('git.Repo.clone_from') as mock_clone:
        work_dir = env_manager.setup_repository("https://github.com/user/repo.git")
        assert isinstance(work_dir, Path)
        mock_clone.assert_called_once()

def test_setup_container(env_manager):
    with patch.object(env_manager, 'work_dir', Path(tempfile.mkdtemp())):
        mock_command = Mock()
        mock_command.dockerfile = "FROM python:3.9"
        mock_image = Mock()
        mock_container = Mock()
        
        env_manager.docker_client.images.build = Mock(return_value=(mock_image, None))
        env_manager.docker_client.containers.run = Mock(return_value=mock_container)
        
        env_manager.setup_container(mock_command)
        
        assert env_manager.container == mock_container
        env_manager.docker_client.images.build.assert_called_once()
        env_manager.docker_client.containers.run.assert_called_once_with(
            mock_image.id,
            detach=True,
            volumes={str(env_manager.work_dir): {'bind': '/workspace', 'mode': 'rw'}},
            working_dir='/workspace',
            environment={}
        )

@pytest.mark.asyncio
async def test_execute_command(env_manager):
    # Mock command
    mock_command = Mock()
    mock_command.execute = Mock(
        return_value=CommandResult(
            success=True,
            message="Command executed successfully",
            data={"result": "test output"}
        )
    )

    # Test config
    config = EnvironmentConfig(
        repo_url="https://github.com/test/repo.git"
    )

    # Mock setup methods
    env_manager.setup_repository = Mock()
    env_manager.setup_container = Mock()
    
    result = await env_manager.execute_command(mock_command, {"arg": "value"}, config)
    
    assert result.success is True
    assert result.message == "Command executed successfully"
    assert result.data == {"result": "test output"}

def test_run_in_container(env_manager):
    mock_container = Mock()
    mock_container.exec_run.return_value = (0, b"command output")
    env_manager.container = mock_container

    exit_code, output = env_manager.run_in_container("echo 'test'")
    
    assert exit_code == 0
    assert output == "command output"

def test_cleanup(env_manager):
    mock_container = Mock()
    env_manager.container = mock_container
    env_manager.work_dir = Path(tempfile.mkdtemp())

    env_manager.cleanup()

    mock_container.stop.assert_called_once()
    mock_container.remove.assert_called_once()
    assert env_manager.container is None
    assert env_manager.work_dir is None
import os
import pytest
from pathlib import Path
from typing import Dict, Any

from repopal.schemas.environment import EnvironmentConfig
from repopal.services.environment_manager import EnvironmentManager
from repopal.services.commands.base import Command


class TestCommand(Command):
    """Test command that just echoes some text"""
    
    dockerfile = """
FROM python:3.9-slim
WORKDIR /workspace
CMD ["bash"]
"""

    async def execute(self, args: Dict[str, Any], env_manager) -> Any:
        exit_code, output = env_manager.run_in_container("echo 'test successful'")
        return {
            "success": exit_code == 0,
            "message": output,
            "data": {"exit_code": exit_code}
        }

    def can_handle_event(self, event_type: str) -> bool:
        return True


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
    command = TestCommand()
    
    config = EnvironmentConfig(
        repo_url=str(test_repo),
        branch="master",
        environment_vars={"TEST_VAR": "test_value"}
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
        
        # Execute the command
        result = await command.execute({}, manager)
        assert result["success"]
        assert "test successful" in result["message"]
        
    finally:
        manager.cleanup()
