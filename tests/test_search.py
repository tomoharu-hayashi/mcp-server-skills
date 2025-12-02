"""セマンティック検索のテスト"""

import pytest

from mcp_brain.models import Knowledge
from mcp_brain.search import SemanticSearch


class TestSemanticSearch:
    """セマンティック検索のテスト"""

    @pytest.fixture
    def items(self):
        """テスト用知識"""
        return [
            Knowledge(
                name="create-pr",
                description="PRを作成したいとき",
                content="## 手順\n1. git push\n2. gh pr create",
            ),
            Knowledge(
                name="review-pr",
                description="PRをレビューしたいとき",
                content="## 手順\n1. コードを確認\n2. コメントを追加",
            ),
            Knowledge(
                name="deploy-staging",
                description="ステージング環境にデプロイしたいとき",
                content="## 手順\n1. テスト実行\n2. デプロイコマンド実行",
            ),
        ]

    def test_semantic_search(self, items):
        """セマンティック検索（意味的な類似性）"""
        search = SemanticSearch()
        search.build(items)

        # 「本番公開」でデプロイ関連が見つかる
        results = search.search("本番公開")
        assert len(results) >= 1

    def test_search_pr(self, items):
        """PR関連の検索"""
        search = SemanticSearch()
        search.build(items)

        results = search.search("PRを作成したい")
        assert len(results) >= 1
        names = [r.name for r in results]
        assert "create-pr" in names

    def test_add(self, items):
        """知識追加後の検索"""
        search = SemanticSearch()
        search.build(items[:2])

        assert len(search.knowledge_map) == 2

        search.add(items[2])
        assert len(search.knowledge_map) == 3

        results = search.search("デプロイしたい")
        names = [r.name for r in results]
        assert "deploy-staging" in names

    def test_update(self, items):
        """知識更新後の検索"""
        search = SemanticSearch()
        search.build(items)

        updated = Knowledge(
            name="create-pr",
            description="マージリクエストを作成したいとき",
            content="## 手順\n1. git push\n2. GitLabでMRを作成",
        )
        search.update(updated)

        results = search.search("GitLabでマージリクエスト")
        assert len(results) >= 1
        # 更新された知識が上位に来ることを確認
        assert results[0].name == "create-pr"

    def test_empty_build(self):
        """空の知識リストでビルド"""
        search = SemanticSearch()
        search.build([])

        results = search.search("anything")
        assert results == []

    def test_empty_query(self, items):
        """空クエリの場合は空を返す"""
        search = SemanticSearch()
        search.build(items)

        results = search.search("")
        assert results == []

    def test_rebuild(self, items):
        """再インデックス"""
        search = SemanticSearch()
        search.build(items[:1])
        assert len(search.knowledge_map) == 1

        search.rebuild(items)
        assert len(search.knowledge_map) == 3
