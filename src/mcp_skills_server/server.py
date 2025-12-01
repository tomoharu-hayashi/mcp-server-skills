"""FastMCPサーバー定義"""

import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .models import Skill, SkillSummary, SkillUpdate
from .storage import SkillStorage

# グローバルなストレージインスタンス（mainで初期化）
storage: SkillStorage | None = None

mcp = FastMCP("skills")


def get_storage() -> SkillStorage:
    """ストレージを取得"""
    if storage is None:
        raise RuntimeError("Storage not initialized")
    return storage


@mcp.tool()
def search_skills(query: str) -> list[SkillSummary]:
    """タスクに関連するスキルを検索

    Args:
        query: 検索クエリ（スキル名や説明に含まれる文字列）

    Returns:
        マッチしたスキルの概要リスト
    """
    return get_storage().search_skills(query)


@mcp.tool()
def get_skill(name: str) -> Skill | None:
    """スキルの詳細を取得

    Args:
        name: スキル識別名

    Returns:
        スキルの完全な情報（存在しない場合はNone）
    """
    return get_storage().load_skill(name)


@mcp.tool()
def create_skill(name: str, description: str, instructions: str) -> Skill:
    """新しいスキルを作成

    Args:
        name: スキル識別名
        description: 説明・使用タイミング
        instructions: スキルの手順・詳細（Markdown形式）

    Returns:
        作成されたスキル
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
    """既存スキルを更新

    Args:
        name: スキル識別名
        updates: 更新内容（description, allowed_tools, content）

    Returns:
        更新されたスキル
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

    if len(sys.argv) < 2:
        sys.stderr.write("Usage: mcp-skills-server <skills-directory>\n")
        sys.exit(1)

    skills_dir = Path(sys.argv[1])
    storage = SkillStorage(skills_dir)

    mcp.run()


if __name__ == "__main__":
    main()
