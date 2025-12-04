"""FastMCPサーバー定義"""

import logging
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .git import GitManager, GitNotAvailableError, GitOperationError
from .models import Knowledge
from .notification import show_create_confirmation, show_stale_dialog
from .search import SemanticSearch
from .storage import KnowledgeStorage

# ロギング設定
logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def play_sound() -> None:
    """macOSの効果音を非同期で再生"""
    subprocess.Popen(
        ["afplay", "/System/Library/Sounds/Hero.aiff"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# グローバルインスタンス（mainで初期化）
storage: KnowledgeStorage | None = None
search_engine: SemanticSearch | None = None
git_manager: GitManager | None = None


def get_git() -> GitManager:
    """Gitマネージャーを取得"""
    if git_manager is None:
        raise RuntimeError("Git manager not initialized")
    return git_manager


mcp = FastMCP(
    "brain",
    instructions="""AIの長期記憶。経験から学び、同じ失敗を繰り返さない。

タスク開始時:
1. search で過去の経験を想起
2. 見つかれば get で思い出し、その通りに実行
3. 新しい経験は create で記憶、失敗から学んだら update で強化""",
)


def get_storage() -> KnowledgeStorage:
    """ストレージを取得"""
    if storage is None:
        raise RuntimeError("Storage not initialized")
    return storage


def get_search() -> SemanticSearch:
    """検索エンジンを取得"""
    if search_engine is None:
        raise RuntimeError("Search engine not initialized")
    return search_engine


def _expand_related(
    s: KnowledgeStorage,
    related_names: list[str],
    hops: int,
    visited: set[str] | None = None,
) -> list[dict]:
    """関連知識をNホップ先まで展開（自動関連用）

    Args:
        s: ストレージ
        related_names: 関連知識名のリスト
        hops: 残りホップ数
        visited: 訪問済み知識名（循環防止）

    Returns:
        関連知識のサマリーリスト
    """
    if hops <= 0 or not related_names:
        return []

    if visited is None:
        visited = set()

    search = get_search()
    results = []

    for name in related_names:
        if name in visited:
            continue
        visited.add(name)

        knowledge = s.load(name)
        if knowledge is None:
            continue

        # 次のホップ: この知識に類似する知識を取得
        next_similar_names = [
            summary.name for summary, _ in search.find_similar(name, top_k=3)
        ]
        nested_related = _expand_related(s, next_similar_names, hops - 1, visited)

        results.append(
            {
                "name": knowledge.name,
                "description": knowledge.description,
                "related": nested_related,
            }
        )

    return results


@mcp.tool()
async def search(query: str) -> list[dict]:
    """過去の経験を想起。タスク開始前に「これ、前にやったことあるか？」と記憶を探る。

    Args:
        query: タスクのキーワード（例: "PR", "deploy", "test"）
    """
    play_sound()
    results = get_search().search(query)
    return [{"name": r.name, "description": r.description} for r in results]


@mcp.tool()
async def get(name: str, hops: int = 2) -> dict:
    """記憶を思い出す。過去の経験の詳細を取得し、その通りに実行する。

    Args:
        name: searchで見つけた知識名
        hops: 連想する関連記憶の深さ（デフォルト: 2、最大: 5）
    """
    play_sound()

    # hopsのバリデーション
    hops = max(0, min(hops, 5))

    s = get_storage()
    search_eng = get_search()
    knowledge = s.load(name)
    if knowledge is None:
        raise ValueError(f"Knowledge '{name}' not found")

    # last_usedを更新（忘却システム用）
    knowledge.last_used = date.today()
    s.save(knowledge)

    # Embeddingベースで類似知識を自動取得
    similar = search_eng.find_similar(name, top_k=5)
    similar_names = [summary.name for summary, _ in similar]

    # N ホップ先まで関連知識を展開
    related_summaries = _expand_related(s, similar_names, hops, visited={name})

    return {
        "name": knowledge.name,
        "description": knowledge.description,
        "content": knowledge.content,
        "version": knowledge.version,
        "related": related_summaries,
    }


@mcp.tool()
async def create(name: str, description: str, instructions_markdown: str) -> dict:
    """新しい知識を記録。タスク成功後、再利用できる手順を保存する。

    ここでの「経験」を記録する。AIが元々知っている一般知識ではなく、
    実際にここで試行錯誤して得た知見や、ユーザーから教わった手順を保存する。

    例:
    - ○ ここ固有のデプロイ手順（特殊な環境変数、独自スクリプト）
    - ○ ユーザーが「こうやって」と教えてくれたワークフロー
    - × git の一般的な使い方（AIは既に知っている）
    - × React公式ドキュメントに書いてある内容

    Args:
        name: kebab-case識別名（例: "deploy-staging"）
        description: いつ使うか（例: "ステージング環境にデプロイしたいとき"）
        instructions_markdown: 手順をMarkdownで記述
    """
    s = get_storage()

    # 既存知識のチェック
    if s.load(name) is not None:
        raise ValueError(f"Knowledge '{name}' already exists")

    # 確認ダイアログ
    if not show_create_confirmation(name, description):
        return {"cancelled": True, "message": "ユーザーが作成をキャンセルしました"}

    # 知識の作成（バリデーションエラーはそのままraise）
    knowledge = Knowledge(
        name=name, description=description, content=instructions_markdown
    )

    # 保存
    s.save(knowledge)

    # インデックスに追加
    get_search().add(knowledge)

    # Git commit + push
    get_git().commit_and_push(name, "create")

    return {
        "name": knowledge.name,
        "description": knowledge.description,
        "content": knowledge.content,
        "version": knowledge.version,
    }


@mcp.tool()
async def update(
    name: str,
    description: str | None = None,
    content_markdown: str | None = None,
) -> dict:
    """記憶を強化。失敗から学んだ教訓や、より良いやり方で上書きする。

    Args:
        name: 更新する知識名
        description: 説明・使用タイミング（任意）
        content_markdown: 知識の手順・詳細（任意）
    """
    play_sound()
    s = get_storage()
    knowledge = s.load(name)
    if knowledge is None:
        raise ValueError(f"Knowledge '{name}' not found")

    # 更新を適用
    if description is not None:
        knowledge.description = description
    if content_markdown is not None:
        knowledge.content = content_markdown

    # バージョンを上げる
    knowledge.version += 1

    # 保存
    s.save(knowledge)

    # インデックスを更新
    get_search().update(knowledge)

    # Git commit + push
    get_git().commit_and_push(name, "update")

    return {
        "name": knowledge.name,
        "description": knowledge.description,
        "content": knowledge.content,
        "version": knowledge.version,
    }


@mcp.tool()
async def forget(name: str) -> dict:
    """記憶を忘却。間違った記憶や、もう必要ない経験を消去する。

    Args:
        name: 削除する知識名
    """
    play_sound()
    s = get_storage()

    # 存在確認
    knowledge = s.load(name)
    if knowledge is None:
        raise ValueError(f"Knowledge '{name}' not found")

    # 検索インデックスから削除
    get_search().remove(name)

    # ファイルを削除
    s.delete(name)

    # Git commit + push
    get_git().commit_and_push(name, "forget")

    return {"deleted": name}


def _load_all(s: KnowledgeStorage) -> list[Knowledge]:
    """全知識を読み込み"""
    items = []
    for summary in s.list_all():
        knowledge = s.load(summary.name)
        if knowledge:
            items.append(knowledge)
    return items


def main() -> None:
    """エントリポイント"""
    global storage, search_engine, git_manager

    # 知識ベースディレクトリ: MCP_BRAIN_DIR > 引数 > ~/.mcp-brain
    default_dir = Path.home() / ".mcp-brain"
    env_dir = os.environ.get("MCP_BRAIN_DIR", "").strip()
    knowledge_path = env_dir or (sys.argv[1] if len(sys.argv) > 1 else str(default_dir))
    knowledge_dir = Path(knowledge_path).expanduser().resolve()
    logger.info("Knowledge directory: %s", knowledge_dir)

    # Git管理を初期化（必須: リモート接続を検証）
    try:
        git_manager = GitManager(knowledge_dir)
        git_manager.verify_remote()
    except GitNotAvailableError as e:
        logger.error("Git integration required: %s", e)
        sys.exit(1)

    # ストレージを初期化
    storage = KnowledgeStorage(knowledge_dir)

    # 検索エンジンを初期化（キャッシュディレクトリを指定）
    search_engine = SemanticSearch(cache_dir=knowledge_dir)

    # 起動時に全知識をインデックス化（キャッシュがあれば即座に完了）
    logger.info("Initializing search index...")
    items = _load_all(storage)
    search_engine.build(items)
    logger.info("Search index ready (%d items)", len(items))

    # 忘却チェック: 古い知識があればGUIで通知
    stale = storage.get_stale(threshold_days=30)
    if stale:
        stale_names = [k.name for k in stale]
        logger.info("Found %d stale knowledge items", len(stale_names))

        if show_stale_dialog(stale_names):
            # 削除を選択（バッチ処理なので1件の失敗で中断しない）
            for k in stale:
                search_engine.remove(k.name)
                storage.delete(k.name)
                try:
                    git_manager.commit_and_push(k.name, "forget")
                except GitOperationError:
                    logger.exception("Failed to commit stale deletion: %s", k.name)
            logger.info("Deleted %d stale knowledge items", len(stale))

    mcp.run()


if __name__ == "__main__":
    main()
