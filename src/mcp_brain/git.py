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

    def _ensure_clean_state(self) -> None:
        """不正なGit状態を強制的に解除してクリーンな状態にする

        以下の状態を検出・解除:
        - rebase中 → abort
        - merge中 → abort
        - cherry-pick中 → abort
        - 未コミットの変更 → 破棄

        Raises:
            GitOperationError: 状態のリセットに失敗した場合
        """
        git_dir = Path(self.repo.git_dir)

        try:
            # rebase中を検出・解除
            if (git_dir / "rebase-merge").exists() or (
                git_dir / "rebase-apply"
            ).exists():
                logger.warning("Detected rebase in progress, aborting...")
                self.repo.git.rebase("--abort")

            # merge中を検出・解除
            if (git_dir / "MERGE_HEAD").exists():
                logger.warning("Detected merge in progress, aborting...")
                self.repo.git.merge("--abort")

            # cherry-pick中を検出・解除
            if (git_dir / "CHERRY_PICK_HEAD").exists():
                logger.warning("Detected cherry-pick in progress, aborting...")
                self.repo.git.cherry_pick("--abort")

            # 未コミットの変更を破棄（ステージング含む）
            if self.repo.is_dirty(untracked_files=True):
                logger.warning("Detected uncommitted changes, discarding...")
                self.repo.git.reset("--hard", "HEAD")
                self.repo.git.clean("-fd")

        except GitCommandError as e:
            raise GitOperationError(
                f"Failed to reset git state: {e}. "
                "Please manually fix the repository state."
            ) from e

    def _sync_with_remote(self) -> None:
        """リモートと同期（pull）

        Raises:
            GitOperationError: 同期に失敗した場合
        """
        try:
            origin = self.repo.remote("origin")
            origin.pull(rebase=True)
            logger.info("Synced with remote")
        except GitCommandError as e:
            # pull失敗時は状態をリセットして再試行
            logger.warning("Pull failed, resetting to remote state: %s", e)
            try:
                self.repo.git.fetch("origin")
                self.repo.git.reset("--hard", "origin/HEAD")
            except GitCommandError as reset_error:
                raise GitOperationError(
                    f"Failed to sync with remote: {reset_error}"
                ) from reset_error

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

    def commit_and_push(self, name: str, action: str, scope: str | None = None) -> None:
        """変更をcommit + push

        Args:
            name: 知識名
            action: 操作（create, update, forget）
            scope: スコープ（None の場合は global）

        Raises:
            GitOperationError: Git操作に失敗した場合
        """
        # 操作前に不正な状態をリセット
        self._ensure_clean_state()

        # リモートと同期
        self._sync_with_remote()

        try:
            # ファイルをステージング（knowledge_dir相対パス、スコープを含む）
            scope_prefix = Path(scope) if scope else Path("global")
            knowledge_path = scope_prefix / name / "KNOWLEDGE.md"
            if action == "forget":
                self.repo.index.remove([str(knowledge_path)], working_tree=True)
            else:
                self.repo.index.add([str(knowledge_path)])

            # コミット
            message = f"{action}: {name}"
            self.repo.index.commit(message)
            logger.info("Committed: %s", message)

            # プッシュ
            self._push()

        except GitCommandError as e:
            raise GitOperationError(f"Git operation failed: {e}") from e

    def _push(self) -> None:
        """リモートにプッシュ"""
        origin = self.repo.remote("origin")
        origin.push()
        logger.info("Pushed to origin")
