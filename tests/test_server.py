"""MCPサーバーのテスト"""

from mcp_brain.models import Knowledge, KnowledgeSummary
from mcp_brain.storage import KnowledgeStorage


class TestKnowledgeStorage:
    """ストレージ層のテスト"""

    def test_save_and_load(self, tmp_path):
        """知識の保存と読み込み"""
        storage = KnowledgeStorage(tmp_path / "knowledge")

        knowledge = Knowledge(
            name="test-knowledge",
            description="テスト用知識",
            content="## 手順\n1. テストを実行",
        )
        storage.save(knowledge)

        loaded = storage.load("test-knowledge")
        assert loaded is not None
        assert loaded.name == "test-knowledge"
        assert loaded.description == "テスト用知識"
        assert "テストを実行" in loaded.content

    def test_list_all(self, tmp_path):
        """知識一覧の取得"""
        storage = KnowledgeStorage(tmp_path / "knowledge")

        storage.save(Knowledge(name="knowledge-a", description="知識A"))
        storage.save(Knowledge(name="knowledge-b", description="知識B"))

        items = storage.list_all()
        assert len(items) == 2
        names = {k.name for k in items}
        assert names == {"knowledge-a", "knowledge-b"}

    def test_search(self, tmp_path):
        """知識検索"""
        storage = KnowledgeStorage(tmp_path / "knowledge")

        storage.save(Knowledge(name="create-pr", description="PRを作成したいとき"))
        storage.save(Knowledge(name="review-pr", description="PRをレビューしたいとき"))
        storage.save(Knowledge(name="run-tests", description="テストを実行したいとき"))

        # 名前で検索
        results = storage.search("pr")
        assert len(results) == 2

        # 説明で検索
        results = storage.search("テスト")
        assert len(results) == 1
        assert results[0].name == "run-tests"

    def test_delete(self, tmp_path):
        """知識の削除"""
        storage = KnowledgeStorage(tmp_path / "knowledge")

        storage.save(Knowledge(name="to-delete", description="削除対象"))
        assert storage.load("to-delete") is not None

        deleted = storage.delete("to-delete")
        assert deleted is True
        assert storage.load("to-delete") is None

    def test_load_nonexistent(self, tmp_path):
        """存在しない知識の読み込み"""
        storage = KnowledgeStorage(tmp_path / "knowledge")
        assert storage.load("nonexistent") is None

    def test_allowed_tools_field(self, tmp_path):
        """allowed-toolsフィールドの読み書き"""
        storage = KnowledgeStorage(tmp_path / "knowledge")

        knowledge = Knowledge(
            name="with-tools",
            description="ツール制限あり",
            allowed_tools="Bash",
        )
        storage.save(knowledge)

        loaded = storage.load("with-tools")
        assert loaded is not None
        assert loaded.allowed_tools == "Bash"


class TestModels:
    """モデルのテスト"""

    def test_knowledge_to_summary(self):
        """Knowledgeから概要への変換"""
        knowledge = Knowledge(
            name="test",
            description="テスト",
            content="詳細",
        )
        summary = knowledge.to_summary()
        assert isinstance(summary, KnowledgeSummary)
        assert summary.name == "test"
        assert summary.description == "テスト"

    def test_knowledge_to_summary_with_project(self):
        """Knowledgeから概要への変換（project付き）"""
        knowledge = Knowledge(
            name="test-with-project",
            description="プロジェクト付きテスト",
            content="詳細",
            project="my-app",
        )
        summary = knowledge.to_summary()
        assert summary.project == "my-app"

    def test_knowledge_default_project(self):
        """Knowledgeのデフォルトproject"""
        knowledge = Knowledge(
            name="test-default",
            description="デフォルトテスト",
        )
        assert knowledge.project == "global"
        assert knowledge.to_summary().project == "global"


class TestProjectValidation:
    """プロジェクト名バリデーションのテスト"""

    def test_valid_project_names(self):
        """有効なプロジェクト名"""
        valid_names = ["my-app", "project123", "mcp-server-brain", "global"]
        for name in valid_names:
            knowledge = Knowledge(
                name="test",
                description="test",
                project=name,
            )
            assert knowledge.project == name

    def test_invalid_project_uppercase(self):
        """大文字は無効"""
        import pytest

        with pytest.raises(ValueError, match="must be kebab-case"):
            Knowledge(name="test", description="test", project="MyApp")

    def test_invalid_project_underscore(self):
        """アンダースコアは無効"""
        import pytest

        with pytest.raises(ValueError, match="must be kebab-case"):
            Knowledge(name="test", description="test", project="my_app")

    def test_invalid_project_empty(self):
        """空文字は無効"""
        import pytest

        with pytest.raises(ValueError, match="cannot be empty"):
            Knowledge(name="test", description="test", project="")

    def test_invalid_project_space(self):
        """スペースは無効"""
        import pytest

        with pytest.raises(ValueError, match="must be kebab-case"):
            Knowledge(name="test", description="test", project="my app")


class TestProjectSorting:
    """プロジェクトソートのテスト"""

    def test_project_sorting_logic(self):
        """プロジェクト一致 → global → その他の順でソートされる"""
        # KnowledgeSummaryのリストを作成
        results = [
            KnowledgeSummary(name="k1", description="other", project="other-project"),
            KnowledgeSummary(name="k2", description="global", project="global"),
            KnowledgeSummary(name="k3", description="matched", project="my-app"),
            KnowledgeSummary(name="k4", description="global2", project="global"),
            KnowledgeSummary(name="k5", description="matched2", project="my-app"),
        ]

        project = "my-app"

        # ソートロジック（server.py と同じ）
        matched = [r for r in results if r.project == project]
        global_ = [r for r in results if r.project == "global"]
        others = [r for r in results if r.project not in (project, "global")]
        sorted_results = matched + global_ + others

        # 検証: my-app が先、次に global、最後に other
        assert sorted_results[0].name == "k3"
        assert sorted_results[1].name == "k5"
        assert sorted_results[2].name == "k2"
        assert sorted_results[3].name == "k4"
        assert sorted_results[4].name == "k1"


class TestProjectStorage:
    """プロジェクトフィールドのストレージテスト"""

    def test_save_and_load_with_project(self, tmp_path):
        """projectフィールド付き知識の保存と読み込み"""
        storage = KnowledgeStorage(tmp_path / "knowledge")

        knowledge = Knowledge(
            name="project-knowledge",
            description="プロジェクト付き知識",
            project="my-awesome-app",
        )
        storage.save(knowledge)

        loaded = storage.load("project-knowledge")
        assert loaded is not None
        assert loaded.project == "my-awesome-app"

    def test_load_without_project_defaults_to_global(self, tmp_path):
        """projectフィールドがない既存知識はglobalになる"""
        storage = KnowledgeStorage(tmp_path / "knowledge")

        # projectフィールドなしの.mdファイルを直接作成（フラット形式）
        (tmp_path / "knowledge" / "old-knowledge.md").write_text(
            """---
name: old-knowledge
description: 古い知識
version: 1
created: 2025-01-01
---

## 手順
古い手順
""",
            encoding="utf-8",
        )

        loaded = storage.load("old-knowledge")
        assert loaded is not None
        assert loaded.project == "global"
