from typing import Dict, Type, List
from repopal.services.commands.base import Command
from repopal.schemas.command import CommandMetadata

class CommandFactory:
    """Factory for creating and managing commands"""
    
    _commands: Dict[str, Type[Command]] = {}

    @classmethod
    def register(cls, command_class: Type[Command]) -> None:
        """Register a new command"""
        command_instance = command_class()
        cls._commands[command_instance.metadata.name] = command_class

    @classmethod
    def get_command(cls, command_name: str) -> Command:
        """Get a command instance by name"""
        if command_name not in cls._commands:
            raise ValueError(f"Command {command_name} not found")
        return cls._commands[command_name]()

    @classmethod
    def list_commands(cls) -> List[CommandMetadata]:
        """List all available commands"""
        return [cmd().metadata for cmd in cls._commands.values()]

    @classmethod
    def get_commands_for_event(cls, event_type: str) -> List[Command]:
        """Get all commands that can handle a specific event type"""
        return [
            cmd() for cmd in cls._commands.values()
            if cmd().can_handle_event(event_type)
        ]
