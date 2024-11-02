from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel

class CommandType(str, Enum):
    """Types of commands that can be executed"""
    AIDER = "aider"
    FIND_REPLACE = "find_replace"
    SHELL = "shell"

class CommandMetadata(BaseModel):
    """Metadata about a command"""
    name: str
    description: str
    documentation: str
    command_type: CommandType

class CommandArgs(BaseModel):
    """Base class for command arguments"""
    pass

class CommandResult(BaseModel):
    """Result of executing a command"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
