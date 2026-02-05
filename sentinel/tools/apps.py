import os
from sentinel.tools.smart_index import index_file
import shutil
import platform
import subprocess
import webbrowser
import difflib
import logging

APP_CACHE = globals().get("APP_CACHE", {})

def _native_open(target):
    """
    Cross-platform helper to open a file, folder, or URI using the OS default handler.
    """
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(target)
        elif system == "Darwin":  # macOS
            subprocess.Popen(["open", target])
        else:  # Linux / Unix
            subprocess.Popen(["xdg-open", target])
        return True
    except Exception as e:
        logging.error(f"Native open failed for {target}: {e}")
        return False


def _run_command(cmd_str):
    """
    Safely runs a command string cross-platform.
    """
    try:
        subprocess.Popen(cmd_str, shell=True)
        return True
    except Exception as e:
        logging.error(f"Command failed {cmd_str}: {e}")
        return False


def _get_os_aliases():
    """
    Returns a dictionary of app aliases specific to the current operating system.
    """
    system = platform.system()

    # 1. Common Aliases (Work if binary is in PATH)
    aliases = {
        "code": "code",
        "python": "python",
        "git": "git",
        "firefox": "firefox",
        "vlc": "vlc",
        "discord": "discord",
        "spotify": "spotify",
    }

    # 2. Windows Specifics
    if system == "Windows":
        return {**aliases, **{
            # --- BROWSERS ---
            "chrome": "chrome",
            "google chrome": "chrome",
            "firefox": "firefox",
            "edge": "msedge",
            "microsoft edge": "msedge",
            "brave": "brave",
            "opera": "opera",

            # --- MICROSOFT OFFICE ---
            "word": "winword",
            "excel": "excel",
            "powerpoint": "powerpnt",
            "ppt": "powerpnt",
            "outlook": "outlook",
            "onenote": "onenote",
            "teams": "ms-teams:",
            "access": "msaccess",

            # --- SYSTEM TOOLS ---
            "explorer": "explorer",
            "file explorer": "explorer",
            "settings": "start ms-settings:",
            "control panel": "control",
            "task manager": "taskmgr",
            "cmd": "start cmd",  #
            "command prompt": "start cmd",
            "terminal": "wt",  # Windows Terminal
            "powershell": "start powershell",
            "system info": "msinfo32",
            "registry": "regedit",
            "services": "services.msc",

            # --- DIRECTORY SHORTCUTS ---
            "downloads": "explorer shell:downloads",
            "documents": "explorer shell:personal",
            "desktop": "explorer shell:desktop",
            "pictures": "explorer shell:my pictures",
            "startup": "explorer shell:startup",

            # --- DEV TOOLS ---
            "code": "code",
            "vscode": "code",
            "visual studio": "devenv",
            "pycharm": "pycharm64",
            "intellij": "idea64",
            "docker": "start \"Docker Desktop\" \"C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe\"",
            "wsl": "wsl",
            "git": "git-bash",

            # --- MEDIA & UTILITIES ---
            "spotify": "spotify",
            "vlc": "vlc",
            "notepad": "notepad",
            "paint": "mspaint",
            "calc": "calc",
            "calculator": "calc",
            "snipping tool": "snippingtool",
            "screenshot": "snippingtool",
            "photos": "ms-photos:",
            "camera": "microsoft.windows.camera:",
            "clock": "ms-clock:",
            "alarms": "ms-clock:",
            "weather": "ms-weather:",
            "maps": "bingmaps:",

            # --- COMMUNICATION ---
            "discord": "discord",
            "slack": "slack",
            "whatsapp": "start whatsapp:",
            "zoom": "zoom",
            "telegram": "telegram",

            # --- STORE & UWP ---
            "store": "ms-windows-store:",
            "mail": "outlookmail:",
            "calendar": "outlookcal:",
            "xbox": "xbox:",
        }}

    # 3. macOS Specifics (Darwin)
    elif system == "Darwin":
        return {**aliases, **{
            # --- BROWSERS ---
            "chrome": "open -a 'Google Chrome'",
            "google chrome": "open -a 'Google Chrome'",
            "firefox": "open -a Firefox",
            "safari": "open -a Safari",
            "edge": "open -a 'Microsoft Edge'",
            "brave": "open -a 'Brave Browser'",
            "opera": "open -a Opera",
            "arc": "open -a Arc",

            # --- MICROSOFT OFFICE ---
            "word": "open -a 'Microsoft Word'",
            "excel": "open -a 'Microsoft Excel'",
            "powerpoint": "open -a 'Microsoft PowerPoint'",
            "onenote": "open -a 'Microsoft OneNote'",
            "outlook": "open -a 'Microsoft Outlook'",
            "teams": "open -a 'Microsoft Teams'",

            # --- DEV TOOLS ---
            "vscode": "open -a 'Visual Studio Code'",
            "code": "open -a 'Visual Studio Code'",
            "sublime": "open -a 'Sublime Text'",
            "iterm": "open -a iTerm",
            "terminal": "open -a Terminal",
            "docker": "open -a Docker",
            "pycharm": "open -a 'PyCharm CE'",
            "intellij": "open -a 'IntelliJ IDEA CE'",
            "xcode": "open -a Xcode",

            # --- COMMUNICATION ---
            "slack": "open -a Slack",
            "discord": "open -a Discord",
            "whatsapp": "open -a WhatsApp",
            "telegram": "open -a Telegram",
            "signal": "open -a Signal",
            "zoom": "open -a zoom.us",
            "messages": "open -a Messages",
            "imessage": "open -a Messages",
            "mail": "open -a Mail",

            # --- CREATIVE & MEDIA ---
            "spotify": "open -a Spotify",
            "vlc": "open -a VLC",
            "quicktime": "open -a 'QuickTime Player'",
            "preview": "open -a Preview",
            "photos": "open -a Photos",
            "photoshop": "open -a 'Adobe Photoshop'",
            "premiere": "open -a 'Adobe Premiere Pro'",

            # --- PRODUCTIVITY ---
            "notion": "open -a Notion",
            "obsidian": "open -a Obsidian",
            "evernote": "open -a Evernote",
            "notes": "open -a Notes",
            "reminders": "open -a Reminders",
            "calendar": "open -a Calendar",
            "contacts": "open -a Contacts",
            "maps": "open -a Maps",

            # --- SYSTEM UTILITIES ---
            "finder": "open .",
            "explorer": "open .",
            "settings": "open -b com.apple.systempreferences",
            "preferences": "open -b com.apple.systempreferences",
            "app store": "open -a 'App Store'",
            "activity monitor": "open -a 'Activity Monitor'",
            "task manager": "open -a 'Activity Monitor'",
            "disk utility": "open -a 'Disk Utility'",
            "calculator": "open -a Calculator",
            "calc": "open -a Calculator",
            "screenshot": "open -a Screenshot",
            "textedit": "open -a TextEdit",
            "facetime": "open -a FaceTime",
        }}

    # 4. Linux Specifics
    else:
        return {**aliases, **{
            # --- BROWSERS ---
            "chrome": "google-chrome",
            "chromium": "chromium-browser",
            "firefox": "firefox",
            "brave": "brave-browser",
            "edge": "microsoft-edge",
            "opera": "opera",

            # --- OFFICE (LibreOffice Suite) ---
            "word": "libreoffice --writer",
            "writer": "libreoffice --writer",
            "excel": "libreoffice --calc",
            "calc": "libreoffice --calc",
            "powerpoint": "libreoffice --impress",
            "impress": "libreoffice --impress",
            "teams": "teams-for-linux",

            # --- DEV TOOLS ---
            "vscode": "code",
            "code": "code",
            "sublime": "subl",
            "vim": "vim",
            "nano": "nano",
            "docker": "docker",
            "terminal": "gnome-terminal",
            "konsole": "konsole",

            # --- COMMUNICATION ---
            "discord": "discord",
            "slack": "slack",
            "telegram": "telegram-desktop",
            "signal": "signal-desktop",
            "zoom": "zoom",
            "skype": "skypeforlinux",

            # --- MEDIA ---
            "vlc": "vlc",
            "spotify": "spotify",
            "rhythmbox": "rhythmbox",
            "mpv": "mpv",
            "photos": "eog",
            "gimp": "gimp",
            "obs": "obs",

            # --- SYSTEM UTILITIES ---
            "explorer": "xdg-open .",
            "finder": "xdg-open .",
            "nautilus": "nautilus",
            "dolphin": "dolphin",
            "thunar": "thunar",


            "settings": "gnome-control-center",
            "control panel": "gnome-control-center",

            # Task Manager equivalents
            "task manager": "gnome-system-monitor",
            "system monitor": "gnome-system-monitor",
            "htop": "x-terminal-emulator -e htop",

            "calculator": "gnome-calculator",
            "screenshot": "gnome-screenshot",
            "textedit": "gedit",
            "gedit": "gedit",
        }}

