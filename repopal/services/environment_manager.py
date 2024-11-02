import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import docker
import git
from docker.models.containers import Container

from repopal.schemas.command import CommandResult
from repopal.schemas.environment import EnvironmentConfig
from repopal.services.commands.base import Command


class EnvironmentManager:
    """Manages Docker environments and Git repositories for command execution"""

    def __init__(self):
        self.docker_client = docker.from_env()
        self.work_dir: Optional[Path] = None
        self.container: Container | None = None
        self.logger = logging.getLogger(__name__)

    def setup_repository(
        self, repo_url: str, branch: str = "main", github_token: Optional[str] = None
    ) -> Path:
        """Clone a repository into a temporary working directory

        Args:
            repo_url: The URL of the repository to clone
            branch: The branch to clone (defaults to "main")
            github_token: Optional GitHub token for authentication
        """
        self.work_dir = Path(tempfile.mkdtemp())

        if github_token and "github.com" in repo_url:
            # Insert token into GitHub URL
            url_parts = repo_url.split("://")
            if len(url_parts) == 2:
                repo_url = (
                    f"{url_parts[0]}://x-access-token:{github_token}@{url_parts[1]}"
                )

        git.Repo.clone_from(repo_url, self.work_dir, branch=branch)
        return self.work_dir

    def setup_container(
        self, command: Command, environment: Dict[str, str] = None
    ) -> None:
        """Create and start a Docker container with the working directory mounted"""
        if not self.work_dir:
            raise ValueError(
                "Working directory not set up. Call setup_repository first."
            )

        # Create a temporary directory for the Dockerfile
        with tempfile.TemporaryDirectory() as docker_build_dir:
            dockerfile_path = Path(docker_build_dir) / "Dockerfile"
            dockerfile_path.write_text(command.dockerfile)

            # Build the image
            image, _ = self.docker_client.images.build(
                path=str(docker_build_dir), rm=True, forcerm=True
            )

            # Run the container
            self.container = self.docker_client.containers.run(
                image,
                detach=True,
                volumes={str(self.work_dir): {"bind": "/workspace", "mode": "rw"}},
                working_dir="/workspace",
                environment=environment or {},
                user="1000:1000"  # Run as non-root user
            )

    async def execute_command(
        self, command: Command, args: Dict[str, Any], config: EnvironmentConfig
    ) -> CommandResult:
        """Execute a command in a configured environment"""
        try:
            # Set up the environment
            self.setup_repository(
                config.repo_url,
                config.branch,
                github_token=config.environment_vars.get("GITHUB_TOKEN"),
            )
            self.setup_container(command, config.environment_vars)

            # Get the command to execute
            shell_command = command.get_execution_command(args)

            # Execute in container
            exit_code, output = self.run_in_container(shell_command)

            if exit_code == 0:
                return CommandResult(
                    success=True,
                    message=f"Command {command.metadata.name} completed successfully",
                    data={"output": output if output else "No output"},
                )
            else:
                return CommandResult(
                    success=False,
                    message=f"Command failed with exit code {exit_code}",
                    data={"error": output},
                )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to execute command: {str(e)}",
                data={"error": str(e)},
            )
        finally:
            pass

    def run_in_container(self, command: str) -> Tuple[int, str]:
        """Execute a raw command in the Docker container"""
        if not self.container:
            raise ValueError("Container not set up. Call setup_container first.")

        # Wait for container to be ready
        self.container.reload()  # Refresh container state
        self.logger.info(f"Container status: {self.container.status}")
        if self.container.status != "running":
            self.container.start()

        exit_code, output = self.container.exec_run(command)
        return exit_code, output.decode("utf-8")

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
