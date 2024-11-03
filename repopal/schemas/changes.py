from typing import List, Literal
from pydantic import BaseModel

class TrackedChange(BaseModel):
    """Represents a tracked file change in the repository"""
    path: str
    diff: str

class UntrackedChange(BaseModel):
    """Represents an untracked file in the repository"""
    path: str
    content: str

class ChangeSet(BaseModel):
    """Represents a set of changes of a particular type"""
    type: Literal["diff", "untracked"]
    content: str | None = None
    files: List[UntrackedChange] | None = None

class RepositoryChanges(BaseModel):
    """Container for all changes in a repository"""
    tracked_changes: List[TrackedChange]
    untracked_changes: List[UntrackedChange]
