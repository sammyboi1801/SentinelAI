import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from sentinel.core.config import ConfigManager
from sentinel.paths import CREDENTIALS_PATH as CREDS_FILE

console = Console()
cfg = ConfigManager()


def print_step(title):
    console.print(f"\n[bold cyan]🔹 {title}[/bold cyan]")


def setup_wizard():
    console.clear()
    console.print(Panel.fit(
        "[bold white]Welcome to Sentinel OS[/bold white]\n[dim]Autonomous AI Agent System[/dim]",
        border_style="cyan",
        padding=(1, 4)
    ))

    console.print("\n[italic]Let's get your system configured. Press Enter to skip optional fields.[/italic]\n")

    # 1. User Profile
    print_step("User Profile")
    name = Prompt.ask("What should I call you?", default="User")
    location = Prompt.ask("What is your city? (for weather/time)", default="New York")

    cfg.set("user.name", name)
    cfg.set("user.location", location)

    # 2. Intelligence Engine
    print_step("Intelligence Engine")
    provider = Prompt.ask(
        "Select Primary Brain",
        choices=["openai", "anthropic", "groq", "ollama"],
        default="openai"
    )

    api_key = ""
    if provider != "ollama":
        api_key = Prompt.ask(f"Enter API Key for [cyan]{provider}[/cyan]", password=True)

    cfg.set("llm.provider", provider)

    if api_key:
        cfg.set_key(provider, api_key)

    # 3. Search
    print_step("Search Capabilities")
    console.print("Sentinel uses [bold green]Tavily[/bold green] for advanced research, falling back to DuckDuckGo.")

    tavily_key = Prompt.ask("Enter Tavily API Key (Optional)", password=True)
    if tavily_key:
        cfg.set_key("tavily", tavily_key)

    serp_key = Prompt.ask("Enter SerpAPI Key (Optional - for Flights)", password=True)
    if serp_key:
        cfg.set_key("serp_api", serp_key)

    gmaps_key = Prompt.ask("Enter Google Maps API Key (Optional - for Navigation)", password=True)
    if gmaps_key:
        cfg.set_key("google_maps", gmaps_key)

    # 4. Google Workspace
    print_step("Google Workspace")
    if Confirm.ask("Do you want to link Gmail/Calendar now?"):
        if CREDS_FILE.exists():
            console.print("[green]✔ credentials.json found.[/green]")
            console.print("Authentication will trigger automatically on first use.")
        else:
            console.print("[red]❌ credentials.json not found.[/red]\n")
            console.print("1. Go to Google Cloud Console")
            console.print("2. Enable Gmail + Calendar APIs")
            console.print("3. Create OAuth Desktop App")
            console.print("4. Download credentials.json")
            console.print("\nPlace it here:\n")
            console.print(f"[bold cyan]{CREDS_FILE}[/bold cyan]")
            console.print("\nThen run: sentinel auth")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Initializing Neural Interfaces...", total=100)
        time.sleep(0.5)
        progress.update(task, advance=50)
        cfg.set("system.setup_completed", True)
        time.sleep(0.5)
        progress.update(task, advance=50)

    console.print("\n[bold green]✔ Setup Complete.[/bold green] Launching Sentinel...")
    time.sleep(1)