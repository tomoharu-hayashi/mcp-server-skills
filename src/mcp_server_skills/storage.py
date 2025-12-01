"""スキルファイルの読み書き"""

import re
from datetime import date
from pathlib import Path

import yaml

from .models import Skill, SkillSummary

# YAMLフロントマターのパターン
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


class SkillStorage:
    """スキルファイルのストレージ"""

    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def _skill_path(self, name: str) -> Path:
        """スキルファイルのパスを取得"""
        return self.skills_dir / name / "SKILL.md"

    def list_skills(self) -> list[SkillSummary]:
        """全スキルの概要を取得"""
        skills = []
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    skill = self.load_skill(skill_dir.name)
                    if skill:
                        skills.append(skill.to_summary())
        return skills

    def search_skills(self, query: str) -> list[SkillSummary]:
        """クエリに一致するスキルを検索"""
        query_lower = query.lower()
        results = []
        for summary in self.list_skills():
            # name と description で検索
            if (
                query_lower in summary.name.lower()
                or query_lower in summary.description.lower()
            ):
                results.append(summary)
        return results

    def load_skill(self, name: str) -> Skill | None:
        """スキルを読み込み"""
        path = self._skill_path(name)
        if not path.exists():
            return None

        text = path.read_text(encoding="utf-8")
        return self._parse_skill_file(name, text)

    def save_skill(self, skill: Skill) -> None:
        """スキルを保存"""
        path = self._skill_path(skill.name)
        path.parent.mkdir(parents=True, exist_ok=True)
        text = self._serialize_skill(skill)
        path.write_text(text, encoding="utf-8")

    def delete_skill(self, name: str) -> bool:
        """スキルを削除"""
        path = self._skill_path(name)
        if path.exists():
            path.unlink()
            # 空ディレクトリも削除
            if path.parent.exists() and not any(path.parent.iterdir()):
                path.parent.rmdir()
            return True
        return False

    def _parse_skill_file(self, name: str, text: str) -> Skill:
        """SKILL.mdファイルをパース"""
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

        return Skill(
            name=frontmatter.get("name", name),
            description=frontmatter.get("description", ""),
            allowed_tools=allowed_tools,
            version=frontmatter.get("version", 1),
            created=created or date.today(),
            last_used=last_used,
            content=content.strip(),
        )

    def _serialize_skill(self, skill: Skill) -> str:
        """スキルをSKILL.md形式にシリアライズ"""
        frontmatter: dict = {
            "name": skill.name,
            "description": skill.description,
        }

        # オプションフィールド
        if skill.allowed_tools:
            frontmatter["allowed-tools"] = skill.allowed_tools

        # 拡張フィールド
        frontmatter["version"] = skill.version
        frontmatter["created"] = skill.created.isoformat()
        if skill.last_used:
            frontmatter["last_used"] = skill.last_used.isoformat()

        yaml_str = yaml.dump(
            frontmatter, allow_unicode=True, sort_keys=False, default_flow_style=False
        )
        return f"---\n{yaml_str}---\n\n{skill.content}"
