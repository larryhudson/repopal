import logging
from typing import Any, Dict

from repopal.schemas.service_handler import StandardizedEvent
from repopal.services.commands.base import Command
from repopal.services.commands.factory import CommandFactory
from repopal.services.llm import LLMService


class CommandSelectorService:
    def __init__(self):
        self.llm = LLMService()
        self.logger = logging.getLogger(__name__)

    async def select_and_prepare_command(
        self, event: StandardizedEvent
    ) -> tuple[Command, Dict[str, Any]]:
        """
        Select the most appropriate command and prepare its arguments based on the event.
        Returns a tuple of (command_instance, command_args).
        """
        # Get all available commands that can handle this event type
        available_commands = CommandFactory.get_commands_for_event(event.event_type)

        if not available_commands:
            raise ValueError("No commands available for this event type")

        # Prepare command descriptions for LLM
        command_descriptions = [
            {"name": cmd.metadata.name, "description": cmd.metadata.description}
            for cmd in available_commands
        ]

        # Use LLM to select the best command
        selected_command_name = await self.llm.select_command(
            event.user_request, command_descriptions
        )
        self.logger.info(f"LLM selected command: {selected_command_name}")

        # Get the selected command instance
        command = CommandFactory.get_command(selected_command_name)

        # Use LLM to generate appropriate arguments
        command_args = await self.llm.generate_command_args(
            event.user_request, command.metadata.documentation
        )
        self.logger.info(f"LLM generated arguments: {command_args}")

        return command, command_args
