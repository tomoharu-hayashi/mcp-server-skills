"""macOS ネイティブ通知"""

import shutil
import subprocess
import tempfile
from contextlib import suppress
from pathlib import Path


def _escape_applescript(text: str) -> str:
    """AppleScript文字列のエスケープ（インジェクション対策）"""
    # バックスラッシュとダブルクォートをエスケープ
    return text.replace("\\", "\\\\").replace('"', '\\"')


def play_sosumi() -> None:
    """Sosumi効果音を再生"""
    subprocess.Popen(
        ["afplay", "/System/Library/Sounds/Sosumi.aiff"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def show_create_confirmation(name: str, description: str) -> bool:
    """知識作成の確認ダイアログを表示

    Args:
        name: 作成する知識名
        description: 知識の説明

    Returns:
        True: 作成を承認 / False: キャンセル
    """
    # 効果音
    play_sosumi()

    # AppleScript用にエスケープ（インジェクション対策）
    safe_name = _escape_applescript(name)
    safe_desc = _escape_applescript(description)

    # AppleScript でダイアログ表示
    script = f"""
    display dialog "以下の知識を作成しますか？\\n\\n\
名前: {safe_name}\\n説明: {safe_desc}" ¬
        with title "MCP Brain: 知識の作成確認" ¬
        buttons {{"キャンセル", "作成する"}} default button "作成する" ¬
        with icon note
    """

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return "作成する" in result.stdout
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


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

    # 表示用リスト（エスケープしてインジェクション対策）
    names_display = "\\n".join(
        f"• {_escape_applescript(name)}" for name in stale_names[:10]
    )
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


def show_update_confirmation(name: str, description: str) -> bool:
    """知識更新の確認ダイアログを表示"""
    play_sosumi()
    safe_name = _escape_applescript(name)
    safe_desc = _escape_applescript(description)

    script = f"""
    display dialog "以下の知識を更新しますか？\\n\\n\
名前: {safe_name}\\n説明: {safe_desc}" ¬
        with title "MCP Brain: 知識の更新確認" ¬
        buttons {{"キャンセル", "更新する"}} default button "更新する" ¬
        with icon note
    """

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return "更新する" in result.stdout
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def edit_content_with_textedit(
    name: str, description: str, content: str, timeout: int = 300
) -> str | None:
    """VS Codeで全文を開いて編集してもらう。開けなければNoneを返す。"""
    # 未使用引数だがシグネチャ互換のため保持
    _ = (name, description, timeout)
    # VS Codeが読みやすい場所に一時ファイルを作成（/tmp配下、644権限）
    tmp_dir = Path("/tmp/mcp-brain")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".md", encoding="utf-8", dir=tmp_dir
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    tmp_path.chmod(0o644)

    def _launch_with_code() -> bool:
        """VS Codeで開く。code --waitがあれば同期、なければopen -aで非同期。"""
        if shutil.which("code"):
            try:
                subprocess.run(
                    ["code", "--wait", str(tmp_path)],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            except Exception:
                return False

        with suppress(Exception):
            subprocess.Popen(["open", "-a", "Visual Studio Code", str(tmp_path)])
            return True
        return False

    # VS Codeのみで開く（TextEditフォールバックはなし）
    if _launch_with_code():
        edited: str | None = None
        with suppress(Exception), tmp_path.open("r", encoding="utf-8") as f:
            edited = f.read()
        with suppress(OSError):
            tmp_path.unlink()
        return edited

    # VS Codeが起動できなかった場合はNoneを返す
    with suppress(OSError):
        tmp_path.unlink()
    return None
