import pyautogui
import pygetwindow as gw
import screen_brightness_control as sbc
import platform
import pyttsx3
import base64
import os
import subprocess
import sys

pyautogui.FAILSAFE = True

# Global handle for the current speech process
_CURRENT_SPEECH_PROCESS = None

def _safe_str(x):
    try:
        return str(x)
    except:
        return "Unknown result"


def set_volume(level):
    """
    Sets volume by zeroing it out and stepping up.
    """
    try:
        target = int(level)

        pyautogui.press('volumedown', presses=50)

        clicks = int(target / 2)
        if clicks > 0:
            pyautogui.press('volumeup', presses=clicks)

        return f"🔊 Volume adjusted to ~{target}%."
    except Exception as e:
        return f"❌ Volume error: {e}"


def media_control(action):
    """
    Controls media playback.
    Actions: playpause, next, prev, mute
    """
    valid = ["playpause", "nexttrack", "prevtrack", "volumemute"]

    # Map friendly names to keys
    key_map = {
        "play": "playpause",
        "pause": "playpause",
        "next": "nexttrack",
        "skip": "nexttrack",
        "previous": "prevtrack",
        "back": "prevtrack",
        "mute": "volumemute",
        "unmute": "volumemute"
    }

    key = key_map.get(action.lower(), action.lower())

    if key not in valid:
        return f"❌ Unknown media command. Try: play, pause, next, mute."

    try:
        pyautogui.press(key)
        return f"⏯️ Sent media command: {key}"
    except Exception as e:
        return f"❌ Media error: {e}"


def set_brightness(level):
    try:
        sbc.set_brightness(int(level))
        return f"🔆 Brightness set to {level}%."
    except Exception as e:
        return f"❌ Brightness error: {e}"


def _find_window_fuzzy(name):
    name = name.lower()
    # filtering for visible windows helps avoid hidden background processes
    wins = [w for w in gw.getAllWindows() if w.title]

    for w in wins:
        if name in w.title.lower():
            return w
    return None


def focus_window(app_name):
    """Brings a window to the front."""
    try:
        win = _find_window_fuzzy(app_name)
        if not win: return f"❌ '{app_name}' not found."

        if win.isMinimized:
            win.restore()

        win.activate()
        return f"📂 Switched to: {win.title}"
    except Exception as e:
        return f"❌ Focus error: {e}"


def close_window(app_name):
    """Closes a window. Dangerous!"""
    try:
        win = _find_window_fuzzy(app_name)
        if not win: return f"❌ '{app_name}' not found."

        win.close()
        return f"🗑️ Closed: {win.title}"
    except Exception as e:
        return f"❌ Close error: {e}"


def minimize_window(app_name=None):
    try:
        win = _find_window_fuzzy(app_name) if app_name else gw.getActiveWindow()
        if not win: return "❌ No window found."

        win.minimize()
        return f"Actions: Minimized {win.title}"
    except Exception as e:
        return f"Error: {e}"

def maximize_window(app_name=None):
    try:
        win = _find_window_fuzzy(app_name) if app_name else gw.getActiveWindow()
        if not win: return "❌ No window found."

        win.maximize()
        return f"Actions: Maximized {win.title}"
    except Exception as e:
        return f"Error: {e}"


def type_text(text):
    """Types text at a realistic speed."""
    try:
        # interval=0.005 is safer than 0.001 for some apps
        pyautogui.write(str(text), interval=0.005)
        return "⌨️ Typed text."
    except Exception as e:
        return f"❌ Typing error: {e}"


def press_hotkey(keys):
    """
    Presses a combination of keys.
    Example: "ctrl+s", "alt+f4", "command+c"
    """
    try:
        combo = keys.lower().split('+')
        pyautogui.hotkey(*combo)
        return f"⌨️ Pressed: {keys}"
    except Exception as e:
        return f"❌ Hotkey error: {e}"


def scroll(amount, direction="down"):
    """Scrolls the screen."""
    try:
        clicks = int(amount)
        if direction == "down":
            clicks = -clicks

        pyautogui.scroll(clicks)
        return f"📜 Scrolled {direction} by {amount}."
    except Exception as e:
        return f"❌ Scroll error: {e}"


def take_screenshot(filename="screenshot.png"):
    try:
        pyautogui.screenshot(filename)
        return f"📸 Screenshot saved to {filename}"
    except Exception as e:
        return f"❌ Screenshot failed: {e}"


def speak(text):
    """
    Non-Blocking, Process-Based Speech.
    Spawns a separate Python process to handle the audio.
    """
    global _CURRENT_SPEECH_PROCESS

    if _CURRENT_SPEECH_PROCESS and _CURRENT_SPEECH_PROCESS.poll() is None:
        try:
            _CURRENT_SPEECH_PROCESS.terminate()
            _CURRENT_SPEECH_PROCESS.wait(timeout=0.5)
        except Exception:
            pass

    try:
        b64_text = base64.b64encode(str(text).encode("utf-8")).decode("utf-8")
    except Exception as e:
        return f"❌ Text encoding error: {e}"

    script = (
        "import sys, pyttsx3, base64; "
        "text = base64.b64decode(sys.argv[1]).decode('utf-8'); "
        "engine = pyttsx3.init(); "
        "engine.say(text); "
        "engine.runAndWait()"
    )

    cmd = [sys.executable, "-c", script, b64_text]

    try:
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        _CURRENT_SPEECH_PROCESS = subprocess.Popen(
            cmd,
            startupinfo=startupinfo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return f"🗣️ Speaking: '{str(text)[:40]}...'"
    except Exception as e:
        return f"❌ Speech system error: {e}"