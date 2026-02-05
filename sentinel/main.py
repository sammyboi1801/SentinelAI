# FILE: main.py
import typer
from sentinel.core.config import ConfigManager
from sentinel.core.agent import SentinelAgent
from sentinel.core.ui import UI
from sentinel.core.registry import initialize_tools
from sentinel.core.setup import setup_wizard

app = typer.Typer(
    name="Sentinel",
    help="Autonomous AI Agent for your OS",
    add_completion=False,
    no_args_is_help=False
)


def boot_sequence(briefing: bool = False):
    """
    Shared startup logic for both default run and 'start' command.
    """
    UI.console.clear()

    # 1. Check Configuration
    cfg = ConfigManager()
    if not cfg.exists():
        setup_wizard()
        cfg = ConfigManager()  # Reload after wizard

    # 2. Boot Up
    UI.print_banner()

    # Check for keys
    # We check if ANY key is present or if using Ollama
    has_key = (
            cfg.get_key("openai") or
            cfg.get_key("anthropic") or
            cfg.get_key("groq") or
            cfg.get("llm.provider") == "ollama"
    )

    if not has_key:
        UI.print_warning("No LLM API Key found. System running in Limited Mode.")
    else:
        provider = cfg.get("llm.provider", "unknown")
        UI.print_system(f"Brain Active: [green]{provider.upper()}[/green]")

    # 3. Initialize Background Services
    initialize_tools()

    # 4. Run Briefing (If requested)
    if briefing:
        if has_key:
            UI.print_system("Generating Daily Briefing...")
            try:
                from sentinel.core.cognitive import get_daily_briefing
                report = get_daily_briefing(cfg)
                UI.print_agent(report)
            except Exception as e:
                UI.print_error(f"Briefing failed: {e}")
        else:
            UI.print_error("Skipping Daily Briefing (Offline Mode).")

    # 5. Start Agent Loop
    try:
        agent = SentinelAgent(cfg)
        agent.run_loop()
    except KeyboardInterrupt:
        UI.print_system("Shutting down...")
    except Exception as e:
        UI.print_error(f"Critical System Failure: {e}")


@app.callback(invoke_without_command=True)
def main(
        ctx: typer.Context,
        briefing: bool = typer.Option(False, "--briefing", "-b", help="Run Daily Briefing on startup")
):
    """
    Main Entry Point. Checks state and routes to Setup or Runtime.
    """
    # If a subcommand (like 'config' or 'auth') is called, skip this default boot
    if ctx.invoked_subcommand is not None:
        return

    boot_sequence(briefing=briefing)


@app.command()
def start(
        briefing: bool = typer.Option(False, "--briefing", "-b", help="Run Daily Briefing on startup")
):
    """Explicit start command."""
    boot_sequence(briefing=briefing)


@app.command()
def config():
    """Re-run the configuration wizard."""
    setup_wizard()


@app.command()
def auth():
    """Run the Google Authentication fix tool."""
    from sentinel.auth import fix_authentication
    fix_authentication()


if __name__ == "__main__":
    app()