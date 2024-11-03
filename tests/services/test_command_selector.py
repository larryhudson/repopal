import asyncio
from unittest.mock import patch

import pytest

from repopal.schemas.command import CommandMetadata
from repopal.schemas.service_handler import StandardizedEvent
from repopal.services.command_selector import CommandSelectorService


class MockCommand:
    def __init__(self, name="test_command", description="Test command description"):
        self.metadata = CommandMetadata(
            name=name,
            description=description,
            documentation="Test command documentation",
        )


@pytest.fixture
def service():
    with patch("repopal.services.llm.LLMService") as mock_class:
        instance = mock_class.return_value
        # Mock async methods
        instance.select_command.return_value = "test_command"
        instance.select_command.return_value = asyncio.Future()
        instance.select_command.return_value.set_result("test_command")

        instance.generate_command_args.return_value = asyncio.Future()
        instance.generate_command_args.return_value.set_result({"arg1": "value1"})
        service = CommandSelectorService()
        service.llm = instance  # Explicitly set the mock instance
        yield service, instance


@pytest.fixture
def mock_command_factory():
    with patch("repopal.services.command_selector.CommandFactory") as mock:
        mock_command = MockCommand()
        mock.get_commands_for_event.return_value = [mock_command]
        mock.get_command.return_value = mock_command
        yield mock


async def test_select_and_prepare_command_success(service, mock_command_factory):
    service_instance, mock_llm = service
    # Arrange
    event = StandardizedEvent(
        provider="github",
        event_type="push",
        payload={},
        user_request="Test user request",
        raw_payload={"test": "data"},
    )

    # Act
    command, args = await service_instance.select_and_prepare_command(event)

    # Assert
    mock_command_factory.get_commands_for_event.assert_called_once_with(
        event.event_type
    )
    mock_llm.select_command.assert_called_once_with(
        "Test user request",
        [{"name": "test_command", "description": "Test command description"}],
    )
    mock_llm.generate_command_args.assert_called_once()
    assert isinstance(command, MockCommand)
    assert args == {"arg1": "value1"}


async def test_select_and_prepare_command_no_commands(service, mock_command_factory):
    service_instance, _ = service
    # Arrange
    event = StandardizedEvent(
        provider="github",
        event_type="unknown_event",
        payload={},
        user_request="Test user request",
        raw_payload={"test": "data"},
    )
    mock_command_factory.get_commands_for_event.return_value = []

    # Act & Assert
    with pytest.raises(ValueError, match="No commands available for this event type"):
        await service_instance.select_and_prepare_command(event)


pytestmark = pytest.mark.asyncio
