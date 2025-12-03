"""インデックスキャッシュのテスト"""

import numpy as np

from mcp_brain.index_cache import IndexCache, compute_content_hash


class TestIndexCache:
    """インデックスキャッシュのテスト"""

    def test_content_hash_empty(self, tmp_path):
        """空ディレクトリのハッシュ"""
        hash1 = compute_content_hash(tmp_path)
        hash2 = compute_content_hash(tmp_path)
        assert hash1 == hash2

    def test_content_hash_changes(self, tmp_path):
        """内容変更でハッシュが変わる"""
        knowledge_dir = tmp_path / "test-knowledge"
        knowledge_dir.mkdir()
        (knowledge_dir / "KNOWLEDGE.md").write_text("test")

        hash1 = compute_content_hash(tmp_path)

        # 内容を変更
        (knowledge_dir / "KNOWLEDGE.md").write_text("modified")
        hash2 = compute_content_hash(tmp_path)

        assert hash1 != hash2

    def test_cache_save_load(self, tmp_path):
        """キャッシュの保存と読み込み"""
        cache = IndexCache(tmp_path)

        embeddings = {
            "test1": np.array([1.0, 2.0, 3.0]),
            "test2": np.array([4.0, 5.0, 6.0]),
        }

        cache.save(embeddings)
        loaded = cache.load()

        assert loaded is not None
        assert set(loaded.keys()) == {"test1", "test2"}
        np.testing.assert_array_equal(loaded["test1"], embeddings["test1"])

    def test_cache_invalid_after_change(self, tmp_path):
        """内容変更後はキャッシュが無効"""
        cache = IndexCache(tmp_path)
        embeddings = {"test1": np.array([1.0, 2.0, 3.0])}
        cache.save(embeddings)

        # ファイルを追加
        knowledge_dir = tmp_path / "new-knowledge"
        knowledge_dir.mkdir()
        (knowledge_dir / "KNOWLEDGE.md").write_text("new content")

        # load()がNoneを返す = キャッシュ無効
        assert cache.load() is None
