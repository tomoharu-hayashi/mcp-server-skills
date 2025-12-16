#!/usr/bin/env python3
"""UserPromptSubmit Hook: Brain自動コンテキスト注入"""

import json
import sys

from brain_client import search_and_get


def main() -> None:
    try:
        data = json.load(sys.stdin)
        knowledge = search_and_get(data.get("prompt", ""))

        if knowledge:
            sys.stdout.write(
                f"""[自動取得: Brain MCP Server]
Hooksにより現在の会話をクエリとして、過去のナレッジが自動検索されました。
必要に応じて参考にしてください（必須ではありません）。
---
{knowledge}
---"""
            )
    except Exception:
        pass


if __name__ == "__main__":
    main()
