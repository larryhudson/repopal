from typing import Dict, Any, Optional
from pydantic import BaseModel

class CommandMetadata(BaseModel):
    """Metadata about a command"""
    name: str
    description: str
    documentation: str

class CommandArgs(BaseModel):
    """Base class for command arguments"""
    pass

class CommandResult(BaseModel):
    """Result of executing a command"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
