from .base import Command
from .factory import CommandFactory
from .github_commands import AiderCommand, FindReplaceCommand

# Register all commands
CommandFactory.register(AiderCommand)
CommandFactory.register(FindReplaceCommand)

__all__ = ['Command', 'CommandFactory', 'AiderCommand', 'FindReplaceCommand']
