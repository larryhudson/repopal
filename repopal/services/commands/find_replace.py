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
                check=True,
            )

            return CommandResult(
                success=True,
                message="Find and replace completed successfully",
                data={"output": process.stdout if process.stdout else "No output"},
            )
        except subprocess.CalledProcessError as e:
            return CommandResult(
                success=False,
                message=f"Find and replace failed: {str(e)}",
                data={"error": e.stderr},
            )

    def can_handle_event(self, event_type: str) -> bool:
        # This command can be triggered by various events
        return True