def refresh_app_cache():
    """
    Cross-platform indexer.
    Scans system directories to build a map of {app_name: path}.
    """
    global APP_CACHE
    APP_CACHE = {}
    system = platform.system()

    # --- WINDOWS INDEXING ---
    if system == "Windows":
        paths = [
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs")
        ]
        for path in paths:
            if not os.path.exists(path): continue
            for root, _, files in os.walk(path):
                for file in files:
                    if file.lower().endswith(".lnk"):
                        name = file.lower().replace(".lnk", "")
                        APP_CACHE[name] = os.path.join(root, file)

    # --- MACOS INDEXING ---
    elif system == "Darwin":
        # Scan standard application folders
        app_dirs = ["/Applications", "/System/Applications", os.path.expanduser("~/Applications")]
        for app_dir in app_dirs:
            if not os.path.exists(app_dir): continue
            try:
                for item in os.listdir(app_dir):
                    if item.endswith(".app"):
                        name = item.replace(".app", "").lower()
                        full_path = os.path.join(app_dir, item)
                        APP_CACHE[name] = full_path
            except PermissionError:
                continue

    # --- LINUX INDEXING ---
    elif system == "Linux":
        desktop_dirs = ["/usr/share/applications", os.path.expanduser("~/.local/share/applications")]
        for d_dir in desktop_dirs:
            if not os.path.exists(d_dir): continue
            try:
                for item in os.listdir(d_dir):
                    if item.endswith(".desktop"):
                        name = item.replace(".desktop", "").lower()
                        full_path = os.path.join(d_dir, item)
                        APP_CACHE[name] = full_path
            except PermissionError:
                continue


