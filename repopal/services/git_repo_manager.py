import logging
from pathlib import Path
from typing import Optional

import git


class GitRepoManager:
    """Class to create PRs on GitHub"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.repo: git.Repo | None = None


    def clone_repo(
        self, repo_url: str, branch: str = "main", github_token: Optional[str] = None
    ) -> Path:
        """Clone a repository into a temporary working directory

        Args:
            repo_url: The URL of the repository to clone
            branch: The branch to clone (defaults to "main")
            github_token: Optional GitHub token for authentication
        """
        if not self.work_dir:
            self.work_dir = Path(tempfile.mkdtemp())
            self.logger.debug(f"Created working directory: {self.work_dir}")
            self.logger.debug(
                f"Working directory absolute path: {self.work_dir.absolute()}"
            )

        if github_token and "github.com" in repo_url:
            # Insert token into GitHub URL
            url_parts = repo_url.split("://")
            if len(url_parts) == 2:
                repo_url = (
                    f"{url_parts[0]}://x-access-token:{github_token}@{url_parts[1]}"
                )

        self.repo = git.Repo.clone_from(repo_url, self.work_dir, branch=branch)
        return self.work_dir

    def create_branch(self, branch_name: str) -> None:
        """Create a new branch in the repository
        Args:
            work_dir: The path to the repository working directory
            branch_name: The name of the new branch
        """
        if not self.repo:
            raise ValueError("Repository not initialized")
        self.repo.git.checkout("HEAD", b="main")
        # TODO: check if branch exists, raise error if it does
        self.repo.git.checkout("HEAD", b=branch_name)
        self.logger.debug(f"Created branch: {branch_name}")

    def commit_changes(self, commit_message: str) -> None:
        """Commit changes to the repository
        Args:
            work_dir: The path to the repository working directory
            commit_message: The commit message
        """
        if not self.repo:
            raise ValueError("Repository not initialized")
        self.repo.git.add(".")
        self.repo.index.commit(commit_message)
        self.logger.debug(f"Committed changes with message: {commit_message}")

    def push_changes(self, branch_name: str) -> None:
        """Push changes to the remote repository
        Args:
            work_dir: The path to the repository working directory
            branch_name: The name of the branch to push
        """
        if not self.repo:
            raise ValueError("Repository not initialized")
        self.repo.remotes.origin.push(branch_name)
        self.logger.debug(f"Pushed changes to branch: {branch_name}")

    def push_changes_to_new_branch(self, commit_message: str, branch_name: str) -> None:
        """Push changes to a new branch in the remote repository
        Args:
            work_dir: The path to the repository working directory
            branch_name: The name of the new branch
            base_branch: The name of the base branch to create the new branch from
        """
        if not self.repo:
            raise ValueError("Repository not initialized")

        self.create_branch(branch_name)
        self.commit_changes(commit_message)
        self.push_changes(branch_name)




