import os
import psutil
import pyperclip
import subprocess
import typer
from sentinel.core.config import ConfigManager
from sentinel.core.ui import UI


def switch_model(provider, model=None):
    """
    Updates configuration and interactively asks for API keys if missing.
    """
    provider = provider.lower().strip()

    defaults = {
        "openai": "gpt-4o",
        "groq": "llama-3.3-70b-versatile",
        "anthropic": "claude-sonnet-4-5-20250929",
        "ollama": "llama3"
    }

    if not model:
        model = defaults.get(provider)
        if not model:
            model = "default-model"

    cfg = ConfigManager()

    existing_key = cfg.get_key(provider)

    is_key_missing = not existing_key or str(existing_key).strip() == ""
    needs_key = (provider != "ollama" and is_key_missing)

    if needs_key:
        UI.console.print(f"\n[bold yellow]⚠️  Configuration Required[/bold yellow]")
        UI.console.print(
            f"You are switching to [cyan]{provider.upper()}[/cyan], but no API key was found.")

        confirm = typer.confirm(f"Would you like to set up {provider.upper()} now?")

        if confirm:
            new_key = typer.prompt(f"Enter API Key for {provider.upper()}", hide_input=True)
            if new_key and new_key.strip():
                cfg.set_key(provider, new_key.strip())
                UI.print_success("API Key stored securely.")
            else:
                return "❌ Operation cancelled. Key cannot be empty."
        else:
            return f"❌ Switch cancelled. {provider.upper()} requires an API key."

    cfg.update_llm(provider, model)
    return f"⚡ Brain updated to [bold green]{provider.upper()}[/bold green] | Model: {model}"


def get_clipboard():
    try:
        content = pyperclip.paste()

        if len(content) > 5000:
            return f"{content[:5000]}... [Truncated]"
        return content
    except Exception as e:
        return f"Error reading clipboard: {e}"


def get_system_stats():
    cpu = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory().percent
    return f"CPU: {cpu}% | RAM: {memory}%"


def run_cmd(cmd):
    """
    Runs a shell command with a timeout to prevent freezing.
    """
    try:
        result = subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.STDOUT,
            timeout=10
        )
        return result.decode('utf-8').strip()
    except subprocess.TimeoutExpired:
        return f"❌ Command timed out after 10 seconds. (It might still be running in background)"
    except subprocess.CalledProcessError as e:
        return f"❌ Command failed:\n{e.output.decode('utf-8')}"
    except Exception as e:
        return f"❌ Error: {e}"


def kill_process(name):
    """
    Kills processes by name, but protects Sentinel itself.
    """
    killed_count = 0
    my_pid = os.getpid()

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if name.lower() in proc.info['name'].lower():
                if proc.info['pid'] == my_pid:
                    continue

                proc.kill()
                killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if killed_count == 0:
        return f"No processes found matching '{name}'."
    return f"💀 Killed {killed_count} process(es) matching '{name}'."