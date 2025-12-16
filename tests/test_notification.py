import subprocess
from types import SimpleNamespace

import mcp_brain.notification as notification


def test_escape_applescript_escapes_backslash_and_quotes() -> None:
    assert notification._escape_applescript('a"b\\c') == 'a\\"b\\\\c'


def test_play_sosumi_invokes_afplay(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_popen(args: list[str], **_kwargs: object) -> None:
        calls.append(args)

    monkeypatch.setattr(notification.subprocess, "Popen", fake_popen)
    notification.play_sosumi()

    assert calls == [["afplay", "/System/Library/Sounds/Sosumi.aiff"]]


def test_show_create_confirmation_true_when_button_selected(monkeypatch) -> None:
    monkeypatch.setattr(notification, "play_sosumi", lambda: None)

    def fake_run(*_args: object, **_kwargs: object) -> object:
        return SimpleNamespace(stdout="作成する")

    monkeypatch.setattr(notification.subprocess, "run", fake_run)
    assert notification.show_create_confirmation("n", "d") is True


def test_show_create_confirmation_false_on_timeout(monkeypatch) -> None:
    monkeypatch.setattr(notification, "play_sosumi", lambda: None)

    def fake_run(*_args: object, **_kwargs: object) -> object:
        raise subprocess.TimeoutExpired(cmd=["osascript"], timeout=60)

    monkeypatch.setattr(notification.subprocess, "run", fake_run)
    assert notification.show_create_confirmation("n", "d") is False


def test_show_stale_dialog_returns_false_for_empty_list() -> None:
    assert notification.show_stale_dialog([]) is False


def test_show_stale_dialog_true_when_delete_selected(monkeypatch) -> None:
    monkeypatch.setattr(notification, "play_sosumi", lambda: None)

    def fake_run(*_args: object, **_kwargs: object) -> object:
        return SimpleNamespace(stdout="削除する")

    monkeypatch.setattr(notification.subprocess, "run", fake_run)
    assert notification.show_stale_dialog(["a", "b"]) is True
