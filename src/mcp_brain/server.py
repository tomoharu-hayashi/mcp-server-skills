"""FastMCPサーバー定義"""

import logging
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

from .git import GitManager
from .models import Knowledge
from .search import SemanticSearch
from .storage import KnowledgeStorage

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
base_knowledge_dir: Path | None = None

mcp = FastMCP(
    "brain",
    instructions="""知識学習サーバー。タスク実行時の推奨フロー:
1. search(タスクのキーワード) で既存知識を検索
2. 見つかれば get(name) で手順を取得し従う
3. 知識がなければ自力で実行、成功したら create で記録
4. 失敗したら update で注意点を追記

知識はプロジェクトごとに自動スコープされます。
現在のプロジェクト固有の知識が優先され、親ディレクトリやグローバルの知識も検索されます。""",
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


def _uri_to_path(uri: str) -> Path | None:
    """file:// URIをPathに変換"""
    parsed = urlparse(uri)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path))
    return None


async def _get_project_path(ctx: Context[ServerSession, None]) -> Path | None:
    """クライアントのrootsからプロジェクトパスを取得"""
    try:
        roots_result = await ctx.session.list_roots()
        if roots_result.roots:
            return _uri_to_path(str(roots_result.roots[0].uri))
    except Exception as e:
        logger.debug("Failed to get roots: %s", e)
    return None


async def _with_project_scope(ctx: Context[ServerSession, None]) -> None:
    """プロジェクトスコープを設定"""
    project_path = await _get_project_path(ctx)
    s = get_storage()

    # スコープが変わった場合のみ更新
    if s.project_path != project_path:
        s.set_project(project_path)
        # インデックスを再構築
        items = _load_all(s)
        get_search().build(items)
        logger.info("Project scope: %s", project_path or "global")


@mcp.tool()
async def search(query: str, ctx: Context[ServerSession, None]) -> list[dict]:
    """タスク開始前に関連知識を検索。見つかればgetで詳細を取得し手順に従う。

    Args:
        query: タスクのキーワード（例: "PR", "deploy", "test"）
    """
    play_sound()
    await _with_project_scope(ctx)
    results = get_search().search(query)
    return [{"name": r.name, "description": r.description} for r in results]


@mcp.tool()
async def get(name: str, ctx: Context[ServerSession, None]) -> dict:
    """知識の詳細（手順・注意点）を取得。contentに従って作業を進める。

    Args:
        name: searchで見つけた知識名
    """
    play_sound()
    await _with_project_scope(ctx)
    knowledge = get_storage().load(name)
    if knowledge is None:
        return {"error": f"Knowledge '{name}' not found"}
    return {
        "name": knowledge.name,
        "description": knowledge.description,
        "content": knowledge.content,
        "version": knowledge.version,
    }


@mcp.tool()
async def create(
    name: str, description: str, instructions: str, ctx: Context[ServerSession, None]
) -> dict:
    """新しい知識を記録。タスク成功後、再利用できる手順を保存する。

    Args:
        name: kebab-case識別名（例: "deploy-staging"）
        description: いつ使うか（例: "ステージング環境にデプロイしたいとき"）
        instructions: 手順をMarkdownで記述
    """
    play_sound()
    await _with_project_scope(ctx)
    s = get_storage()

    # 既存知識のチェック
    if s.load(name) is not None:
        raise ValueError(f"Knowledge '{name}' already exists")

    knowledge = Knowledge(name=name, description=description, content=instructions)
    s.save(knowledge)

    # インデックスに追加
    get_search().add(knowledge)

    # Git commit + push
    if git_manager:
        git_manager.commit_and_push(name, "create")

    return {
        "name": knowledge.name,
        "description": knowledge.description,
        "content": knowledge.content,
        "version": knowledge.version,
    }


@mcp.tool()
async def update(
    name: str,
    ctx: Context[ServerSession, None],
    description: str | None = None,
    content: str | None = None,
) -> dict:
    """知識を改善。失敗から学んだ注意点や、より良い手順を追記する。

    Args:
        name: 更新する知識名
        description: 説明・使用タイミング（任意）
        content: 知識の手順・詳細（任意）
    """
    play_sound()
    await _with_project_scope(ctx)
    s = get_storage()
    knowledge = s.load(name)
    if knowledge is None:
        raise ValueError(f"Knowledge '{name}' not found")

    # 更新を適用
    if description is not None:
        knowledge.description = description
    if content is not None:
        knowledge.content = content

    # バージョンを上げる
    knowledge.version += 1

    s.save(knowledge)

    # インデックスを更新
    get_search().update(knowledge)

    # Git commit + push
    if git_manager:
        git_manager.commit_and_push(name, "update")

    return {
        "name": knowledge.name,
        "description": knowledge.description,
        "content": knowledge.content,
        "version": knowledge.version,
    }


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
    global storage, search_engine, git_manager, base_knowledge_dir

    # 知識ベースディレクトリ: MCP_BRAIN_DIR > 引数 > ~/.mcp-brain
    default_dir = Path.home() / ".mcp-brain"
    knowledge_path = os.environ.get("MCP_BRAIN_DIR") or (
        sys.argv[1] if len(sys.argv) > 1 else str(default_dir)
    )
    base_knowledge_dir = Path(knowledge_path)

    # 初期はglobalスコープで起動（ツール呼び出し時にrootsから自動設定）
    storage = KnowledgeStorage(base_knowledge_dir)

    # Git管理を初期化
    git_manager = GitManager(base_knowledge_dir)

    # 検索エンジンを初期化
    search_engine = SemanticSearch()

    # 起動時に全知識をインデックス化（初期はglobalスコープ）
    logger.info("Building search index...")
    items = _load_all(storage)
    search_engine.build(items)
    logger.info("Search index built with %d items", len(items))

    mcp.run()


if __name__ == "__main__":
    main()
