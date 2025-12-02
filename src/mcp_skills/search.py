"""セマンティック検索"""

from mcp_skills.embedding import EmbeddingIndex
from mcp_skills.models import Skill, SkillSummary


class SemanticSearch:
    """Embeddingベースのセマンティック検索"""

    def __init__(self, model_name: str = "cl-nagoya/ruri-v3-30m") -> None:
        self.embedding_index = EmbeddingIndex(model_name)
        self.skills_map: dict[str, Skill] = {}

    def build(self, skills: list[Skill]) -> None:
        """インデックス構築（起動時）"""
        self.skills_map = {s.name: s for s in skills}
        self.embedding_index.build(skills)

    def rebuild(self, skills: list[Skill], model_name: str | None = None) -> None:
        """再インデックス（モデル切り替え対応）"""
        if model_name:
            self.embedding_index.rebuild(skills, model_name)
        else:
            self.embedding_index.build(skills)
        self.skills_map = {s.name: s for s in skills}

    def add(self, skill: Skill) -> None:
        """スキルを追加"""
        self.skills_map[skill.name] = skill
        self.embedding_index.add(skill)

    def update(self, skill: Skill) -> None:
        """スキルを更新"""
        self.skills_map[skill.name] = skill
        self.embedding_index.update(skill)

    def remove(self, skill_name: str) -> None:
        """スキルを削除"""
        self.skills_map.pop(skill_name, None)
        self.embedding_index.remove(skill_name)

    def search(self, query: str, top_k: int = 10) -> list[SkillSummary]:
        """セマンティック検索

        Args:
            query: 自然言語クエリ
            top_k: 返す件数
        """
        if not self.skills_map or not query:
            return []

        results = self.embedding_index.search(query, top_k=top_k)

        return [
            self.skills_map[name].to_summary()
            for name, _ in results
            if name in self.skills_map
        ]
