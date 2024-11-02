import os
import subprocess
from typing import Dict, Any
from pydantic import BaseModel

from repopal.services.commands.base import Command
from repopal.schemas.command import CommandMetadata, CommandResult, CommandType

class AiderArgs(BaseModel):
    """Arguments for running Aider"""
    prompt: str
    working_dir: str

class FindReplaceArgs(BaseModel):
    """Arguments for find and replace operation"""
    find_pattern: str
    replace_text: str
    file_pattern: str = "*"  # e.g. "*.py" for Python files
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
            command_type=CommandType.AIDER
        )

    async def execute(self, args: AiderArgs) -> CommandResult:
        try:
            # Change to the working directory
            os.chdir(args.working_dir)
            
            # Run Aider with the prompt
            process = subprocess.run(
                ["aider", "--no-git", args.prompt],
                capture_output=True,
                text=True,
                check=True
            )
            
            return CommandResult(
                success=True,
                message="Aider command executed successfully",
                data={"output": process.stdout}
            )
        except subprocess.CalledProcessError as e:
            return CommandResult(
                success=False,
                message=f"Aider command failed: {str(e)}",
                data={"error": e.stderr}
            )

    def can_handle_event(self, event_type: str) -> bool:
        # This command can be triggered by various events
        return True

class FindReplaceCommand(Command[FindReplaceArgs]):
    """Command to perform find and replace operations"""

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
            command_type=CommandType.FIND_REPLACE
        )

    async def execute(self, args: FindReplaceArgs) -> CommandResult:
        try:
            # Change to the working directory
            os.chdir(args.working_dir)
            
            # Use find and sed for the operation
            process = subprocess.run(
                f"find . -type f -name '{args.file_pattern}' -exec sed -i '' 's/{args.find_pattern}/{args.replace_text}/g' {{}} +",
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            
            return CommandResult(
                success=True,
                message="Find and replace completed successfully",
                data={"output": process.stdout if process.stdout else "No output"}
            )
        except subprocess.CalledProcessError as e:
            return CommandResult(
                success=False,
                message=f"Find and replace failed: {str(e)}",
                data={"error": e.stderr}
            )

    def can_handle_event(self, event_type: str) -> bool:
        # This command can be triggered by various events
        return True
