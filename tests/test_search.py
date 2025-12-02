"""ハイブリッド検索のテスト"""

import pytest

from mcp_skills.models import Skill
from mcp_skills.search import HybridSearch


class TestHybridSearch:
    """ハイブリッド検索のテスト"""

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

    def test_build_and_search(self, skills):
        """インデックス構築と検索"""
        search = HybridSearch()
        search.build(skills)

        results = search.search("PR")
        assert len(results) >= 1
        # PRに関連するスキルが上位に来る
        names = [r.name for r in results]
        assert "create-pr" in names or "review-pr" in names

    def test_search_semantic(self, skills):
        """セマンティック検索（意味的な類似性）"""
        search = HybridSearch()
        search.build(skills)

        # 「本番公開」で検索 -> deploy関連がヒットすべき
        results = search.search("本番公開")
        assert len(results) >= 1

    def test_add_skill(self, skills):
        """スキル追加後の検索"""
        search = HybridSearch()
        search.build(skills[:2])

        # 最初は2件
        assert len(search.skills_map) == 2

        # スキル追加
        search.add(skills[2])
        assert len(search.skills_map) == 3

        # 追加したスキルが検索できる
        results = search.search("deploy")
        names = [r.name for r in results]
        assert "deploy-staging" in names

    def test_update_skill(self, skills):
        """スキル更新後の検索"""
        search = HybridSearch()
        search.build(skills)

        # スキルを更新
        updated_skill = Skill(
            name="create-pr",
            description="マージリクエストを作成したいとき",
            content="## 手順\n1. git push\n2. GitLabでMRを作成",
        )
        search.update(updated_skill)

        # 更新内容で検索できる
        results = search.search("GitLab")
        assert len(results) >= 1
        names = [r.name for r in results]
        assert "create-pr" in names

    def test_empty_build(self):
        """空のスキルリストでビルド"""
        search = HybridSearch()
        search.build([])

        results = search.search("anything")
        assert results == []

    def test_rebuild(self, skills):
        """再インデックス"""
        search = HybridSearch()
        search.build(skills[:1])
        assert len(search.skills_map) == 1

        search.rebuild(skills)
        assert len(search.skills_map) == 3

