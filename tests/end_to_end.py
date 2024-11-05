import logging

import pytest

from repopal.schemas.environment import EnvironmentConfig
from repopal.schemas.service_handler import StandardizedEvent
from repopal.services.command_selector import CommandSelectorService
from repopal.services.commands.find_replace import FindReplaceCommand
from repopal.services.environment_manager import EnvironmentManager
from repopal.services.llm import LLMService
from repopal.services.service_handlers.base import ResponseType
from repopal.services.service_handlers.github import GitHubHandler

pytestmark = pytest.mark.integration



@pytest.mark.asyncio
async def test_end_to_end_workflow(test_repo, webhook_signature):
    """Integration test that simulates full workflow from webhook to command execution"""
    import asyncio

    # Create new event loop for this test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Setup services
        webhook_secret = "test_secret"
        service_handler = GitHubHandler(webhook_secret=webhook_secret)
        llm_service = LLMService()
        command_selector = CommandSelectorService(llm=llm_service)
        environment_manager = EnvironmentManager()

        # Create a test issue payload
        issue_payload = {
            "action": "opened",
            "issue": {
                "title": "Update greeting",
                "body": "Please replace all occurrences of 'world' with 'everyone' in test.txt",
                "user": {"login": "user1"},
            },
            "repository": {
                "full_name": str(test_repo),
                "html_url": f"https://github.com/{test_repo}",
            },
            "sender": {"login": "user1"},
        }

        # Generate webhook signature
        headers, payload_bytes = webhook_signature(webhook_secret, issue_payload)

        # Validate webhook
        assert service_handler.validate_webhook(headers, issue_payload) is True

        # Process webhook to get standardized event
        event = service_handler.process_webhook(issue_payload)
        assert isinstance(event, StandardizedEvent)
        assert event.event_type == "issue"
        assert event.action == "opened"

        # Select command and generate arguments
        command, args = await command_selector.select_and_prepare_command(event)
        assert command is not None, "Should select a command"
        assert args is not None, "Should generate arguments"

        # Set up environment
        environment_config = EnvironmentConfig(
            repo_url=str(test_repo),
            branch="main",
            environment_vars={},
        )

        # Set up repository and container
        work_dir = environment_manager.setup_repository(
            environment_config.repo_url, environment_config.branch
        )
        assert work_dir.exists()
        environment_manager.setup_container(command)
        assert environment_manager.container is not None

        # Use args directly since they're already properly typed from command.convert_args()
        command_args = args

        # Send initial received status
        thread_id = service_handler.send_response(
            payload=issue_payload,
            message=await llm_service.generate_status_message(
                "received", {"user_request": event.user_request}
            ),
            response_type=ResponseType.INITIAL,
        )

        # Send command selected status
        thread_id = service_handler.send_response(
            payload=issue_payload,
            message=await llm_service.generate_status_message(
                "selected",
                {
                    "user_request": event.user_request,
                    "command_name": command.__class__.__name__,
                    "command_args": args,
                },
            ),
            response_type=ResponseType.UPDATE,
            thread_id=thread_id,
        )

        # Execute the command
        result = await environment_manager.execute_command(
            command, command_args, environment_config
        )

        # Log the result for debugging
        logging.debug(f"Command execution result: {result}")

        # Get changes and generate summary
        repository_changes = environment_manager.get_repository_changes()
        changes_summary = await llm_service.generate_change_summary(
            event.user_request, command.__class__.__name__, result.output, repository_changes
        )

        # Send final status with changes
        service_handler.send_response(
            payload=issue_payload,
            message=await llm_service.generate_status_message(
                "completed",
                {
                    "user_request": event.user_request,
                    "changes_summary": changes_summary,
                },
            ),
            response_type=ResponseType.FINAL,
            thread_id=thread_id,
        )

        # Verify command executed successfully
        assert result.success

        # Verify the changes were made
        changes = environment_manager.get_repository_changes()
        assert changes, "Should have detected changes in the repository"

        # For find/replace command, verify the specific changes
        if isinstance(command, FindReplaceCommand):
            # Check the diff content
            diff_changes = next((c for c in changes.tracked_changes), None)
            assert diff_changes, "Should have tracked changes"
            assert "everyone" in diff_changes.diff
            assert "-Hello world!" in diff_changes.diff
            assert "+Hello everyone!" in diff_changes.diff

    finally:
        environment_manager.cleanup()
        # Clean up the event loop
        loop.close()
