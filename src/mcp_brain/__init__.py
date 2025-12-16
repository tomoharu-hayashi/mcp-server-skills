"""MCP Brain Server - AIエージェントに統合的な知識を提供"""

from __future__ import annotations

import sys
from pathlib import Path

__version__ = "0.1.0"


def _configure_pycache_prefix() -> bool:
    prefix = Path.home() / ".cache" / "mcp-brain" / "pycache"
    try:
        prefix.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False
    sys.pycache_prefix = str(prefix)
    return True


_configure_pycache_prefix()
