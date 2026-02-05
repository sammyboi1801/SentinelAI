import time
import json
import os
from datetime import datetime
from sentinel.core.config import ConfigManager
from pathlib import Path

BASE_DIR = Path.home() / ".sentinel-1"
BASE_DIR.mkdir(exist_ok=True)
LOG_FILE = BASE_DIR / "audit_log.jsonl"


class AuditLogger:
    def __init__(self):
        self.cfg = ConfigManager()

    def is_enabled(self):
        return self.cfg.get("system.audit_logging", False)

    def toggle(self, state: bool):
        self.cfg.set("system.audit_logging", state)
        status = "ENABLED" if state else "DISABLED"
        return f"Audit Logging is now {status}."

    def log_event(self, event_type, provider, model, input_data, output_data, duration_ms):
        if not self.is_enabled():
            return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "provider": provider,
            "model": model,
            "duration_ms": round(duration_ms, 2),
            "input": str(input_data)[:2000],
            "output": str(output_data)
        }

        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Logger Error: {e}")

# Global Instance
audit = AuditLogger()