import json
import os
import keyring
from typing import Any, Optional
from sentinel.paths import CONFIG_PATH

APP_NAME = "sentinel-ai"

class ConfigManager:
    def __init__(self):
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        if not CONFIG_PATH.exists():
            default_config = {
                "user": {"name": "User", "location": "New York"},
                "system": {"setup_completed": False, "audit_logging": False},
                "llm": {"provider": "openai", "model": "gpt-4o"}
            }
            self.save(default_config)

    def exists(self) -> bool:
        """Checks if setup has been completed."""
        return self.get("system.setup_completed", False)

    def load(self) -> dict:
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save(self, data: dict):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def get(self, dot_path: str, default: Any = None) -> Any:
        """
        Retrieves a value using dot notation (e.g., "user.name").
        """
        data = self.load()
        keys = dot_path.split(".")
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key)
            else:
                return default
        return data if data is not None else default

    def set(self, dot_path: str, value: Any):
        """
        Sets a value using dot notation and saves immediately.
        """
        data = self.load()
        keys = dot_path.split(".")

        # Traverse to the last key
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set value
        current[keys[-1]] = value
        self.save(data)

    # --- KEYRING INTEGRATION (Secrets) ---

    def set_key(self, service: str, api_key: str):
        """Stores a secret in the OS Keychain."""
        if not api_key: return
        try:
            # Service = "openai", "anthropic", etc.
            keyring.set_password(APP_NAME, service, api_key)
        except Exception as e:
            print(f"[Config] Error saving to Keychain: {e}")

    def get_key(self, service: str) -> Optional[str]:
        """Retrieves a secret from the OS Keychain."""
        try:
            return keyring.get_password(APP_NAME, service)
        except Exception:
            return None

    def update_llm(self, provider, model):
        """
        Helper used by system_ops.py to switch brains and save to disk.
        """
        self.set("llm.provider", provider)
        self.set("llm.model", model)
        print(f"[Config] Saved new brain settings: {provider} / {model}")