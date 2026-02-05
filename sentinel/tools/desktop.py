import pyautogui
import pygetwindow as gw
import screen_brightness_control as sbc
import platform
import pyttsx3

# Fail-safe
pyautogui.FAILSAFE = True

_ENGINE = None


def _safe_str(x):
    """Force any output to be a string (prevents Anthropic crashes)."""
    try:
        return str(x)
    except:
        return "Unknown result"


def set_volume(level):
    system = platform.system()

    try:
        target = int(level)

        # Mute first to calibrate
        pyautogui.press('volumedown', presses=50)

        clicks = int(target / 2)
        if clicks > 0:
            pyautogui.press('volumeup', presses=clicks)

        return _safe_str(f"Volume adjusted to approx {target}% (OS: {system}).")

    except Exception as e:
        return _safe_str(f"Volume control failed: {e}")


def set_brightness(level):
    try:
        sbc.set_brightness(int(level))
        return _safe_str(f"Brightness set to {level}%.")
    except Exception as e:
        return _safe_str(f"Error setting brightness: {e}")


def _find_window_fuzzy(name):
    """Find first window containing name (case-insensitive)."""
    name = name.lower()
    for w in gw.getAllWindows():
        if name in w.title.lower():
            return w
    return None


def minimize_window(app_name=None):
    try:
        if not app_name:
            win = gw.getActiveWindow()
        else:
            win = _find_window_fuzzy(app_name)

        if not win:
            return _safe_str(f"No window found for '{app_name}'.")

        win.minimize()
        return _safe_str(f"Minimized: {win.title}")

    except Exception as e:
        return _safe_str(f"Minimize error: {e}")


def maximize_window(app_name=None):
    try:
        if not app_name:
            win = gw.getActiveWindow()
        else:
            win = _find_window_fuzzy(app_name)

        if not win:
            return _safe_str(f"No window found for '{app_name}'.")

        win.maximize()
        return _safe_str(f"Maximized: {win.title}")

    except Exception as e:
        return _safe_str(f"Maximize error: {e}")


def type_text(text):
    try:
        pyautogui.write(str(text), interval=0.001)
        return _safe_str("Typed text successfully.")
    except Exception as e:
        return _safe_str(f"Typing error: {e}")


def take_screenshot(filename="screenshot.png"):
    try:
        pyautogui.screenshot(filename)
        return _safe_str(f"Screenshot saved to {filename}")
    except Exception as e:
        return _safe_str(f"Screenshot failed: {e}")


def speak(text):
    global _ENGINE
    try:
        if _ENGINE is None:
            _ENGINE = pyttsx3.init()
        _ENGINE.say(str(text))
        _ENGINE.runAndWait()
        return _safe_str("Spoken.")
    except Exception as e:
        return _safe_str(f"TTS Error: {e}")
