import platform
import subprocess

from models import CheckResult


def notify_desktop(title: str, message: str):
    """Send a desktop notification (best-effort, cross-platform)."""
    system = platform.system()
    try:
        if system == "Darwin":
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], check=False, timeout=5)
        elif system == "Linux":
            subprocess.run(["notify-send", "--urgency=critical", title, message],
                           check=False, timeout=5)
        elif system == "Windows":
            from plyer import notification  # type: ignore
            notification.notify(title=title, message=message, timeout=10)
    except Exception:
        pass  # Notifications are a bonus; don't crash the app


def play_alert():
    """Play a short alert sound (best-effort)."""
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"],
                           check=False, timeout=5)
        elif system == "Linux":
            # Try paplay, then aplay, then bell
            for cmd in (["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                        ["aplay", "-q", "/usr/share/sounds/alsa/Front_Left.wav"]):
                if subprocess.run(cmd, check=False, timeout=5).returncode == 0:
                    break
        elif system == "Windows":
            import winsound  # type: ignore
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        pass


def notify_available(product_name: str, result: CheckResult):
    price_str = f" — ${result.price:.2f}" if result.price else ""
    title = f"AVAILABLE: {product_name}"
    body = f"{result.site}{price_str}\n{result.message}"
    notify_desktop(title, body)
    play_alert()
