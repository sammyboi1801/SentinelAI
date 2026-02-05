from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box
from rich.table import Table


class UI:
    console = Console()

    @staticmethod
    def print_banner():
        logo = """
   ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗     
   ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║     
   ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║     
   ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║     
   ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
   ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
        """
        UI.console.print(f"[bold cyan]{logo}[/bold cyan]")
        UI.console.print("[dim]OPERATING SYSTEM v1.0[/dim]\n")

    @staticmethod
    def print_system(msg):
        UI.console.print(f"[dim]System: {msg}[/dim]")

    @staticmethod
    def print_success(msg):
        UI.console.print(f"[bold green]✔ {msg}[/bold green]")

    @staticmethod
    def print_warning(msg):
        UI.console.print(f"[bold yellow]⚠ {msg}[/bold yellow]")

    @staticmethod
    def print_error(msg):
        UI.console.print(Panel(
            f"[bold white]{msg}[/bold white]",
            title="System Alert",
            border_style="red",
            box=box.ROUNDED,
            expand=False
        ))

    @staticmethod
    def print_agent(text, model=None):
        """The SENTINEL Response Panel."""
        if not isinstance(text, Markdown):
            text = Markdown(str(text))

        title = "[bold cyan]SENTINEL[/bold cyan]"
        if model:
            title += f" [dim]({model})[/dim]"

        UI.console.print(Panel(
            text,
            title=title,
            title_align="left",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2),
            expand=True
        ))

    @staticmethod
    def print_tool(tool_name):
        UI.console.print(f"[dim]   ⚙ Executing: {tool_name}...[/dim]")

    @staticmethod
    def print_result(result):
        text = str(result)
        if len(text) > 400:
            text = text[:400] + "... (truncated)"
        UI.console.print(Panel(
            text,
            title="Action Result",
            border_style="dim white",
            box=box.ROUNDED,
            expand=False
        ))

    @staticmethod
    def print_help():
        table = Table(title="Sentinel Control Panel", border_style="cyan", box=box.ROUNDED)
        table.add_column("Command", style="bold cyan")
        table.add_column("Description", style="white")

        table.add_row("/help", "Show this menu")
        table.add_row("/exit", "Shutdown system")
        table.add_row("/status", "View current model, provider, and memory stats")
        table.add_row("/memory [n]", "Set Context Window size (e.g., /memory 5)")
        table.add_row("/log [on/off]", "Toggle audit logging (Default: OFF)")

        table.add_row("/clear", "Clear active chat memory (RAM only)")
        table.add_row("/wipe", "Wipe long-term memory (Vector DB + brain.db)")
        table.add_row("/factory_reset", "[bold red]FULL FACTORY RESET[/bold red] (Deletes EVERYTHING)")

        table.add_row("/switch [p] [m]", "Switch Brain (e.g., /switch groq llama3)")
        table.add_row("/setkey [p] [k]", "Update API Key")

        UI.console.print(table)

    @staticmethod
    def get_input():
        try:
            UI.console.print()
            return UI.console.input("[bold cyan]>>> [/bold cyan]")
        except KeyboardInterrupt:
            return None