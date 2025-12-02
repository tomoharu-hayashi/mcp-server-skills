"""FastMCPサーバー定義"""

import logging
import os
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .git import GitManager
from .models import Skill, SkillSummary, SkillUpdate
from .search import HybridSearch
from .storage import SkillStorage

logger = logging.getLogger(__name__)


def play_sound() -> None:
    """macOSの効果音を非同期で再生"""
    subprocess.Popen(
        ["afplay", "/System/Library/Sounds/Hero.aiff"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# グローバルインスタンス（mainで初期化）
storage: SkillStorage | None = None
search_engine: HybridSearch | None = None
git_manager: GitManager | None = None

mcp = FastMCP(
    "skills",
    instructions="""スキル学習サーバー。タスク実行時の推奨フロー:
1. search_skills(タスクのキーワード) で既存スキルを検索
2. 見つかれば get_skill(name) で手順を取得し従う
3. スキルがなければ自力で実行、成功したら create_skill で記録
4. 失敗したら update_skill で注意点を追記""",
)


def get_storage() -> SkillStorage:
    """ストレージを取得"""
    if storage is None:
        raise RuntimeError("Storage not initialized")
    return storage


def get_search() -> HybridSearch:
    """検索エンジンを取得"""
    if search_engine is None:
        raise RuntimeError("Search engine not initialized")
    return search_engine


@mcp.tool()
def search_skills(query: str) -> list[SkillSummary]:
    """タスク開始前に関連スキルを検索。見つかったらget_skillで詳細を取得し手順に従う。

    Args:
        query: タスクのキーワード（例: "PR", "deploy", "test"）
    """
    play_sound()
    return get_search().search(query)


@mcp.tool()
def get_skill(name: str) -> Skill | None:
    """スキルの手順・注意点を取得。contentに従って作業を進める。

    Args:
        name: search_skillsで見つけたスキル名
    """
    play_sound()
    return get_storage().load_skill(name)


@mcp.tool()
def create_skill(name: str, description: str, instructions: str) -> Skill:
    """新しいスキルを記録。タスク成功後、再利用できる手順を保存する。

    Args:
        name: kebab-case識別名（例: "deploy-staging"）
        description: いつ使うか（例: "ステージング環境にデプロイしたいとき"）
        instructions: 手順をMarkdownで記述
    """
    play_sound()
    s = get_storage()

    # 既存スキルのチェック
    if s.load_skill(name) is not None:
        raise ValueError(f"Skill '{name}' already exists")

    skill = Skill(name=name, description=description, content=instructions)
    s.save_skill(skill)

    # インデックスに追加
    get_search().add(skill)

    # Git commit + push
    if git_manager:
        git_manager.commit_and_push(name, "create")

    return skill


@mcp.tool()
def update_skill(name: str, updates: SkillUpdate) -> Skill:
    """スキルを改善。失敗から学んだ注意点や、より良い手順を追記する。

    Args:
        name: 更新するスキル名
        updates: 変更内容（description, content等）
    """
    play_sound()
    s = get_storage()
    skill = s.load_skill(name)
    if skill is None:
        raise ValueError(f"Skill '{name}' not found")

    # 更新を適用
    if updates.description is not None:
        skill.description = updates.description
    if updates.allowed_tools is not None:
        skill.allowed_tools = updates.allowed_tools
    if updates.content is not None:
        skill.content = updates.content

    # バージョンを上げる
    skill.version += 1

    s.save_skill(skill)

    # インデックスを更新
    get_search().update(skill)

    # Git commit + push
    if git_manager:
        git_manager.commit_and_push(name, "update")

    return skill


def _load_all_skills(s: SkillStorage) -> list[Skill]:
    """全スキルを読み込み"""
    skills = []
    for summary in s.list_skills():
        skill = s.load_skill(summary.name)
        if skill:
            skills.append(skill)
    return skills


def main() -> None:
    """エントリポイント"""
    global storage, search_engine, git_manager

    # 環境変数 > コマンドライン引数 > デフォルト(~/.mcp-skills)
    default_dir = Path.home() / ".mcp-skills"
    skills_path = os.environ.get("MCP_SKILLS_DIR") or (
        sys.argv[1] if len(sys.argv) > 1 else str(default_dir)
    )

    skills_dir = Path(skills_path)
    storage = SkillStorage(skills_dir)

    # Git管理を初期化
    git_manager = GitManager(skills_dir)

    # 検索エンジンを初期化
    search_engine = HybridSearch()

    # 起動時に全スキルをインデックス化
    logger.info("Building search index...")
    skills = _load_all_skills(storage)
    search_engine.build(skills)
    logger.info("Search index built with %d skills", len(skills))

    mcp.run()


if __name__ == "__main__":
    main()
