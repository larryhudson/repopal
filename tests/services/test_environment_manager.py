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

def test_execute_command(env_manager):
    mock_container = Mock()
    mock_container.exec_run.return_value = (0, b"command output")
    env_manager.container = mock_container

    result = env_manager.execute_command("echo 'test'")
    
    assert result["exit_code"] == 0
    assert result["output"] == "command output"

def test_cleanup(env_manager):
    mock_container = Mock()
    env_manager.container = mock_container
    env_manager.work_dir = Path(tempfile.mkdtemp())

    env_manager.cleanup()

    mock_container.stop.assert_called_once()
    mock_container.remove.assert_called_once()
    assert env_manager.container is None
    assert env_manager.work_dir is None
