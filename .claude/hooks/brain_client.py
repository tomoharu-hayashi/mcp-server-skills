#!/usr/bin/env python3
"""Brain MCP クライアント"""

import json
import os
import subprocess
from pathlib import Path


def call_brain(method: str, params: dict, timeout: int = 10) -> dict | None:
    """Brain MCPサーバーを呼び出す"""
    server_path = os.environ.get(
        "MCP_BRAIN_PATH", str(Path("~/pj/my/mcp-server-brain").expanduser())
    )

    requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "claude-hook", "version": "1.0"},
            },
        },
        {"jsonrpc": "2.0", "method": "initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": method, "params": params},
    ]

    result = subprocess.run(
        ["uv", "run", "mcp-brain"],
        input="\n".join(json.dumps(req) for req in requests),
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=server_path,
    )

    if result.returncode != 0:
        return None

    for line in reversed(result.stdout.strip().split("\n")):
        if line.startswith("{") and "result" in line:
            return json.loads(line).get("result")
    return None


def search_and_get(query: str, project: str = "global") -> str:
    """Brain MCPから関連知識を検索して取得"""
    if not query:
        return ""

    search_result = call_brain(
        "tools/call",
        {"name": "search", "arguments": {"query": query[:200], "project": project}},
    )

    if not search_result:
        return ""

    items = search_result.get("structuredContent", {}).get("result", [])
    if not items:
        return ""

    name = items[0].get("name", "")
    if not name:
        return ""

    get_result = call_brain(
        "tools/call", {"name": "get", "arguments": {"name": name, "hops": 2}}
    )

    if not get_result:
        return ""

    content_array = get_result.get("content", [])
    if not content_array:
        return ""

    text_content = content_array[0].get("text", "")
    if not text_content:
        return ""

    try:
        return json.loads(text_content).get("content", "")
    except (json.JSONDecodeError, KeyError):
        return ""
