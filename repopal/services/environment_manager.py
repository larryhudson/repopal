import os
import docker
import tempfile
import git
from pathlib import Path
from typing import Optional, Dict, Any

class EnvironmentManager:
    """Manages Docker environments and Git repositories for command execution"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.work_dir: Optional[Path] = None
        self.container = None

    def setup_repository(self, repo_url: str, branch: str = "main") -> Path:
        """Clone a repository into a temporary working directory"""
        self.work_dir = Path(tempfile.mkdtemp())
        git.Repo.clone_from(repo_url, self.work_dir, branch=branch)
        return self.work_dir

    def setup_container(self, image: str, environment: Dict[str, str] = None) -> None:
        """Create and start a Docker container with the working directory mounted"""
        if not self.work_dir:
            raise ValueError("Working directory not set up. Call setup_repository first.")

        self.container = self.docker_client.containers.run(
            image,
            detach=True,
            volumes={
                str(self.work_dir): {
                    'bind': '/workspace',
                    'mode': 'rw'
                }
            },
            working_dir='/workspace',
            environment=environment or {}
        )

    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a command in the Docker container"""
        if not self.container:
            raise ValueError("Container not set up. Call setup_container first.")

        exit_code, output = self.container.exec_run(command)
        return {
            "exit_code": exit_code,
            "output": output.decode('utf-8')
        }

    def cleanup(self) -> None:
        """Clean up resources - stop container and remove working directory"""
        if self.container:
            self.container.stop()
            self.container.remove()
            self.container = None

        if self.work_dir:
            import shutil
            shutil.rmtree(self.work_dir)
            self.work_dir = None
