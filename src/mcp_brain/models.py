"""Pydanticモデル定義"""

import re
from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

# 知識名の正規表現: kebab-case（英数字とハイフンのみ）
KNOWLEDGE_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# プロジェクトベースディレクトリ
PJ_BASE_DIR = Path.home() / "pj"


def get_valid_project_names() -> set[str]:
    """~/pj 以下の全プロジェクトフォルダ名を取得"""
    if not PJ_BASE_DIR.exists():
        return set()

    projects = set()
    # ~/pj 直下のカテゴリ（my, work, other）を走査
    for category in PJ_BASE_DIR.iterdir():
        if category.is_dir() and not category.name.startswith("."):
            # カテゴリ内のプロジェクトフォルダを追加
            for project in category.iterdir():
                if project.is_dir() and not project.name.startswith("."):
                    projects.add(project.name)
    return projects


def validate_project_name(v: str) -> str:
    """プロジェクト名のバリデーション

    Args:
        v: プロジェクト名

    Returns:
        バリデーション済みのプロジェクト名

    Raises:
        ValueError: 無効なプロジェクト名の場合
    """
    if not v:
        raise ValueError("project cannot be empty")
    if len(v) > 100:
        raise ValueError("project is too long (max 100 characters)")

    # "global"は常に許可
    if v == "global":
        return v

    # ~/pj 以下に存在するプロジェクト名のみ許可
    valid_projects = get_valid_project_names()
    if v not in valid_projects:
        raise ValueError(
            f"Invalid project '{v}': must be 'global' or an existing project in ~/pj. "
            f"Available: {sorted(valid_projects)}"
        )
    return v


class KnowledgeSummary(BaseModel):
    """知識の概要（検索結果用）"""

    name: str = Field(description="知識識別名")
    description: str = Field(description="説明・使用タイミング")
    project: str = Field(default="global", description="所属プロジェクト")


class Knowledge(BaseModel):
    """知識の完全な情報"""

    name: str = Field(description="知識識別名")
    description: str = Field(description="説明・使用タイミング")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """知識名のバリデーション（kebab-case、ディレクトリトラバーサル防止）"""
        if not v:
            raise ValueError("name cannot be empty")
        if not KNOWLEDGE_NAME_PATTERN.match(v):
            raise ValueError(
                f"Invalid name '{v}': must be kebab-case (e.g., 'my-knowledge')"
            )
        if len(v) > 100:
            raise ValueError("name is too long (max 100 characters)")
        return v

    # プロジェクト分類
    project: str = Field(default="global", description="所属プロジェクト")

    @field_validator("project")
    @classmethod
    def validate_project(cls, v: str) -> str:
        """プロジェクト名のバリデーション"""
        return validate_project_name(v)

    # オプション
    allowed_tools: str | None = Field(default=None, description="ツール制限")

    # 拡張フィールド（学習用）
    version: int = Field(default=1, description="バージョン番号")
    created: date = Field(default_factory=date.today, description="作成日")
    last_used: date | None = Field(default=None, description="最終使用日")

    # Markdown本文
    content: str = Field(default="", description="知識の手順・詳細")

    def to_summary(self) -> KnowledgeSummary:
        """概要に変換"""
        return KnowledgeSummary(
            name=self.name, description=self.description, project=self.project
        )
