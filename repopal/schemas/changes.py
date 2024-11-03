from typing import List, Optional
from pydantic import BaseModel

class UnTrackedFile(BaseModel):
    """Represents an untracked file in the repository"""
    path: str
    content: str

class ChangeSet(BaseModel):
    """Represents a set of changes in the repository"""
    type: str  # 'diff' or 'untracked'
    content: Optional[str] = None  # For diff content
    files: Optional[List[UnTrackedFile]] = None  # For untracked files

class RepositoryChanges(BaseModel):
    """Container for all changes in a repository"""
    changes: List[ChangeSet]
