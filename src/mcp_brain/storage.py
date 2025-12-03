"""知識ファイルの読み書き"""

import logging
import re
from datetime import date, timedelta
from pathlib import Path

import yaml

from .models import Knowledge, KnowledgeSummary

logger = logging.getLogger(__name__)

# YAMLフロントマターのパターン
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


class KnowledgeStorage:
    """知識ファイルのストレージ"""

    def __init__(self, knowledge_dir: Path) -> None:
        if not knowledge_dir or str(knowledge_dir) == "":
            raise ValueError("knowledge_dir must not be empty")
        # 絶対パスに変換（resolve()で相対パスを解決）
        self.knowledge_dir = Path(knowledge_dir).expanduser().resolve()
        logger.info("KnowledgeStorage initialized: %s", self.knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

    def _knowledge_path(self, name: str) -> Path:
        """知識ファイルのパスを取得"""
        return self.knowledge_dir / name / "KNOWLEDGE.md"

    def list_all(self) -> list[KnowledgeSummary]:
        """全知識を取得"""
        items = []
        for item_dir in self.knowledge_dir.iterdir():
            if item_dir.is_dir():
                knowledge_file = item_dir / "KNOWLEDGE.md"
                if knowledge_file.exists():
                    knowledge = self.load(item_dir.name)
                    if knowledge:
                        items.append(knowledge.to_summary())
        return items

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

    def load(self, name: str) -> Knowledge | None:
        """知識を読み込み"""
        path = self._knowledge_path(name)
        if not path.exists():
            return None

        text = path.read_text(encoding="utf-8")
        return self._parse_knowledge_file(name, text)

    def save(self, knowledge: Knowledge) -> None:
        """知識を保存

        Raises:
            OSError: ファイル書き込みに失敗した場合
        """
        path = self._knowledge_path(knowledge.name)
        logger.info("Saving knowledge to: %s (knowledge_dir=%s)", path, self.knowledge_dir)

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            text = self._serialize_knowledge(knowledge)
            path.write_text(text, encoding="utf-8")
            logger.info("Knowledge saved successfully: %s", knowledge.name)
        except OSError as e:
            logger.error("Failed to save knowledge '%s' to '%s': %s", knowledge.name, path, e)
            raise

    def delete(self, name: str) -> bool:
        """知識を削除

        Returns:
            成功フラグ
        """
        path = self._knowledge_path(name)
        if not path.exists():
            return False

        path.unlink()
        # 空ディレクトリも削除
        if path.parent.exists() and not any(path.parent.iterdir()):
            path.parent.rmdir()
        return True

    def get_stale(self, threshold_days: int = 30) -> list[Knowledge]:
        """古い知識を取得（最終使用日からthreshold_days以上経過）"""
        cutoff = date.today() - timedelta(days=threshold_days)
        stale = []

        for summary in self.list_all():
            knowledge = self.load(summary.name)
            if knowledge is None:
                continue

            # last_usedがなければcreatedを使用
            last_active = knowledge.last_used or knowledge.created
            if last_active < cutoff:
                stale.append(knowledge)

        return stale

    def _parse_knowledge_file(self, name: str, text: str) -> Knowledge | None:
        """KNOWLEDGE.mdファイルをパース

        Returns:
            Knowledge または None（パース失敗時）
        """
        frontmatter: dict = {}
        content = text

        try:
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
        except (yaml.YAMLError, ValueError) as e:
            logger.warning("Failed to parse knowledge file '%s': %s", name, e)
            return None

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
