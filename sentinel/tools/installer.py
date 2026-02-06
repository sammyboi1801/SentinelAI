import subprocess
import re
import shutil


def is_winget_available():
    return shutil.which("winget") is not None


def winget_search(name):
    """
    Safely finds the best Winget Package ID using Regex.
    """
    try:
        result = subprocess.run(
            ["winget", "search", name],
            capture_output=True,
            text=True,
            encoding='utf-8',  # Force UTF-8 for special chars
            errors='ignore'
        )

        if result.returncode != 0:
            return None

        lines = result.stdout.splitlines()

        for line in lines:
            if "--------" in line or "Name" in line:
                continue

            match = re.search(r'\s{2,}([^\s]+)\s{2,}', line)
            if match:
                return match.group(1)

    except Exception as e:
        print(f"Search Error: {e}")
        pass

    return None


def install_software(package_names):
    """
    Generates a SAFE list of install commands.
    """
    if not is_winget_available():
        return "Error: Winget is not installed on this system."

    # Map of common aliases to Official IDs
    WINGET_MAP = {
        # --- BROWSERS ---
        "chrome": "Google.Chrome",
        "firefox": "Mozilla.Firefox",
        "brave": "Brave.Brave",
        "edge": "Microsoft.Edge",
        "opera": "Opera.Opera",
        "arc": "TheBrowserCompany.Arc",

        # --- DEVELOPMENT & EDITORS ---
        "vscode": "Microsoft.VisualStudioCode",
        "visualstudio": "Microsoft.VisualStudio.2022.Community",
        "cursor": "Anysphere.Cursor",
        "pycharm": "JetBrains.PyCharm.Community",
        "intellij": "JetBrains.IntelliJIDEA.Community",
        "androidstudio": "Google.AndroidStudio",
        "sublime": "SublimeHQ.SublimeText.4",
        "notepad++": "Notepad++.Notepad++",
        "vim": "vim.vim",

        # --- LANGUAGES & RUNTIMES ---
        "git": "Git.Git",
        "github": "GitHub.GitHubDesktop",
        "python": "Python.Python.3.11",
        "python3": "Python.Python.3.12",
        "node": "OpenJS.NodeJS.LTS",
        "deno": "DenoLand.Deno",
        "go": "GoLang.Go",
        "rust": "Rustlang.Rustup",
        "java": "Oracle.JDK.21",
        "jdk": "Oracle.JDK.21",
        "miniconda": "Anaconda.Miniconda3",

        # --- UTILITIES & TERMINAL ---
        "docker": "Docker.DockerDesktop",
        "terminal": "Microsoft.WindowsTerminal",
        "powershell": "Microsoft.PowerShell",
        "powertoys": "Microsoft.PowerToys",
        "7zip": "7zip.7zip",
        "winrar": "RARLab.WinRAR",
        "putty": "PuTTY.PuTTY",
        "wireshark": "WiresharkFoundation.Wireshark",
        "virtualbox": "Oracle.VirtualBox",
        "vmware": "VMware.WorkstationPlayer",

        # --- API & DB TOOLS ---
        "postman": "Postman.Postman",
        "insomnia": "Kong.Insomnia",
        "dbeaver": "DBeaver.DBeaver",
        "mongodb": "MongoDB.Compass.Full",

        # --- COMMUNICATION ---
        "discord": "Discord.Discord",
        "slack": "SlackTechnologies.Slack",
        "zoom": "Zoom.Zoom",
        "teams": "Microsoft.Teams",
        "whatsapp": "WhatsApp.WhatsApp",
        "telegram": "Telegram.TelegramDesktop",
        "signal": "Signal.Signal",

        # --- MEDIA & CREATIVE ---
        "spotify": "Spotify.Spotify",
        "vlc": "VideoLAN.VLC",
        "obs": "OBSProject.OBSStudio",
        "blender": "BlenderFoundation.Blender",
        "gimp": "GIMP.GIMP",
        "inkscape": "Inkscape.Inkscape",
        "audacity": "Audacity.Audacity",
        "ffmpeg": "Gyan.FFmpeg",
        "handbrake": "HandBrake.HandBrake",
        "paint.net": "dotPDN.PaintDotNet",

        # --- PRODUCTIVITY ---
        "notion": "Notion.Notion",
        "obsidian": "Obsidian.Obsidian",
        "evernote": "Evernote.Evernote",
        "adobe reader": "Adobe.Acrobat.Reader.64-bit",
        "libreoffice": "LibreOffice.LibreOffice",

        # --- GAMING ---
        "steam": "Valve.Steam",
        "epic": "EpicGames.EpicGamesLauncher",
        "nvidia": "Nvidia.GeForceExperience"
    }

    commands = []

    for pkg in package_names:
        pkg_lower = pkg.lower().strip()

        target_id = WINGET_MAP.get(pkg_lower)

        if not target_id:
            print(f"🔍 Searching winget for '{pkg}'...")
            target_id = winget_search(pkg)

        if not target_id:
            print(f"⚠️  Could not find package ID for '{pkg}'. Skipping.")
            continue

        cmd = (
            f"winget install --id {target_id} "
            f"--exact --silent --accept-source-agreements --accept-package-agreements"
        )
        commands.append(cmd)

    if not commands:
        return "No valid packages found to install."

    return " && ".join(commands)


def list_installed():
    """Returns a clean list of installed apps."""
    try:
        result = subprocess.run(
            ["winget", "list"],
            capture_output=True, text=True, encoding='utf-8', errors='ignore'
        )
        return result.stdout[:2000] + "\n... (truncated)"
    except FileNotFoundError:
        return "Error: Winget not found."