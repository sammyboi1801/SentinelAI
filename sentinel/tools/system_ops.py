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
    provider = provider.lower()

    # Smart Defaults
    defaults = {
        "openai": "gpt-4o",
        "groq": "llama-3.3-70b-versatile",
        "anthropic": "claude-3-5-sonnet-20241022",
        "ollama": "llama3"
    }

    if not model:
        model = defaults.get(provider, "gpt-4o")

    cfg = ConfigManager()

    # 1. Check if we actually have a key for this provider
    # Ollama is local, so it doesn't need a key.
    existing_key = cfg.get_key(provider)
    needs_key = (provider != "ollama" and not existing_key)

    if needs_key:
        UI.console.print(f"\n[bold yellow]⚠️  Configuration Required[/bold yellow]")
        UI.console.print(
            f"You are switching to [cyan]{provider.upper()}[/cyan], but no API key was found in the secure vault.")

        confirm = typer.confirm(f"Would you like to set up {provider.upper()} now?")

        if confirm:
            new_key = typer.prompt(f"Enter API Key for {provider.upper()}", hide_input=True)
            if new_key:
                cfg.set_key(provider, new_key)
                UI.print_success("API Key stored securely in system keychain.")
            else:
                return "❌ Operation cancelled. Key cannot be empty."
        else:
            return f"❌ Switch cancelled. {provider.upper()} requires an API key."

    # 2. Apply the switch
    cfg.update_llm(provider, model)
    return f"⚡ Brain updated to [bold green]{provider.upper()}[/bold green] | Model: {model}"


def get_clipboard():
    try:
        return pyperclip.paste()
    except Exception as e:
        return f"Error reading clipboard: {e}"


def get_system_stats():
    cpu = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory().percent
    return f"CPU: {cpu}% | RAM: {memory}%"


def run_cmd(cmd):
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return result.decode('utf-8').strip()
    except Exception as e:
        return f"Error: {e}"


def kill_process(name):
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if name.lower() in proc.info['name'].lower():
                proc.kill()
                killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return f"Killed {killed_count} process(es) matching '{name}'."