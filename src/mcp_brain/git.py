"""知識の自動Git管理"""

import logging
from pathlib import Path

from git import InvalidGitRepositoryError, Repo
from git.exc import GitCommandError

logger = logging.getLogger(__name__)


class GitNotAvailableError(Exception):
    """Git連携が利用できない場合のエラー"""

    pass


class GitOperationError(Exception):
    """Git操作が失敗した場合のエラー（ツールエラーとして返す）"""

    pass


class GitManager:
    """知識の自動Git管理"""

    def __init__(self, knowledge_dir: Path) -> None:
        self.knowledge_dir = knowledge_dir
        self.repo: Repo = self._init_repo()

    def _init_repo(self) -> Repo:
        """リポジトリを初期化（必須）"""
        try:
            return Repo(self.knowledge_dir)
        except InvalidGitRepositoryError as e:
            raise GitNotAvailableError(
                f"Knowledge directory is not a git repository: {self.knowledge_dir}"
            ) from e

    def verify_remote(self) -> None:
        """リモート接続を検証（起動時チェック用）

        Raises:
            GitNotAvailableError: リモートが設定されていない、または接続できない場合
        """
        try:
            origin = self.repo.remote("origin")
        except ValueError as e:
            raise GitNotAvailableError(
                "No 'origin' remote configured. Please add a remote: "
                "git remote add origin <url>"
            ) from e

        try:
            # ls-remoteでリモート接続を確認（軽量な接続チェック）
            self.repo.git.ls_remote("--exit-code", "origin")
            logger.info("Remote connection verified: %s", origin.url)
        except GitCommandError as e:
            raise GitNotAvailableError(f"Cannot connect to remote 'origin': {e}") from e

    def commit_and_push(self, name: str, action: str) -> None:
        """変更をcommit + push

        手動変更への耐性:
        1. 未コミットの変更があれば先にコミット（手動変更を保護）
        2. 今回の変更をコミット
        3. プッシュ時に競合があればrebaseで解決

        Args:
            name: 知識名
            action: 操作（create, update, forget）

        Raises:
            GitOperationError: Git操作に失敗した場合
        """
        try:
            # 1. 不正なGit状態（rebase中など）があれば解除
            self._abort_incomplete_operations()

            # 2. 未コミットの手動変更があれば先にコミット（保護）
            self._commit_manual_changes()

            # 3. 今回の変更をステージング・コミット
            knowledge_path = Path(name) / "KNOWLEDGE.md"
            if action == "forget":
                self.repo.index.remove([str(knowledge_path)], working_tree=True)
            else:
                self.repo.index.add([str(knowledge_path)])

            message = f"{action}: {name}"
            self.repo.index.commit(message)
            logger.info("Committed: %s", message)

            # 4. プッシュ（競合時はrebaseで解決）
            self._push_with_rebase()

        except GitCommandError as e:
            raise GitOperationError(f"Git operation failed: {e}") from e

    def _abort_incomplete_operations(self) -> None:
        """不完全なGit操作を中止（rebase中、merge中など）"""
        git_dir = Path(self.repo.git_dir)

        try:
            if (git_dir / "rebase-merge").exists() or (
                git_dir / "rebase-apply"
            ).exists():
                logger.warning("Aborting incomplete rebase...")
                self.repo.git.rebase("--abort")

            if (git_dir / "MERGE_HEAD").exists():
                logger.warning("Aborting incomplete merge...")
                self.repo.git.merge("--abort")

            if (git_dir / "CHERRY_PICK_HEAD").exists():
                logger.warning("Aborting incomplete cherry-pick...")
                self.repo.git.cherry_pick("--abort")
        except GitCommandError as e:
            logger.warning("Failed to abort incomplete operation: %s", e)

    def _commit_manual_changes(self) -> None:
        """未コミットの手動変更をコミット（変更を保護）"""
        if not self.repo.is_dirty(untracked_files=True):
            return

        try:
            # 全ての変更をステージング
            self.repo.git.add("-A")
            # 手動変更としてコミット
            self.repo.index.commit("manual: uncommitted changes")
            logger.info("Committed manual changes")
        except GitCommandError as e:
            logger.warning("Failed to commit manual changes: %s", e)

    def _push_with_rebase(self) -> None:
        """プッシュ（競合時はrebaseで解決）"""
        origin = self.repo.remote("origin")
        try:
            origin.push()
            logger.info("Pushed to origin")
        except GitCommandError:
            # プッシュ失敗 → pull --rebase してリトライ
            logger.info("Push failed, trying pull --rebase...")
            try:
                origin.pull(rebase=True)
                origin.push()
                logger.info("Pushed after rebase")
            except GitCommandError as e:
                raise GitOperationError(f"Push failed after rebase: {e}") from e
