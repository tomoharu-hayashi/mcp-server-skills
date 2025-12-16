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

    # 既定は knowledge/ 配下（リポジトリ構造に合わせる）
    # テストや旧構造ではknowledge_dir直下の再帰走査にフォールバック
    content_root = knowledge_dir / "knowledge"
    search_root = content_root if content_root.is_dir() else knowledge_dir

    knowledge_files = sorted(search_root.rglob("*.md"))
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

    def load(self) -> dict[str, np.ndarray] | None:
        """キャッシュからEmbeddingを読み込み（有効性チェック込み）"""
        if not self.cache_path.exists() or not self.hash_path.exists():
            return None

        # ハッシュが一致するか確認
        stored_hash = self.hash_path.read_text(encoding="utf-8").strip()
        current_hash = compute_content_hash(self.knowledge_dir)
        if stored_hash != current_hash:
            return None

        try:
            with self.cache_path.open("rb") as f:
                return pickle.load(f)  # noqa: S301
        except Exception:
            return None

    def save(self, embeddings: dict[str, np.ndarray]) -> None:
        """Embeddingをキャッシュに保存（アトミック書き込み）"""
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

        current_hash = compute_content_hash(self.knowledge_dir)

        # 一時ファイルに書いてからrenameでアトミック化
        tmp_cache = self.cache_path.with_suffix(".tmp")
        with tmp_cache.open("wb") as f:
            pickle.dump(embeddings, f)
        tmp_cache.rename(self.cache_path)

        tmp_hash = self.hash_path.with_suffix(".tmp")
        tmp_hash.write_text(current_hash, encoding="utf-8")
        tmp_hash.rename(self.hash_path)
