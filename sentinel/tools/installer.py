import subprocess
import json


def winget_search(name):
    """Find best Winget package ID for a given name."""
    try:
        output = subprocess.check_output(
            f'winget search "{name}" --output json',
            shell=True
        ).decode()

        data = json.loads(output)

        if "Data" in data and len(data["Data"]) > 0:
            return data["Data"][0]["PackageIdentifier"]

    except:
        pass

    return None


def install_software(package_names):
    """
    Returns safe winget install commands.
    The agent should pass this to run_cmd.
    """

    WINGET_MAP = {
        "vscode": "Microsoft.VisualStudioCode",
        "chrome": "Google.Chrome",
        "discord": "Discord.Discord",
        "git": "Git.Git",
        "python": "Python.Python.3.11",
        "node": "OpenJS.NodeJS",
        "spotify": "Spotify.Spotify",
        "zoom": "Zoom.Zoom",
        "notion": "Notion.Notion",
        "docker": "Docker.DockerDesktop"
    }

    commands = []

    for pkg in package_names:
        pkg_lower = pkg.lower()

        # 1. Try curated aliases
        target = WINGET_MAP.get(pkg_lower)

        # 2. Live winget search
        if not target:
            target = winget_search(pkg)

        # 3. Fallback
        if not target:
            target = pkg

        cmd = f"winget install -e --id {target} --accept-source-agreements --accept-package-agreements"
        commands.append(cmd)

    return " && ".join(commands)


def list_installed():
    try:
        return subprocess.check_output("winget list", shell=True).decode()
    except:
        return "Could not list apps. Ensure Winget is installed."