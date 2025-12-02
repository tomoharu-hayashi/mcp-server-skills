"""インデックスキャッシュ管理

起動高速化のため、Embeddingをキャッシュしておき、
変更がなければ再利用する。
"""

import hashlib
import pickle
from pathlib import Path

import numpy as np


def compute_content_hash(knowledge_dir: Path) -> str:
    """知識ディレクトリの内容からハッシュを計算"""
    hasher = hashlib.sha256()

    if not knowledge_dir.exists():
        return hasher.hexdigest()

    # 全KNOWLEDGE.mdファイルの内容をハッシュ
    knowledge_files = sorted(knowledge_dir.rglob("KNOWLEDGE.md"))
    for f in knowledge_files:
        hasher.update(str(f.relative_to(knowledge_dir)).encode())
        hasher.update(f.read_bytes())

    return hasher.hexdigest()


class IndexCache:
    """Embeddingインデックスのキャッシュ"""

    CACHE_FILE = ".index_cache.pkl"
    HASH_FILE = ".index_hash"

    def __init__(self, knowledge_dir: Path) -> None:
        self.knowledge_dir = knowledge_dir
        self.cache_path = knowledge_dir / self.CACHE_FILE
        self.hash_path = knowledge_dir / self.HASH_FILE

    def is_valid(self) -> bool:
        """キャッシュが有効か（ハッシュが一致するか）"""
        if not self.cache_path.exists() or not self.hash_path.exists():
            return False

        stored_hash = self.hash_path.read_text(encoding="utf-8").strip()
        current_hash = compute_content_hash(self.knowledge_dir)
        return stored_hash == current_hash

    def load(self) -> dict[str, np.ndarray] | None:
        """キャッシュからEmbeddingを読み込み"""
        if not self.is_valid():
            return None

        try:
            with self.cache_path.open("rb") as f:
                return pickle.load(f)  # noqa: S301
        except Exception:
            return None

    def save(self, embeddings: dict[str, np.ndarray]) -> None:
        """Embeddingをキャッシュに保存"""
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

        # ハッシュを保存
        current_hash = compute_content_hash(self.knowledge_dir)
        self.hash_path.write_text(current_hash, encoding="utf-8")

        # Embeddingを保存
        with self.cache_path.open("wb") as f:
            pickle.dump(embeddings, f)
