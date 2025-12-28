#!/usr/bin/env python3
"""
Cursor stop hook: /jarvis の自動ループ

- `.cache/jarvis/loop.enabled` が存在する時だけ継続する
- ユーザーが停止(aborted) / エラー(error) ならループをOFFにする
"""

from __future__ import annotations

import contextlib
import json
import sys
from pathlib import Path


def _workspace_root(payload: dict) -> Path:
    roots = payload.get("workspace_roots")
    if isinstance(roots, list) and roots:
        return Path(str(roots[0]))
    return Path.cwd()


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        payload = {}

    root = _workspace_root(payload)
    flag = root / ".cache" / "jarvis" / "loop.enabled"

    status = payload.get("status")
    loop_count = payload.get("loop_count", 0)
    if not isinstance(loop_count, int):
        loop_count = 0

    # ユーザー停止/エラー時は即OFF（止めたい時に確実に止まる）
    if flag.exists() and status in {"aborted", "error"}:
        with contextlib.suppress(FileNotFoundError):
            flag.unlink()

    enabled = flag.exists()

    out: dict[str, str] = {}
    if enabled and status == "completed" and loop_count < 5:
        out["followup_message"] = "/jarvis_agent 続けて"

    sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
