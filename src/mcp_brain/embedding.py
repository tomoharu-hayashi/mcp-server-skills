"""ruri-v3によるEmbeddingインデックス管理"""

import numpy as np
from sentence_transformers import SentenceTransformer

from mcp_brain.models import Knowledge

# ruri-v3はquery prefixを使用
QUERY_PREFIX = "クエリ: "
PASSAGE_PREFIX = "文章: "


class EmbeddingIndex:
    """セマンティック検索用のインデックス"""

    def __init__(self, model_name: str = "cl-nagoya/ruri-v3-30m") -> None:
        self.model_name = model_name
        self.model: SentenceTransformer | None = None
        self.embeddings: dict[str, np.ndarray] = {}
        self.knowledge_texts: dict[str, str] = {}

    def _load_model(self) -> None:
        """モデルを遅延ロード"""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)

    def _knowledge_to_text(self, knowledge: Knowledge) -> str:
        """知識を検索用テキストに変換"""
        return f"{knowledge.name}\n{knowledge.description}\n{knowledge.content}"

    def build(self, items: list[Knowledge]) -> None:
        """全知識からインデックスを構築"""
        if not items:
            self.embeddings = {}
            self.knowledge_texts = {}
            return

        self._load_model()
        assert self.model is not None

        texts = []
        names = []
        for knowledge in items:
            text = self._knowledge_to_text(knowledge)
            texts.append(PASSAGE_PREFIX + text)
            names.append(knowledge.name)
            self.knowledge_texts[knowledge.name] = text

        # バッチエンコード
        vectors = self.model.encode(
            texts, convert_to_numpy=True, show_progress_bar=False
        )
        self.embeddings = dict(zip(names, vectors, strict=True))

    def rebuild(self, items: list[Knowledge], model_name: str | None = None) -> None:
        """再インデックス（モデル切り替え対応）"""
        if model_name and model_name != self.model_name:
            self.model_name = model_name
            self.model = None  # 次回ロード時に新モデルをロード
        self.build(items)

    def add(self, knowledge: Knowledge) -> None:
        """知識をインデックスに追加"""
        self._load_model()
        assert self.model is not None

        text = self._knowledge_to_text(knowledge)
        self.knowledge_texts[knowledge.name] = text
        vector = self.model.encode(
            PASSAGE_PREFIX + text, convert_to_numpy=True, show_progress_bar=False
        )
        self.embeddings[knowledge.name] = vector

    def update(self, knowledge: Knowledge) -> None:
        """知識のインデックスを更新"""
        self.add(knowledge)

    def remove(self, name: str) -> None:
        """知識をインデックスから削除"""
        self.embeddings.pop(name, None)
        self.knowledge_texts.pop(name, None)

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """セマンティック検索

        Returns:
            (name, score) のリスト（スコア降順）
        """
        if not self.embeddings:
            return []

        self._load_model()
        assert self.model is not None

        query_vector = self.model.encode(
            QUERY_PREFIX + query, convert_to_numpy=True, show_progress_bar=False
        )

        # コサイン類似度計算
        results = []
        for name, doc_vector in self.embeddings.items():
            norm_q = np.linalg.norm(query_vector)
            norm_d = np.linalg.norm(doc_vector)
            score = float(np.dot(query_vector, doc_vector) / (norm_q * norm_d))
            results.append((name, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
