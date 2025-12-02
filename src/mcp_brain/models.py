"""Pydanticモデル定義"""

from datetime import date

from pydantic import BaseModel, Field


class KnowledgeSummary(BaseModel):
    """知識の概要（検索結果用）"""

    name: str = Field(description="知識識別名")
    description: str = Field(description="説明・使用タイミング")


class Knowledge(BaseModel):
    """知識の完全な情報"""

    name: str = Field(description="知識識別名")
    description: str = Field(description="説明・使用タイミング")

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


class KnowledgeUpdate(BaseModel):
    """知識更新用のパラメータ"""

    description: str | None = Field(default=None, description="説明・使用タイミング")
    allowed_tools: str | None = Field(default=None, description="ツール制限")
    content: str | None = Field(default=None, description="知識の手順・詳細")
