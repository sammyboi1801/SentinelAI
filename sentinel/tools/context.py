import time
import psutil
import platform
import threading
import pygetwindow as gw

try:
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
except ImportError:
    user32 = None

from sentinel.tools import memory_ops

_WATCHER_RUNNING = False


def get_active_app():
    """
    Returns rich context: {pid, app_name, title, url(maybe)}
    """
    if platform.system() != "Windows":
        return {"app_name": "Non-Windows", "title": "Not supported yet"}

    try:
        hwnd = user32.GetForegroundWindow()

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

        process = psutil.Process(pid.value)
        app_name = process.name()

        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value

        return {
            "app_name": app_name,
            "title": title,
            "pid": pid.value,
            "status": "Active"
        }

    except Exception:
        return {"app_name": "Unknown", "title": "Unknown", "status": "Error"}


def watch_app_switch(interval=5):
    """
    Monitors for app switches (For the 'digital twin' log).
    Runs as a background thread so it doesn't block.
    """
    global _WATCHER_RUNNING
    if _WATCHER_RUNNING:
        return "Watcher already running."

    _WATCHER_RUNNING = True

    def _watch_loop():
        last_app = ""
        last_title = ""

        while _WATCHER_RUNNING:
            info = get_active_app()
            current_app = info.get("app_name", "")
            current_title = info.get("title", "")

            if current_app != last_app or (current_app == last_app and current_title != last_title):
                if current_app not in ["Unknown", "explorer.exe", "SearchHost.exe"]:
                    log_msg = f"Switched to {current_app} | {current_title}"
                    print(f"👁️ [Context]: {log_msg}")

                    memory_ops.log_activity("focus_change", log_msg)

                last_app = current_app
                last_title = current_title

            time.sleep(interval)

    thread = threading.Thread(target=_watch_loop, daemon=True)
    thread.start()
    return "✅ Context Watcher started in background."