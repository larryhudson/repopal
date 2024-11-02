from .aider import AiderCommand
from .base import Command
from .factory import CommandFactory
from .find_replace import FindReplaceCommand

# Register all commands
CommandFactory.register(AiderCommand)
CommandFactory.register(FindReplaceCommand)

__all__ = ["Command", "CommandFactory", "AiderCommand", "FindReplaceCommand"]