refresh_app_cache()


def list_all_apps():
    """Returns a list of all indexed applications."""
    if not APP_CACHE:
        return "No apps found in index. (Is this Windows?)"

    # Sort alphabetically
    sorted_apps = sorted(APP_CACHE.keys())
    return "Indexed Apps:\n" + "\n".join([f"- {app}" for app in sorted_apps])


def open_app(name):
    """
    Smart Launcher (Cross-Platform).
    Priority:
    1. Direct Path (Absolute paths)
    2. System Aliases (OS-specific shortcuts)
    3. Dynamic App Cache (Fuzzy Match)
    4. Web URL fallback
    """
    name = name.strip()
    lower_name = name.lower()

    # --- 1. DIRECT PATH ---
    if os.path.exists(name):
        if 'index_file' in globals(): globals()['index_file'](name)

        if _native_open(name):
            return f"Launched file: {name}"

    # --- 2. SYSTEM ALIASES ---
    aliases = _get_os_aliases()

    if lower_name in aliases:
        cmd = aliases[lower_name]
        if _run_command(cmd):
            return f"Launched system tool: {lower_name}"
        return f"Failed to launch alias: {lower_name}"

    # --- 3. DYNAMIC SEARCH (Fuzzy Match) ---
    if APP_CACHE:
        # Exact Match
        if lower_name in APP_CACHE:
            path = APP_CACHE[lower_name]
            _native_open(path)
            return f"Launched {lower_name} from Index."

        # Fuzzy Match
        matches = difflib.get_close_matches(lower_name, APP_CACHE.keys(), n=1, cutoff=0.6)
        if matches:
            best_match = matches[0]
            path = APP_CACHE[best_match]
            _native_open(path)
            return f"Launched {best_match} (matched to '{name}')"

    # --- 4. EXECUTABLE IN PATH ---
    if shutil.which(lower_name):
        _run_command(lower_name)
        return f"Executed command: {lower_name}"

    # --- 5. WEB URL FALLBACK ---
    if "." in name and " " not in name:
        url = name if name.startswith(("http://", "https://")) else f"https://{name}"
        webbrowser.open(url)
        return f"Opened website: {url}"

    return f"Could not find app, file, or command: '{name}'"

def play_music(song_name):
    """Plays music on YouTube Music."""
    query = song_name.replace(" ", "+")
    webbrowser.open(f"https://music.youtube.com/search?q={query}")
    return f"Playing {song_name}..."

def close_app(name):
    """
    Attempts to close a running application by name.
    Uses graceful terminate first, then force kill if needed.
    """
    name = name.lower().strip()

    system = platform.system()

    try:
        if system == "Windows":
            # Try graceful close first
            subprocess.call(f"taskkill /IM {name}.exe", shell=True)
            return f"Closed application: {name}"

        elif system == "Darwin":  # macOS
            subprocess.call(["pkill", "-f", name])
            return f"Closed application: {name}"

        elif system == "Linux":
            subprocess.call(["pkill", "-f", name])
            return f"Closed application: {name}"

        else:
            return "Unsupported OS."

    except Exception as e:
        return f"Failed to close app '{name}': {e}"