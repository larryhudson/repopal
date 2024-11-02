from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel

class CommandType(str, Enum):
    """Types of commands that can be executed"""
    GITHUB_PR = "github_pr"
    GITHUB_ISSUE = "github_issue"
    # Add more command types as needed

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
