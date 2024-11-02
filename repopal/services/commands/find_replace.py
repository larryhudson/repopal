from pydantic import BaseModel
from repopal.services.environment_manager import EnvironmentManager

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

# Install required tools
RUN apt-get update && \
    apt-get install -y \
    findutils \
    sed \
    bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Keep container running
CMD ["tail", "-f", "/dev/null"]
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

    def get_execution_command(self, args: FindReplaceArgs) -> str:
        """Return the shell command to execute the find and replace operation"""
        # Escape special characters for sed
        find_pattern = args.find_pattern.replace("/", "\\/")
        replace_text = args.replace_text.replace("/", "\\/")
        
        # Wrap command in /bin/sh -c to ensure shell features work
        command = f"find . -type f -name '{args.file_pattern}' -exec sed -i 's/{find_pattern}/{replace_text}/g' {{}} + && echo 'Replacement complete' && cat {args.file_pattern}"
        return f"/bin/sh -c '{command}'"

    def can_handle_event(self, event_type: str) -> bool:
        # This command can be triggered by various events
        return True
