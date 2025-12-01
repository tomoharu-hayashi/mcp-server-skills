"""Pydanticモデル定義"""

from datetime import date

from pydantic import BaseModel, Field


class SkillSummary(BaseModel):
    """スキルの概要（検索結果用）"""

    name: str = Field(description="スキル識別名")
    description: str = Field(description="説明・使用タイミング")


class Skill(BaseModel):
    """スキルの完全な情報"""

    # Claude Code 互換（必須）
    name: str = Field(description="スキル識別名")
    description: str = Field(description="説明・使用タイミング")

    # Claude Code 互換（オプション）
    allowed_tools: str | None = Field(default=None, description="ツール制限")

    # 拡張フィールド（学習用）
    version: int = Field(default=1, description="バージョン番号")
    created: date = Field(default_factory=date.today, description="作成日")
    last_used: date | None = Field(default=None, description="最終使用日")

    # Markdown本文
    content: str = Field(default="", description="スキルの手順・詳細")

    def to_summary(self) -> SkillSummary:
        """概要に変換"""
        return SkillSummary(name=self.name, description=self.description)


class SkillUpdate(BaseModel):
    """スキル更新用のパラメータ"""

    description: str | None = Field(default=None, description="説明・使用タイミング")
    allowed_tools: str | None = Field(default=None, description="ツール制限")
    content: str | None = Field(default=None, description="スキルの手順・詳細")
