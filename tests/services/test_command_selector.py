from unittest.mock import patch

import pytest

from repopal.schemas.command import CommandMetadata
from repopal.schemas.webhook import StandardizedEvent
from repopal.services.command_selector import CommandSelectorService


class MockCommand:
    def __init__(self, name="test_command", description="Test command description"):
        self.metadata = CommandMetadata(
            name=name,
            description=description,
            documentation="Test command documentation",
        )


@pytest.fixture
def mock_llm_service():
    with patch("repopal.services.command_selector.LLMService") as mock:
        instance = mock.return_value
        instance.select_command.return_value = "test_command"
        instance.generate_command_args.return_value = {"arg1": "value1"}
        yield instance


@pytest.fixture
def mock_command_factory():
    with patch("repopal.services.command_selector.CommandFactory") as mock:
        mock_command = MockCommand()
        mock.get_commands_for_event.return_value = [mock_command]
        mock.get_command.return_value = mock_command
        yield mock


@pytest.fixture
def service():
    return CommandSelectorService()


@pytest.mark.asyncio
async def test_select_and_prepare_command_success(
    service, mock_llm_service, mock_command_factory
):
    # Arrange
    event = StandardizedEvent(
        provider="github",
        event_type="push",
        description="Test event description",
        payload={},
    )

    # Act
    command, args = await service.select_and_prepare_command(event)

    # Assert
    mock_command_factory.get_commands_for_event.assert_called_once_with(
        event.event_type
    )
    mock_llm_service.select_command.assert_called_once()
    mock_llm_service.generate_command_args.assert_called_once()
    assert isinstance(command, MockCommand)
    assert args == {"arg1": "value1"}


@pytest.mark.asyncio
async def test_select_and_prepare_command_no_commands(
    service, mock_llm_service, mock_command_factory
):
    # Arrange
    event = StandardizedEvent(
        provider="github",
        event_type="unknown_event",
        description="Test event description",
        payload={},
    )
    mock_command_factory.get_commands_for_event.return_value = []

    # Act & Assert
    with pytest.raises(ValueError, match="No commands available"):
        await service.select_and_prepare_command(event)
import pytest
from unittest.mock import Mock, patch
from repopal.services.command_selector import CommandSelectorService
from repopal.schemas.webhook import StandardizedEvent
from repopal.schemas.command import CommandMetadata, CommandType
from repopal.services.commands.base import Command

class MockCommand:
    def __init__(self, name="test_command", description="Test command description"):
        self.metadata = CommandMetadata(
            name=name,
            description=description,
            documentation="Test command documentation",
            command_type=CommandType.find_replace  # Adding required command_type
        )

@pytest.fixture
def mock_llm_service():
    with patch('repopal.services.command_selector.LLMService') as mock:
        instance = mock.return_value
        instance.select_command.return_value = "test_command"
        instance.generate_command_args.return_value = {"arg1": "value1"}
        yield instance

@pytest.fixture
def mock_command_factory():
    with patch('repopal.services.command_selector.CommandFactory') as mock:
        mock_command = MockCommand()
        mock.get_commands_for_event.return_value = [mock_command]
        mock.get_command.return_value = mock_command
        yield mock

@pytest.fixture
def service():
    return CommandSelectorService()

async def test_select_and_prepare_command_success(service, mock_llm_service, mock_command_factory):
    # Arrange
    event = StandardizedEvent(
        provider="github",
        event_type="push",
        description="Test event description",
        payload={}
    )

    # Act
    command, args = await service.select_and_prepare_command(event)

    # Assert
    mock_command_factory.get_commands_for_event.assert_called_once_with(event.event_type)
    mock_llm_service.select_command.assert_called_once()
    mock_llm_service.generate_command_args.assert_called_once()
    assert isinstance(command, MockCommand)
    assert args == {"arg1": "value1"}

async def test_select_and_prepare_command_no_commands(service, mock_llm_service, mock_command_factory):
    # Arrange
    event = StandardizedEvent(
        provider="github",
        event_type="unknown_event",
        description="Test event description",
        payload={}
    )
    mock_command_factory.get_commands_for_event.return_value = []

    # Act & Assert
    with pytest.raises(ValueError, match="No commands available for this event type"):
        await service.select_and_prepare_command(event)

pytestmark = pytest.mark.asyncio
