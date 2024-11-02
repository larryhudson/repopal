from pydantic import BaseModel
from typing import Dict, Optional

class EnvironmentConfig(BaseModel):
    """Configuration for a command execution environment"""
    repo_url: str
    branch: Optional[str] = "main"
    environment_vars: Optional[Dict[str, str]] = None
