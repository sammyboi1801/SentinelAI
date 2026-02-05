import pygetwindow as gw
import platform
import psutil
import time


def get_active_app():
    """
    Returns the title and process name of the currently focused window.
    """
    try:
        if platform.system() == "Windows":
            window = gw.getActiveWindow()
            if not window:
                return "No active window detected."

            return {
                "title": window.title,
                "app_name": "Unknown (Window API limitation)",
                "status": "Active"
            }
        else:
            return "Active app detection is currently Windows-optimized."

    except Exception as e:
        return f"Context Error: {e}"


def watch_app_switch(interval=5):
    """
    Monitors for app switches (For the 'digital twin' log).
    """
    last_window = ""
    while True:
        curr = get_active_app()
        if isinstance(curr, dict) and curr['title'] != last_window:
            print(f"[Context] User switched to: {curr['title']}")
            last_window = curr['title']
        time.sleep(interval)