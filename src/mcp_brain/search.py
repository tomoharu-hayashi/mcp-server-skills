"""セマンティック検索"""

from pathlib import Path

from mcp_brain.embedding import EmbeddingIndex
from mcp_brain.models import Knowledge, KnowledgeSummary


class SemanticSearch:
    """Embeddingベースのセマンティック検索"""

    def __init__(
        self, model_name: str = "cl-nagoya/ruri-v3-30m", cache_dir: Path | None = None
    ) -> None:
        self.embedding_index = EmbeddingIndex(model_name, cache_dir=cache_dir)
        self.knowledge_map: dict[str, Knowledge] = {}

    def build(self, items: list[Knowledge], background: bool = False) -> None:
        """インデックス構築（起動時）"""
        self.knowledge_map = {k.name: k for k in items}
        self.embedding_index.build(items, background=background)

    def rebuild(self, items: list[Knowledge], model_name: str | None = None) -> None:
        """再インデックス（モデル切り替え対応）"""
        if model_name:
            self.embedding_index.rebuild(items, model_name)
        else:
            self.embedding_index.build(items)
        self.knowledge_map = {k.name: k for k in items}

    def add(self, knowledge: Knowledge) -> None:
        """知識を追加"""
        self.knowledge_map[knowledge.name] = knowledge
        self.embedding_index.add(knowledge)

    def update(self, knowledge: Knowledge) -> None:
        """知識を更新"""
        self.knowledge_map[knowledge.name] = knowledge
        self.embedding_index.update(knowledge)

    def remove(self, name: str) -> None:
        """知識を削除"""
        self.knowledge_map.pop(name, None)
        self.embedding_index.remove(name)

    def search(self, query: str, top_k: int = 10) -> list[KnowledgeSummary]:
        """セマンティック検索

        Args:
            query: 自然言語クエリ
            top_k: 返す件数
        """
        if not self.knowledge_map or not query:
            return []

        results = self.embedding_index.search(query, top_k=top_k)

        return [
            self.knowledge_map[name].to_summary()
            for name, _ in results
            if name in self.knowledge_map
        ]

    def find_similar(
        self, name: str, top_k: int = 5
    ) -> list[tuple[KnowledgeSummary, float]]:
        """指定した知識に類似する知識を取得

        Args:
            name: 知識名
            top_k: 返す件数

        Returns:
            (知識サマリー, 類似度) のリスト
        """
        knowledge = self.knowledge_map.get(name)
        if not knowledge:
            return []

        # 知識の説明で検索（自分自身を除外）
        query = f"{knowledge.name} {knowledge.description}"
        results = self.embedding_index.search(query, top_k=top_k + 1)

        return [
            (self.knowledge_map[n].to_summary(), score)
            for n, score in results
            if n in self.knowledge_map and n != name
        ][:top_k]
