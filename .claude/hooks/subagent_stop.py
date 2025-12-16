#!/usr/bin/env python3
"""SubagentStop Hook: サブエージェント終了時のBrain自動コンテキスト注入"""

import json
import sys
from pathlib import Path

from brain_client import search_and_get


def extract_query_from_transcript(transcript_path: str) -> str:
    """transcript.jsonlから最後のユーザーメッセージを抽出"""
    path = Path(transcript_path).expanduser()
    if not path.exists():
        return ""

    messages = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("type") == "user":
                    content = entry.get("message", {}).get("content", "")
                    if content:
                        messages.append(content)
            except (json.JSONDecodeError, KeyError):
                continue

    return messages[-1][:200] if messages else ""


def main() -> None:
    try:
        data = json.load(sys.stdin)

        # 無限ループ防止
        if data.get("stop_hook_active"):
            sys.exit(0)

        query = extract_query_from_transcript(data.get("transcript_path", ""))
        knowledge = search_and_get(query)

        if knowledge:
            output = {
                "decision": "block",
                "reason": f"""[自動取得: Brain MCP Server]
Hooksにより現在の会話をクエリとして、過去のナレッジが自動検索されました。
必要に応じて参考にしてください（必須ではありません）。
---
{knowledge}
---""",
            }
            sys.stdout.write(f"{json.dumps(output)}\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
