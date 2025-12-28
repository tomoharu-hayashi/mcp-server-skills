#!/usr/bin/env python3
"""beforeSubmitPrompt Hook: Makefile help injection."""

import json
import subprocess
import sys
from pathlib import Path


def _workspace_root(payload: dict) -> Path:
    roots = payload.get("workspace_roots") or payload.get("workspaceRoots")
    if isinstance(roots, list) and roots:
        return Path(str(roots[0]))
    return Path.cwd()


def _read_make_help(root: Path) -> str:
    try:
        result = subprocess.run(
            ["make", "help"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        payload = {}

    make_help = _read_make_help(_workspace_root(payload))

    output = {"continue": True}
    if make_help:
        output["user_message"] = f"""[自動取得: Makefile help]
make help の出力です。コマンド定義の参照に使ってください。
---
{make_help}
---"""

    sys.stdout.write(json.dumps(output) + "\n")


if __name__ == "__main__":
    main()
