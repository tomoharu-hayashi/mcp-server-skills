"""MCPサーバーのテスト"""


from mcp_skills.models import Skill, SkillSummary, SkillUpdate
from mcp_skills.storage import SkillStorage


class TestSkillStorage:
    """ストレージ層のテスト"""

    def test_save_and_load_skill(self, tmp_path):
        """スキルの保存と読み込み"""
        storage = SkillStorage(tmp_path / "skills")

        skill = Skill(
            name="test-skill",
            description="テスト用スキル",
            content="## 手順\n1. テストを実行",
        )
        storage.save_skill(skill)

        loaded = storage.load_skill("test-skill")
        assert loaded is not None
        assert loaded.name == "test-skill"
        assert loaded.description == "テスト用スキル"
        assert "テストを実行" in loaded.content

    def test_list_skills(self, tmp_path):
        """スキル一覧の取得"""
        storage = SkillStorage(tmp_path / "skills")

        storage.save_skill(Skill(name="skill-a", description="スキルA"))
        storage.save_skill(Skill(name="skill-b", description="スキルB"))

        skills = storage.list_skills()
        assert len(skills) == 2
        names = {s.name for s in skills}
        assert names == {"skill-a", "skill-b"}

    def test_search_skills(self, tmp_path):
        """スキル検索"""
        storage = SkillStorage(tmp_path / "skills")

        storage.save_skill(Skill(name="create-pr", description="PRを作成したいとき"))
        storage.save_skill(
            Skill(name="review-pr", description="PRをレビューしたいとき")
        )
        storage.save_skill(
            Skill(name="run-tests", description="テストを実行したいとき")
        )

        # 名前で検索
        results = storage.search_skills("pr")
        assert len(results) == 2

        # 説明で検索
        results = storage.search_skills("テスト")
        assert len(results) == 1
        assert results[0].name == "run-tests"

    def test_delete_skill(self, tmp_path):
        """スキルの削除"""
        storage = SkillStorage(tmp_path / "skills")

        storage.save_skill(Skill(name="to-delete", description="削除対象"))
        assert storage.load_skill("to-delete") is not None

        result = storage.delete_skill("to-delete")
        assert result is True
        assert storage.load_skill("to-delete") is None

    def test_load_nonexistent_skill(self, tmp_path):
        """存在しないスキルの読み込み"""
        storage = SkillStorage(tmp_path / "skills")
        assert storage.load_skill("nonexistent") is None

    def test_allowed_tools_field(self, tmp_path):
        """allowed-toolsフィールドの読み書き"""
        storage = SkillStorage(tmp_path / "skills")

        skill = Skill(
            name="with-tools",
            description="ツール制限あり",
            allowed_tools="Bash",
        )
        storage.save_skill(skill)

        loaded = storage.load_skill("with-tools")
        assert loaded is not None
        assert loaded.allowed_tools == "Bash"


class TestModels:
    """モデルのテスト"""

    def test_skill_to_summary(self):
        """Skillから概要への変換"""
        skill = Skill(
            name="test",
            description="テスト",
            content="詳細",
        )
        summary = skill.to_summary()
        assert isinstance(summary, SkillSummary)
        assert summary.name == "test"
        assert summary.description == "テスト"

    def test_skill_update_partial(self):
        """部分更新"""
        update = SkillUpdate(description="新しい説明")
        assert update.description == "新しい説明"
        assert update.content is None
        assert update.allowed_tools is None
