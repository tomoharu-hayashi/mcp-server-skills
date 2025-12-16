from __future__ import annotations

from pathlib import Path

import pytest
from git import InvalidGitRepositoryError
from git.exc import GitCommandError

import mcp_brain.git as gitmod


class FakeIndex:
    def __init__(self) -> None:
        self.added: list[list[str]] = []
        self.removed: list[tuple[list[str], bool]] = []
        self.commits: list[str] = []

    def add(self, paths: list[str]) -> None:
        self.added.append(list(paths))

    def remove(self, paths: list[str], *, working_tree: bool) -> None:
        self.removed.append((list(paths), working_tree))

    def commit(self, message: str) -> None:
        self.commits.append(message)


class FakeRemote:
    def __init__(
        self,
        url: str = "git@example.com/repo.git",
        *,
        push_failures: int = 0,
        pull_raises: bool = False,
    ) -> None:
        self.url = url
        self._push_failures = push_failures
        self._pull_raises = pull_raises
        self.push_calls = 0
        self.pull_calls = 0

    def push(self) -> None:
        self.push_calls += 1
        if self.push_calls <= self._push_failures:
            raise GitCommandError("push", 1)

    def pull(self, *, rebase: bool) -> None:
        self.pull_calls += 1
        if self._pull_raises:
            raise GitCommandError("pull", 1)
        assert rebase is True


class FakeGit:
    def __init__(self, *, ls_remote_raises: bool = False) -> None:
        self.calls: list[tuple[str, tuple[object, ...]]] = []
        self._ls_remote_raises = ls_remote_raises

    def ls_remote(self, *_args: object) -> None:
        self.calls.append(("ls_remote", _args))
        if self._ls_remote_raises:
            raise GitCommandError("ls-remote", 2)

    def add(self, *_args: object) -> None:
        self.calls.append(("add", _args))

    def rebase(self, *_args: object) -> None:
        self.calls.append(("rebase", _args))

    def merge(self, *_args: object) -> None:
        self.calls.append(("merge", _args))

    def cherry_pick(self, *_args: object) -> None:
        self.calls.append(("cherry_pick", _args))


class FakeRepo:
    def __init__(
        self,
        git_dir: Path,
        *,
        remote_raises: Exception | None = None,
        ls_remote_raises: bool = False,
        dirty: bool = False,
        remote: FakeRemote | None = None,
    ) -> None:
        self.git_dir = str(git_dir)
        self.git = FakeGit(ls_remote_raises=ls_remote_raises)
        self.index = FakeIndex()
        self._remote_raises = remote_raises
        self._dirty = dirty
        self._remote = remote or FakeRemote()

    def remote(self, name: str) -> FakeRemote:
        assert name == "origin"
        if self._remote_raises is not None:
            raise self._remote_raises
        return self._remote

    def is_dirty(self, *, untracked_files: bool) -> bool:
        assert untracked_files is True
        return self._dirty


def _manager_with_repo(monkeypatch, repo: FakeRepo) -> gitmod.GitManager:
    def fake_init_repo(self) -> FakeRepo:  # noqa: ANN001
        return repo

    monkeypatch.setattr(gitmod.GitManager, "_init_repo", fake_init_repo)
    return gitmod.GitManager(Path.cwd())


def test_init_repo_raises_when_knowledge_dir_is_not_git_repo(
    monkeypatch,
    tmp_path,
) -> None:
    def fake_repo(_path: Path) -> None:
        raise InvalidGitRepositoryError("nope")

    monkeypatch.setattr(gitmod, "Repo", fake_repo)
    with pytest.raises(gitmod.GitNotAvailableError):
        gitmod.GitManager(tmp_path)


def test_verify_remote_requires_origin(monkeypatch, tmp_path) -> None:
    repo = FakeRepo(tmp_path, remote_raises=ValueError("no origin"))
    manager = _manager_with_repo(monkeypatch, repo)
    with pytest.raises(gitmod.GitNotAvailableError):
        manager.verify_remote()


def test_verify_remote_raises_when_cannot_connect(monkeypatch, tmp_path) -> None:
    repo = FakeRepo(tmp_path, ls_remote_raises=True)
    manager = _manager_with_repo(monkeypatch, repo)
    with pytest.raises(gitmod.GitNotAvailableError):
        manager.verify_remote()


def test_verify_remote_ok(monkeypatch, tmp_path) -> None:
    repo = FakeRepo(tmp_path)
    manager = _manager_with_repo(monkeypatch, repo)
    manager.verify_remote()
    assert ("ls_remote", ("--exit-code", "origin")) in repo.git.calls


def test_abort_incomplete_operations_detects_markers(monkeypatch, tmp_path) -> None:
    git_dir = tmp_path / ".git"
    (git_dir / "rebase-merge").mkdir(parents=True)
    (git_dir / "MERGE_HEAD").write_text("x", encoding="utf-8")
    (git_dir / "CHERRY_PICK_HEAD").write_text("x", encoding="utf-8")

    repo = FakeRepo(git_dir)
    manager = _manager_with_repo(monkeypatch, repo)
    manager._abort_incomplete_operations()

    called = {name for name, _ in repo.git.calls}
    assert {"rebase", "merge", "cherry_pick"} <= called


def test_commit_and_push_commits_manual_changes_and_pushes_with_rebase(
    monkeypatch,
    tmp_path,
) -> None:
    git_dir = tmp_path / ".git"
    git_dir.mkdir(parents=True)

    remote = FakeRemote(push_failures=1)
    repo = FakeRepo(git_dir, dirty=True, remote=remote)
    manager = _manager_with_repo(monkeypatch, repo)

    manager.commit_and_push("x", "create")

    assert repo.index.added == [
        ["knowledge/x.md"],
        [".index_cache.pkl", ".index_hash"],
    ]
    assert repo.index.commits == ["manual: uncommitted changes", "create: x"]
    assert remote.pull_calls == 1
    assert remote.push_calls == 2


def test_commit_and_push_forget_removes_file(monkeypatch, tmp_path) -> None:
    git_dir = tmp_path / ".git"
    git_dir.mkdir(parents=True)

    repo = FakeRepo(git_dir)
    manager = _manager_with_repo(monkeypatch, repo)

    manager.commit_and_push("x", "forget")

    assert repo.index.removed == [(["knowledge/x.md"], True)]
    assert repo.index.added == [[".index_cache.pkl", ".index_hash"]]
    assert repo.index.commits == ["forget: x"]


def test_push_with_rebase_raises_when_pull_fails(monkeypatch, tmp_path) -> None:
    git_dir = tmp_path / ".git"
    git_dir.mkdir(parents=True)

    remote = FakeRemote(push_failures=1, pull_raises=True)
    repo = FakeRepo(git_dir, remote=remote)
    manager = _manager_with_repo(monkeypatch, repo)

    with pytest.raises(gitmod.GitOperationError):
        manager._push_with_rebase()
