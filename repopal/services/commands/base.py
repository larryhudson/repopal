from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from repopal.schemas.command import CommandMetadata, CommandArgs, CommandResult

TArgs = TypeVar('TArgs', bound=CommandArgs)

class Command(Generic[TArgs], ABC):
    """Base class for all commands"""
    
    @property
    @abstractmethod
    def metadata(self) -> CommandMetadata:
        """
        Return metadata about the command.
        Should include:
        - name: str
        - description: str
        - documentation: str (detailed usage instructions and examples)
        """
        pass

    @property
    @abstractmethod
    def dockerfile(self) -> str:
        """
        Return the Dockerfile contents for building this command's container.
        Must include all necessary dependencies and setup instructions.
        """
        pass

    def convert_args(self, args: Dict[str, Any]) -> TArgs:
        """Convert dictionary arguments to the appropriate type"""
        if not hasattr(self, '_args_type'):
            # Get the concrete type bound to TArgs for this class instance
            self._args_type = self.__class__.__orig_bases__[0].__args__[0]
        return self._args_type(**args)

    @abstractmethod
    def get_execution_command(self, args: TArgs) -> str:
        """
        Return the shell command to execute in the container
        """
        pass

    @abstractmethod
    def can_handle_event(self, event_type: str) -> bool:
        """Determine if this command can handle the given event type"""
        pass
