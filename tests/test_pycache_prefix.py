from __future__ import annotations

import sys
from pathlib import Path

import pytest

import mcp_brain


def test_pycache_prefix_is_redirected_to_user_cache() -> None:
    expected = Path.home() / ".cache" / "mcp-brain" / "pycache"
    assert Path(sys.pycache_prefix or "") == expected


def test_pycache_prefix_config_does_not_crash_on_mkdir_error(monkeypatch: pytest.MonkeyPatch) -> None:
    original = sys.pycache_prefix

    def _raise(*args: object, **kwargs: object) -> None:
        raise OSError("nope")

    monkeypatch.setattr(Path, "mkdir", _raise)
    assert mcp_brain._configure_pycache_prefix() is False
    assert sys.pycache_prefix == original

