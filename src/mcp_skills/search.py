"""BM25 + セマンティック検索のハイブリッド検索"""

from rank_bm25 import BM25Okapi

from mcp_skills.embedding import EmbeddingIndex
from mcp_skills.models import Skill, SkillSummary

# RRFパラメータ
RRF_K = 60


def _tokenize(text: str) -> list[str]:
    """シンプルな文字ベーストークナイズ（日本語対応）"""
    # 空白・改行で分割 + 文字ngram
    tokens = text.lower().split()
    # 2-gramも追加（日本語検索精度向上）
    for word in text:
        if len(word) >= 2:
            tokens.extend(word[i : i + 2] for i in range(len(word) - 1))
    return tokens


class HybridSearch:
    """BM25とセマンティック検索のRRF統合"""

    def __init__(self, model_name: str = "cl-nagoya/ruri-v3-30m") -> None:
        self.embedding_index = EmbeddingIndex(model_name)
        self.bm25: BM25Okapi | None = None
        self.skill_names: list[str] = []
        self.skills_map: dict[str, Skill] = {}

    def build(self, skills: list[Skill]) -> None:
        """インデックス構築（起動時）"""
        self.skills_map = {s.name: s for s in skills}
        self.skill_names = [s.name for s in skills]

        # セマンティック検索インデックス
        self.embedding_index.build(skills)

        # BM25インデックス
        if skills:
            corpus = [
                _tokenize(f"{s.name} {s.description} {s.content}") for s in skills
            ]
            self.bm25 = BM25Okapi(corpus)
        else:
            self.bm25 = None

    def rebuild(self, skills: list[Skill], model_name: str | None = None) -> None:
        """再インデックス（モデル切り替え対応）"""
        if model_name:
            self.embedding_index.rebuild(skills, model_name)
        else:
            self.embedding_index.build(skills)

        self.skills_map = {s.name: s for s in skills}
        self.skill_names = [s.name for s in skills]

        if skills:
            corpus = [
                _tokenize(f"{s.name} {s.description} {s.content}") for s in skills
            ]
            self.bm25 = BM25Okapi(corpus)
        else:
            self.bm25 = None

    def add(self, skill: Skill) -> None:
        """スキルを追加"""
        self.skills_map[skill.name] = skill
        self.skill_names.append(skill.name)
        self.embedding_index.add(skill)
        # BM25は全体再構築（簡易実装）
        self._rebuild_bm25()

    def update(self, skill: Skill) -> None:
        """スキルを更新"""
        self.skills_map[skill.name] = skill
        self.embedding_index.update(skill)
        self._rebuild_bm25()

    def remove(self, skill_name: str) -> None:
        """スキルを削除"""
        self.skills_map.pop(skill_name, None)
        if skill_name in self.skill_names:
            self.skill_names.remove(skill_name)
        self.embedding_index.remove(skill_name)
        self._rebuild_bm25()

    def _rebuild_bm25(self) -> None:
        """BM25インデックスを再構築"""
        skills = list(self.skills_map.values())
        if skills:
            corpus = [
                _tokenize(f"{s.name} {s.description} {s.content}") for s in skills
            ]
            self.bm25 = BM25Okapi(corpus)
        else:
            self.bm25 = None

    def _bm25_search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """BM25検索"""
        if self.bm25 is None or not self.skill_names:
            return []

        tokenized_query = _tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        results = [
            (name, float(score))
            for name, score in zip(self.skill_names, scores, strict=True)
        ]
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def _rrf_fusion(
        self,
        bm25_results: list[tuple[str, float]],
        semantic_results: list[tuple[str, float]],
    ) -> list[str]:
        """RRF (Reciprocal Rank Fusion) でスコア統合"""
        rrf_scores: dict[str, float] = {}

        # BM25のランクを計算
        for rank, (name, _) in enumerate(bm25_results):
            rrf_scores[name] = rrf_scores.get(name, 0) + 1 / (RRF_K + rank + 1)

        # セマンティック検索のランクを計算
        for rank, (name, _) in enumerate(semantic_results):
            rrf_scores[name] = rrf_scores.get(name, 0) + 1 / (RRF_K + rank + 1)

        # スコア順にソート
        sorted_names = sorted(
            rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True
        )
        return sorted_names

    def search(self, query: str, top_k: int = 10) -> list[SkillSummary]:
        """ハイブリッド検索"""
        if not self.skills_map:
            return []

        # 両方の検索を実行
        bm25_results = self._bm25_search(query, top_k=top_k * 2)
        semantic_results = self.embedding_index.search(query, top_k=top_k * 2)

        # RRFで統合
        merged_names = self._rrf_fusion(bm25_results, semantic_results)

        # SkillSummaryに変換
        results = []
        for name in merged_names[:top_k]:
            if skill := self.skills_map.get(name):
                results.append(skill.to_summary())
        return results

