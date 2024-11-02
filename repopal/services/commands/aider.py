import os
import subprocess

from pydantic import BaseModel

from repopal.schemas.command import CommandMetadata, CommandResult
from repopal.services.commands.base import Command


class AiderArgs(BaseModel):
    """Arguments for running Aider"""

    prompt: str
    working_dir: str


class AiderCommand(Command[AiderArgs]):
    """Command to run Aider AI assistant"""

    @property
    def metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="aider",
            description="Run Aider AI assistant with a prompt",
            documentation="""
            Executes the Aider AI assistant in a repository with a specific prompt.

            Required arguments:
            - prompt: The instruction for Aider
            - working_dir: The repository directory to work in
            """,
        )

    def get_execution_command(self, args: AiderArgs) -> str:
        """Return the shell command to execute Aider"""
        return f"aider --no-git '{args.prompt}'"

    async def execute(self, args: AiderArgs) -> CommandResult:
        try:
            # Change to the working directory
            os.chdir(args.working_dir)

            # Run Aider with the prompt
            process = subprocess.run(
                ["aider", "--no-git", args.prompt],
                capture_output=True,
                text=True,
                check=True,
            )

            return CommandResult(
                success=True,
                message="Aider command executed successfully",
                data={"output": process.stdout},
            )
        except subprocess.CalledProcessError as e:
            return CommandResult(
                success=False,
                message=f"Aider command failed: {str(e)}",
                data={"error": e.stderr},
            )

    def can_handle_event(self, event_type: str) -> bool:
        # This command can be triggered by various events
        return True

    @property
    def dockerfile(self) -> str:
        return """FROM python:3.12-slim

        # Install git and required system dependencies
        RUN apt-get update && apt-get install -y \
            git \
            && rm -rf /var/lib/apt/lists/*

        # Install Aider
        RUN pip install --no-cache-dir aider-chat
        """
