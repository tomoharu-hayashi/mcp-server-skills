"""FastMCPサーバー定義"""

import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .models import Skill, SkillSummary, SkillUpdate
from .storage import SkillStorage

# グローバルなストレージインスタンス（mainで初期化）
storage: SkillStorage | None = None

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


@mcp.tool()
def search_skills(query: str) -> list[SkillSummary]:
    """タスク開始前に関連スキルを検索。見つかったらget_skillで詳細を取得し手順に従う。

    Args:
        query: タスクのキーワード（例: "PR", "deploy", "test"）
    """
    return get_storage().search_skills(query)


@mcp.tool()
def get_skill(name: str) -> Skill | None:
    """スキルの手順・注意点を取得。contentに従って作業を進める。

    Args:
        name: search_skillsで見つけたスキル名
    """
    return get_storage().load_skill(name)


@mcp.tool()
def create_skill(name: str, description: str, instructions: str) -> Skill:
    """新しいスキルを記録。タスク成功後、再利用できる手順を保存する。

    Args:
        name: kebab-case識別名（例: "deploy-staging"）
        description: いつ使うか（例: "ステージング環境にデプロイしたいとき"）
        instructions: 手順をMarkdownで記述
    """
    s = get_storage()

    # 既存スキルのチェック
    if s.load_skill(name) is not None:
        raise ValueError(f"Skill '{name}' already exists")

    skill = Skill(name=name, description=description, content=instructions)
    s.save_skill(skill)
    return skill


@mcp.tool()
def update_skill(name: str, updates: SkillUpdate) -> Skill:
    """スキルを改善。失敗から学んだ注意点や、より良い手順を追記する。

    Args:
        name: 更新するスキル名
        updates: 変更内容（description, content等）
    """
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
    return skill


def main() -> None:
    """エントリポイント"""
    global storage

    # 環境変数 > コマンドライン引数 > デフォルト(~/.mcp-skills)
    default_dir = Path.home() / ".mcp-skills"
    skills_path = os.environ.get("MCP_SKILLS_DIR") or (
        sys.argv[1] if len(sys.argv) > 1 else str(default_dir)
    )

    storage = SkillStorage(Path(skills_path))
    mcp.run()


if __name__ == "__main__":
    main()
