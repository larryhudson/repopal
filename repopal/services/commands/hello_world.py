from pydantic import BaseModel

from repopal.schemas.command import CommandMetadata
from repopal.services.commands.base import Command


class HelloWorldArgs(BaseModel):
    """Arguments for hello world operation"""

    pass


class HelloWorldCommand(Command[HelloWorldArgs]):
    """Command to write Hello World to a file"""

    dockerfile = """
FROM python:3.9-slim

CMD ["tail", "-f", "/dev/null"]
"""

    @property
    def metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="hello_world",
            description="Write Hello World to hello.txt",
            documentation="""
            Creates a file called hello.txt containing "Hello world"

            Required arguments:
            - working_dir: The repository directory to work in
            """,
        )

    def get_execution_command(self, args: HelloWorldArgs) -> str:
        """Return the shell command to write hello world"""
        return '/bin/sh -c \'echo "Hello world" > hello.txt && ls -l hello.txt && cat hello.txt\''

    def can_handle_event(self, event_type: str) -> bool:
        return True
