"""知識ファイルの読み書き"""

import re
from datetime import date
from pathlib import Path

import yaml

from .models import Knowledge, KnowledgeSummary

# YAMLフロントマターのパターン
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

# グローバル知識用のディレクトリ名
GLOBAL_SCOPE = "global"


def path_to_scope(path: Path) -> str:
    """パスをスコープ文字列に変換（先頭/を除去）"""
    return str(path).lstrip("/")


def get_scope_hierarchy(project_path: Path | None) -> list[str]:
    """プロジェクトパスからスコープ階層を生成

    例: /Users/thayashi/pj/my/project
    → ["Users/thayashi/pj/my/project",
       "Users/thayashi/pj/my",
       "Users/thayashi/pj",
       "global"]
    """
    if project_path is None:
        return [GLOBAL_SCOPE]

    scopes = []
    current = project_path.resolve()

    # ルートに達するまで親を辿る
    while current != current.parent:
        scopes.append(path_to_scope(current))
        current = current.parent

    # 最後にglobalを追加
    scopes.append(GLOBAL_SCOPE)
    return scopes


class KnowledgeStorage:
    """知識ファイルのストレージ"""

    def __init__(self, knowledge_dir: Path, project_path: Path | None = None) -> None:
        self.base_dir = knowledge_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.project_path = project_path
        self.scope_hierarchy = get_scope_hierarchy(project_path)

    @property
    def knowledge_dir(self) -> Path:
        """現在のプロジェクトスコープの知識ディレクトリ"""
        if self.project_path:
            return self.base_dir / path_to_scope(self.project_path)
        return self.base_dir / GLOBAL_SCOPE

    def set_project(self, project_path: Path | None) -> None:
        """プロジェクトパスを設定"""
        self.project_path = project_path
        self.scope_hierarchy = get_scope_hierarchy(project_path)

    def _knowledge_path(self, name: str, scope: str | None = None) -> Path:
        """知識ファイルのパスを取得"""
        if scope:
            return self.base_dir / scope / name / "KNOWLEDGE.md"
        return self.knowledge_dir / name / "KNOWLEDGE.md"

    def _list_scope(self, scope: str) -> list[KnowledgeSummary]:
        """特定スコープの知識を取得"""
        scope_dir = self.base_dir / scope
        if not scope_dir.exists():
            return []

        items = []
        for item_dir in scope_dir.iterdir():
            if item_dir.is_dir():
                knowledge_file = item_dir / "KNOWLEDGE.md"
                if knowledge_file.exists():
                    knowledge = self.load(item_dir.name, scope=scope)
                    if knowledge:
                        items.append(knowledge.to_summary())
        return items

    def list_all(self) -> list[KnowledgeSummary]:
        """スコープ階層内の全知識を取得（重複除去、プロジェクト優先）"""
        seen_names: set[str] = set()
        items = []

        # スコープ階層順（プロジェクト固有 → 親 → global）で取得
        for scope in self.scope_hierarchy:
            for summary in self._list_scope(scope):
                if summary.name not in seen_names:
                    seen_names.add(summary.name)
                    items.append(summary)

        return items

    def list_current_scope(self) -> list[KnowledgeSummary]:
        """現在のプロジェクトスコープのみの知識を取得"""
        if not self.scope_hierarchy:
            return []
        return self._list_scope(self.scope_hierarchy[0])

    def search(self, query: str) -> list[KnowledgeSummary]:
        """クエリに一致する知識を検索"""
        query_lower = query.lower()
        results = []
        for summary in self.list_all():
            if (
                query_lower in summary.name.lower()
                or query_lower in summary.description.lower()
            ):
                results.append(summary)
        return results

    def load(self, name: str, scope: str | None = None) -> Knowledge | None:
        """知識を読み込み

        scopeが指定されていない場合、スコープ階層を上から検索
        """
        if scope:
            path = self._knowledge_path(name, scope=scope)
            if path.exists():
                text = path.read_text(encoding="utf-8")
                return self._parse_knowledge_file(name, text)
            return None

        # スコープ階層を検索
        for s in self.scope_hierarchy:
            path = self._knowledge_path(name, scope=s)
            if path.exists():
                text = path.read_text(encoding="utf-8")
                return self._parse_knowledge_file(name, text)

        return None

    def save(self, knowledge: Knowledge, scope: str | None = None) -> None:
        """知識を保存（デフォルトは現在のプロジェクトスコープ）"""
        if scope:
            path = self._knowledge_path(knowledge.name, scope=scope)
        else:
            path = self._knowledge_path(knowledge.name)
        path.parent.mkdir(parents=True, exist_ok=True)
        text = self._serialize_knowledge(knowledge)
        path.write_text(text, encoding="utf-8")

    def delete(self, name: str) -> bool:
        """知識を削除"""
        path = self._knowledge_path(name)
        if path.exists():
            path.unlink()
            # 空ディレクトリも削除
            if path.parent.exists() and not any(path.parent.iterdir()):
                path.parent.rmdir()
            return True
        return False

    def _parse_knowledge_file(self, name: str, text: str) -> Knowledge:
        """KNOWLEDGE.mdファイルをパース"""
        frontmatter: dict = {}
        content = text

        match = FRONTMATTER_PATTERN.match(text)
        if match:
            frontmatter = yaml.safe_load(match.group(1)) or {}
            content = text[match.end() :]

        # allowed-tools -> allowed_tools の変換
        allowed_tools = frontmatter.get("allowed-tools") or frontmatter.get(
            "allowed_tools"
        )

        # 日付の変換
        created = frontmatter.get("created")
        if isinstance(created, str):
            created = date.fromisoformat(created)

        last_used = frontmatter.get("last_used")
        if isinstance(last_used, str):
            last_used = date.fromisoformat(last_used)

        return Knowledge(
            name=frontmatter.get("name", name),
            description=frontmatter.get("description", ""),
            allowed_tools=allowed_tools,
            version=frontmatter.get("version", 1),
            created=created or date.today(),
            last_used=last_used,
            content=content.strip(),
        )

    def _serialize_knowledge(self, knowledge: Knowledge) -> str:
        """知識をKNOWLEDGE.md形式にシリアライズ"""
        frontmatter: dict = {
            "name": knowledge.name,
            "description": knowledge.description,
        }

        # オプションフィールド
        if knowledge.allowed_tools:
            frontmatter["allowed-tools"] = knowledge.allowed_tools

        # 拡張フィールド
        frontmatter["version"] = knowledge.version
        frontmatter["created"] = knowledge.created.isoformat()
        if knowledge.last_used:
            frontmatter["last_used"] = knowledge.last_used.isoformat()

        yaml_str = yaml.dump(
            frontmatter, allow_unicode=True, sort_keys=False, default_flow_style=False
        )
        return f"---\n{yaml_str}---\n\n{knowledge.content}"
