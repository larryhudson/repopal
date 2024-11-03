from typing import Dict, Any, Optional, List
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
    exit_code: Optional[int] = None
    output: Optional[str] = None
    error: Optional[str] = None
    changes: Optional[List[Dict[str, Any]]] = None
    data: Optional[Dict[str, Any]] = None
