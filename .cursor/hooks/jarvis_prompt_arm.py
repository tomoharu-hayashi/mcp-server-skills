#!/usr/bin/env python3
"""beforeSubmitPrompt Hook: arm jarvis loop when /jarvis_agent is used."""

from __future__ import annotations

import contextlib
import json
import sys
from pathlib import Path


def _workspace_root(payload: dict) -> Path:
    roots = payload.get("workspace_roots") or payload.get("workspaceRoots")
    if isinstance(roots, list) and roots:
        return Path(str(roots[0]))
    return Path.cwd()


def _is_jarvis_prompt(prompt: str) -> bool:
    stripped = prompt.lstrip()
    if not stripped.startswith("/"):
        return False
    head = stripped.split(maxsplit=1)[0]
    return head == "/jarvis_agent"


def _set_jarvis_loop(root: Path, enabled: bool) -> None:
    flag = root / ".cache" / "jarvis" / "loop.enabled"
    if enabled:
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.touch()
        return
    with contextlib.suppress(FileNotFoundError):
        flag.unlink()


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        payload = {}

    prompt = payload.get("prompt", "")
    if not isinstance(prompt, str):
        prompt = ""

    _set_jarvis_loop(_workspace_root(payload), _is_jarvis_prompt(prompt))

    sys.stdout.write(json.dumps({"continue": True}) + "\n")


if __name__ == "__main__":
    main()
