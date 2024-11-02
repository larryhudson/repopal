import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from repopal.services.environment_manager import EnvironmentManager

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
        mock_container = Mock()
        env_manager.docker_client.containers.run = Mock(return_value=mock_container)
        
        env_manager.setup_container("python:3.9")
        
        assert env_manager.container == mock_container
        env_manager.docker_client.containers.run.assert_called_once()

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
        repo_url="https://github.com/test/repo.git",
        docker_image="python:3.9"
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
