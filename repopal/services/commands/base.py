from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from repopal.schemas.command import CommandMetadata, CommandArgs, CommandResult

TArgs = TypeVar('TArgs', bound=CommandArgs)

class Command(Generic[TArgs], ABC):
    """Base class for all commands"""
    
    @property
    @abstractmethod
    def metadata(self) -> CommandMetadata:
        """Return metadata about the command"""
        pass

    @abstractmethod
    async def execute(self, args: TArgs) -> CommandResult:
        """Execute the command with the given arguments"""
        pass

    @abstractmethod
    def can_handle_event(self, event_type: str) -> bool:
        """Determine if this command can handle the given event type"""
        pass
