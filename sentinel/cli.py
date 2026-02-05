from sentinel.main import app
from sentinel.core.config import ConfigManager
from sentinel.core.setup import setup_wizard

def main():
    cfg = ConfigManager()
    if not cfg.exists():
        setup_wizard()
    app()