"""macOS ネイティブ通知"""

import subprocess


def play_sosumi() -> None:
    """Sosumi効果音を再生"""
    subprocess.Popen(
        ["afplay", "/System/Library/Sounds/Sosumi.aiff"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def show_stale_dialog(stale_names: list[str]) -> bool:
    """古い知識の警告ダイアログを表示

    Args:
        stale_names: 古い知識名のリスト

    Returns:
        True: 削除を選択 / False: 後で
    """
    if not stale_names:
        return False

    # 効果音
    play_sosumi()

    # 表示用リスト
    names_display = "\\n".join(f"• {name}" for name in stale_names[:10])
    if len(stale_names) > 10:
        names_display += f"\\n...他 {len(stale_names) - 10} 件"

    # AppleScript でダイアログ表示
    count = len(stale_names)
    msg = f"30日以上使用されていない知識が {count} 件あります:"
    script = f'''
    display dialog "{msg}\\n\\n{names_display}" ¬
        with title "MCP Brain: 古い知識の通知" ¬
        buttons {{"後で", "削除する"}} default button "後で" ¬
        with icon caution
    '''

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return "削除する" in result.stdout
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False
