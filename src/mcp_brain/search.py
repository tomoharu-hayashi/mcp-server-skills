"""セマンティック検索"""

from mcp_brain.embedding import EmbeddingIndex
from mcp_brain.models import Knowledge, KnowledgeSummary


class SemanticSearch:
    """Embeddingベースのセマンティック検索"""

    def __init__(self, model_name: str = "cl-nagoya/ruri-v3-30m") -> None:
        self.embedding_index = EmbeddingIndex(model_name)
        self.knowledge_map: dict[str, Knowledge] = {}

    def build(self, items: list[Knowledge]) -> None:
        """インデックス構築（起動時）"""
        self.knowledge_map = {k.name: k for k in items}
        self.embedding_index.build(items)

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
