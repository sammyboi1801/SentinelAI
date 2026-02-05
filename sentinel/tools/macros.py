import webbrowser
import os
import time
from sentinel.tools import apps, desktop

# Define your personal workflows here
WORKFLOWS = {
    "work": {
        "apps": ["code", "slack"],  # Add your specific app executable names
        "urls": ["https://jira.atlassian.com", "https://github.com"],
        "volume": 20,
        "say": "Work mode activated. Focus."
    },
    "morning": {
        "urls": ["https://news.ycombinator.com", "https://gmail.com", "https://calendar.google.com"],
        "say": "Good morning. Here is your briefing."
    },
    "chill": {
        "urls": ["https://youtube.com", "https://reddit.com"],
        "volume": 50,
        "say": "Relaxing."
    }
}


def run_macro(name):
    """
    Executes a named workflow (work, morning, chill).
    """
    if name not in WORKFLOWS:
        return f"Macro '{name}' not found. Available: {', '.join(WORKFLOWS.keys())}"

    plan = WORKFLOWS[name]
    log = []

    # 1. Open Apps
    if "apps" in plan:
        for app in plan["apps"]:
            apps.open_app(app)
            log.append(f"Opened {app}")
            time.sleep(1)  # Wait for launch

    # 2. Open URLs
    if "urls" in plan:
        for url in plan["urls"]:
            webbrowser.open(url)
            log.append(f"Opened {url}")

    # 3. System Settings
    if "volume" in plan:
        desktop.set_volume(plan["volume"])
        log.append(f"Volume set to {plan['volume']}")

    # 4. Voice
    if "say" in plan:
        desktop.speak(plan["say"])

    return "\n".join(log)