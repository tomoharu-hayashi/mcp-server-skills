"""Pydanticモデル定義"""

import re
from datetime import date

from pydantic import BaseModel, Field, field_validator

# 知識名の正規表現: kebab-case（英数字とハイフンのみ）
KNOWLEDGE_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class KnowledgeSummary(BaseModel):
    """知識の概要（検索結果用）"""

    name: str = Field(description="知識識別名")
    description: str = Field(description="説明・使用タイミング")


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
        return KnowledgeSummary(name=self.name, description=self.description)
