"""Skillの自動Git管理"""

import logging
from pathlib import Path

from git import InvalidGitRepositoryError, Repo
from git.exc import GitCommandError

logger = logging.getLogger(__name__)


class GitManager:
    """Skillの自動Git管理"""

    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir
        self.repo: Repo | None = None
        self._init_repo()

    def _init_repo(self) -> None:
        """リポジトリを初期化"""
        try:
            self.repo = Repo(self.skills_dir)
        except InvalidGitRepositoryError:
            logger.warning(
                "Skills directory is not a git repository: %s", self.skills_dir
            )
            self.repo = None

    def commit_and_push(self, skill_name: str, action: str) -> bool:
        """変更をcommit + push

        Args:
            skill_name: スキル名
            action: 操作（create, update, delete）

        Returns:
            成功したかどうか
        """
        if self.repo is None:
            logger.debug("Git repository not available, skipping commit")
            return False

        try:
            # ファイルをステージング
            skill_path = f"{skill_name}/SKILL.md"
            if action == "delete":
                self.repo.index.remove([skill_path], working_tree=True)
            else:
                self.repo.index.add([skill_path])

            # コミット
            message = f"{action}: {skill_name}"
            self.repo.index.commit(message)
            logger.info("Committed: %s", message)

            # プッシュ
            self._push()
            return True

        except GitCommandError as e:
            logger.error("Git operation failed: %s", e)
            return False

    def _push(self) -> None:
        """リモートにプッシュ"""
        if self.repo is None:
            return

        try:
            origin = self.repo.remote("origin")
            origin.push()
            logger.info("Pushed to origin")
        except (ValueError, GitCommandError) as e:
            logger.warning("Push failed (no remote or error): %s", e)

