from typing import List

from pydantic import BaseModel


class TrackedChange(BaseModel):
    """Represents a tracked file change in the repository"""

    path: str
    diff: str


class UntrackedChange(BaseModel):
    """Represents an untracked file in the repository"""

    path: str
    content: str


class RepositoryChanges(BaseModel):
    """Container for all changes in a repository"""

    tracked_changes: List[TrackedChange]
    untracked_changes: List[UntrackedChange]
