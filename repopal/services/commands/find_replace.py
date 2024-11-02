import os
import subprocess

from pydantic import BaseModel

from repopal.schemas.command import CommandMetadata, CommandResult
from repopal.services.commands.base import Command


class FindReplaceArgs(BaseModel):
    """Arguments for find and replace operation"""

    find_pattern: str
    replace_text: str
    file_pattern: str = "*"  # e.g. "*.py" for Python files
    working_dir: str


class FindReplaceCommand(Command[FindReplaceArgs]):
    """Command to perform find and replace operations"""

    dockerfile = """
FROM python:3.9-slim
WORKDIR /workspace
RUN apt-get update && apt-get install -y findutils sed
"""

    @property
    def metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="find_replace",
            description="Perform find and replace across files",
            documentation="""
            Executes a find and replace operation across files in a repository.

            Required arguments:
            - find_pattern: Text to find
            - replace_text: Text to replace with
            - working_dir: The repository directory to work in

            Optional arguments:
            - file_pattern: Glob pattern for files to process (default: *)
            """,
        )

    async def execute(self, args: FindReplaceArgs, env_manager: 'EnvironmentManager') -> CommandResult:
        try:
            # Construct the find and replace command
            command = f"find . -type f -name '{args.file_pattern}' -exec sed -i 's/{args.find_pattern}/{args.replace_text}/g' {{}} +"
            
            # Execute in container
            exit_code, output = env_manager.run_in_container(command)
            
            if exit_code == 0:
                return CommandResult(
                    success=True,
                    message="Find and replace completed successfully",
                    data={"output": output if output else "No output"}
                )
            else:
                return CommandResult(
                    success=False,
                    message=f"Find and replace failed with exit code {exit_code}",
                    data={"error": output}
                )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Find and replace failed: {str(e)}",
                data={"error": str(e)}
            )

    def can_handle_event(self, event_type: str) -> bool:
        # This command can be triggered by various events
        return True
