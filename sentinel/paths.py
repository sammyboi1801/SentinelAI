import os
import sys
from pathlib import Path

USER_DATA_DIR = Path.home() / ".sentinel"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR = USER_DATA_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

DRAFTS_DIR = USER_DATA_DIR / "drafts"
DRAFTS_DIR.mkdir(exist_ok=True)
CONFIG_PATH = USER_DATA_DIR / "config.json"
DB_PATH = USER_DATA_DIR / "brain.db"
VECTOR_PATH = USER_DATA_DIR / "brain_vectors"  # ChromaDB folder
AUDIT_LOG_PATH = USER_DATA_DIR / "audit_log.jsonl"
MEMORY_FILE = USER_DATA_DIR / "memory.json"
FILE_INDEX_DB = USER_DATA_DIR / "file_index.db"
SMART_INDEX_DB = USER_DATA_DIR / "smart_files.db"


CREDENTIALS_PATH = USER_DATA_DIR / "credentials.json"
TOKEN_PATH = USER_DATA_DIR / "token.json"

def get_script_path(filename: str) -> str:
    """
    Returns the absolute path to a script bundled inside the pip package.
    Expects scripts to be in: src/sentinel/scripts/
    """

    current_dir = os.path.dirname(os.path.abspath(__file__))
    pkg_root = os.path.dirname(current_dir)
    script_path = os.path.join(pkg_root, "scripts", filename)

    if not os.path.exists(script_path):

        repo_root = os.path.dirname(os.path.dirname(pkg_root))
        dev_path = os.path.join(repo_root, "scripts", filename)

        if os.path.exists(dev_path):
            return dev_path

        raise FileNotFoundError(
            f"Could not find bundled script '{filename}'.\n"
            f"Checked: {script_path}\n"
            f"Checked: {dev_path}"
        )

    return script_path