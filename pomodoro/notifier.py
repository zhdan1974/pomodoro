import subprocess
import threading
from pomodoro.timer import Phase

_MESSAGES = {
    Phase.SHORT_BREAK: ("番茄钟", "专注结束，该休息了！"),
    Phase.LONG_BREAK:  ("番茄钟", "专注结束，好好休息一下！"),
    Phase.WORK:        ("番茄钟", "休息结束，继续加油！"),
}


def notify(phase: Phase):
    title, message = _MESSAGES.get(phase, ("番茄钟", ""))
    if not message:
        return
    threading.Thread(target=_send, args=(title, message), daemon=True).start()


def _send(title: str, message: str):
    script = f'display notification "{message}" with title "{title}" sound name "Glass"'
    try:
        subprocess.run(["osascript", "-e", script], check=True, timeout=5)
    except Exception:
        _fallback_sound()


def _fallback_sound():
    try:
        subprocess.run(
            ["afplay", "/System/Library/Sounds/Glass.aiff"],
            check=True,
            timeout=5,
        )
    except Exception:
        pass
