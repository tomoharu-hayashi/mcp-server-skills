"""セマンティック検索のテスト"""

import pytest

from mcp_skills.models import Skill
from mcp_skills.search import SemanticSearch


class TestSemanticSearch:
    """セマンティック検索のテスト"""

    @pytest.fixture
    def skills(self):
        """テスト用スキル"""
        return [
            Skill(
                name="create-pr",
                description="PRを作成したいとき",
                content="## 手順\n1. git push\n2. gh pr create",
            ),
            Skill(
                name="review-pr",
                description="PRをレビューしたいとき",
                content="## 手順\n1. コードを確認\n2. コメントを追加",
            ),
            Skill(
                name="deploy-staging",
                description="ステージング環境にデプロイしたいとき",
                content="## 手順\n1. テスト実行\n2. デプロイコマンド実行",
            ),
        ]

    def test_semantic_search(self, skills):
        """セマンティック検索（意味的な類似性）"""
        search = SemanticSearch()
        search.build(skills)

        # 「本番公開」でデプロイ関連が見つかる
        results = search.search("本番公開")
        assert len(results) >= 1

    def test_search_pr(self, skills):
        """PR関連の検索"""
        search = SemanticSearch()
        search.build(skills)

        results = search.search("PRを作成したい")
        assert len(results) >= 1
        names = [r.name for r in results]
        assert "create-pr" in names

    def test_add_skill(self, skills):
        """スキル追加後の検索"""
        search = SemanticSearch()
        search.build(skills[:2])

        assert len(search.skills_map) == 2

        search.add(skills[2])
        assert len(search.skills_map) == 3

        results = search.search("デプロイしたい")
        names = [r.name for r in results]
        assert "deploy-staging" in names

    def test_update_skill(self, skills):
        """スキル更新後の検索"""
        search = SemanticSearch()
        search.build(skills)

        updated_skill = Skill(
            name="create-pr",
            description="マージリクエストを作成したいとき",
            content="## 手順\n1. git push\n2. GitLabでMRを作成",
        )
        search.update(updated_skill)

        results = search.search("GitLabでマージリクエスト")
        assert len(results) >= 1
        # 更新されたスキルが上位に来ることを確認
        assert results[0].name == "create-pr"

    def test_empty_build(self):
        """空のスキルリストでビルド"""
        search = SemanticSearch()
        search.build([])

        results = search.search("anything")
        assert results == []

    def test_empty_query(self, skills):
        """空クエリの場合は空を返す"""
        search = SemanticSearch()
        search.build(skills)

        results = search.search("")
        assert results == []

    def test_rebuild(self, skills):
        """再インデックス"""
        search = SemanticSearch()
        search.build(skills[:1])
        assert len(search.skills_map) == 1

        search.rebuild(skills)
        assert len(search.skills_map) == 3
