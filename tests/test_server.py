"""MCPサーバーのテスト"""

from pathlib import Path

from mcp_brain.models import Knowledge, KnowledgeSummary
from mcp_brain.storage import (
    GLOBAL_SCOPE,
    KnowledgeStorage,
    get_scope_hierarchy,
    path_to_scope,
)


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

        result = storage.delete("to-delete")
        assert result is True
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


class TestScopeHierarchy:
    """スコープ階層のテスト"""

    def test_path_to_scope(self):
        """パスをスコープ文字列に変換"""
        assert path_to_scope(Path("/Users/me/project")) == "Users/me/project"
        assert path_to_scope(Path("/a/b/c")) == "a/b/c"

    def test_get_scope_hierarchy(self):
        """スコープ階層の生成"""
        hierarchy = get_scope_hierarchy(Path("/Users/me/pj/project"))
        assert hierarchy[0] == "Users/me/pj/project"
        assert hierarchy[1] == "Users/me/pj"
        assert hierarchy[2] == "Users/me"
        assert hierarchy[-1] == GLOBAL_SCOPE

    def test_get_scope_hierarchy_none(self):
        """プロジェクトなしの場合はglobalのみ"""
        hierarchy = get_scope_hierarchy(None)
        assert hierarchy == [GLOBAL_SCOPE]

    def test_storage_scope_priority(self, tmp_path):
        """スコープの優先度: プロジェクト固有 > 親 > global"""
        base_dir = tmp_path / "brain"
        project_path = Path("/Users/me/pj/project")

        # 各スコープに同名の知識を作成
        storage = KnowledgeStorage(base_dir)

        # グローバルに保存
        storage.save(
            Knowledge(name="shared", description="global版"),
            scope=GLOBAL_SCOPE,
        )

        # 親スコープに保存
        storage.save(
            Knowledge(name="shared", description="親スコープ版"),
            scope="Users/me/pj",
        )

        # プロジェクトスコープに保存
        storage.save(
            Knowledge(name="shared", description="プロジェクト版"),
            scope="Users/me/pj/project",
        )

        # プロジェクトスコープを設定
        storage.set_project(project_path)

        # 検索するとプロジェクト版が優先される
        loaded = storage.load("shared")
        assert loaded is not None
        assert loaded.description == "プロジェクト版"

    def test_storage_fallback_to_global(self, tmp_path):
        """プロジェクトスコープに無ければglobalから取得"""
        base_dir = tmp_path / "brain"
        project_path = Path("/Users/me/pj/project")

        storage = KnowledgeStorage(base_dir)

        # グローバルにのみ保存
        storage.save(
            Knowledge(name="global-only", description="グローバル知識"),
            scope=GLOBAL_SCOPE,
        )

        # プロジェクトスコープを設定
        storage.set_project(project_path)

        # グローバルから取得される
        loaded = storage.load("global-only")
        assert loaded is not None
        assert loaded.description == "グローバル知識"

    def test_list_all_merges_scopes(self, tmp_path):
        """list_allは全スコープをマージ（重複除去）"""
        base_dir = tmp_path / "brain"
        project_path = Path("/Users/me/pj/project")

        storage = KnowledgeStorage(base_dir, project_path)

        # 各スコープに知識を作成
        storage.save(
            Knowledge(name="global-item", description="グローバル"),
            scope=GLOBAL_SCOPE,
        )
        storage.save(
            Knowledge(name="project-item", description="プロジェクト"),
            scope="Users/me/pj/project",
        )
        storage.save(
            Knowledge(name="shared", description="グローバル版"),
            scope=GLOBAL_SCOPE,
        )
        storage.save(
            Knowledge(name="shared", description="プロジェクト版"),
            scope="Users/me/pj/project",
        )

        items = storage.list_all()
        names = {k.name for k in items}
        assert names == {"global-item", "project-item", "shared"}

        # sharedはプロジェクト版が優先
        shared_item = next(k for k in items if k.name == "shared")
        assert shared_item.description == "プロジェクト版"