from typing import List
from pydantic import BaseModel

from repopal.schemas.command import CommandMetadata
from repopal.services.commands.base import Command


class ArchitectureDiagramArgs(BaseModel):
    """Arguments for architecture diagram generation"""
    output_format: str = "mermaid"  # or "plantuml"
    include_patterns: List[str] = ["*.py"]  # file patterns to analyze
    exclude_patterns: List[str] = ["tests/*", "venv/*"]  # patterns to exclude
    output_path: str = "docs/architecture.md"  # where to save the diagram


class ArchitectureDiagramCommand(Command[ArchitectureDiagramArgs]):
    """Command to generate architecture diagrams from Python code"""

    dockerfile = """
FROM python:3.9-slim

# Install required tools
RUN pip install --no-cache-dir \
    pylint \
    graphviz \
    && apt-get update \
    && apt-get install -y \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Keep container running
CMD ["tail", "-f", "/dev/null"]
"""

    @property
    def metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="architecture_diagram",
            description="Generate architecture diagrams from Python code",
            documentation="""
            Analyzes Python code and generates architecture diagrams using pyreverse.
            
            Optional arguments:
            - output_format: Format of the diagram (mermaid or plantuml)
            - include_patterns: List of file patterns to analyze (default: *.py)
            - exclude_patterns: List of patterns to exclude (default: tests/*, venv/*)
            - output_path: Where to save the diagram (default: docs/architecture.md)
            """,
        )

    def get_execution_command(self, args: ArchitectureDiagramArgs) -> str:
        """Return the shell command to execute the command"""
        # Convert args to proper type
        command_args = self.convert_args(args)
        
        # Create the output directory
        mkdir_cmd = f"mkdir -p $(dirname {command_args.output_path})"
        
        # Generate class diagram using pyreverse
        pyreverse_cmd = "pyreverse"
        for pattern in command_args.include_patterns:
            pyreverse_cmd += f" $(find . -name '{pattern}')"
        for pattern in command_args.exclude_patterns:
            pyreverse_cmd += f" --ignore={pattern}"
        pyreverse_cmd += " -o dot"  # Output in DOT format
        
        # Convert to desired format
        if command_args.output_format == "mermaid":
            # Convert dot to mermaid format and wrap in markdown
            convert_cmd = f"""
            echo '# Architecture Diagram\n\n```mermaid' > {command_args.output_path} && \
            dot -Txdot classes.dot | python -c 'import sys; \
            import re; \
            dot = sys.stdin.read(); \
            # Basic DOT to Mermaid conversion \
            mermaid = dot.replace("digraph", "classDiagram"); \
            mermaid = re.sub(r"-> (\w+)", r"..> \1", mermaid); \
            print(mermaid)' >> {command_args.output_path} && \
            echo '```' >> {command_args.output_path} && \
            rm classes.dot packages.dot
            """
        else:  # plantuml
            convert_cmd = f"""
            echo '@startuml' > {command_args.output_path} && \
            dot -Txdot classes.dot | python -c 'import sys; \
            import re; \
            dot = sys.stdin.read(); \
            # Basic DOT to PlantUML conversion \
            uml = re.sub(r"-> (\w+)", r"--|> \1", dot); \
            print(uml)' >> {command_args.output_path} && \
            echo '@enduml' >> {command_args.output_path} && \
            rm classes.dot packages.dot
            """
        
        # Combine all commands
        return f"/bin/sh -c '{mkdir_cmd} && {pyreverse_cmd} && {convert_cmd}'"

    def can_handle_event(self, event_type: str) -> bool:
        # This command can be triggered by various events
        return True
