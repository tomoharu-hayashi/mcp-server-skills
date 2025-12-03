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
