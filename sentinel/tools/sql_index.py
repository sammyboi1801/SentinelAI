# FILE: tools/sql_index.py
import sqlite3
import os
import datetime
import platform
from pathlib import Path

BASE_DIR = Path.home() / ".sentinel-1"
BASE_DIR.mkdir(exist_ok=True)

DB_FILE = BASE_DIR / "sentinel-1.db"


SKIP_DIRS = {
    # System Folders
    "Windows", "Program Files", "Program Files (x86)",
    "AppData", "Application Data",
    "$RECYCLE.BIN", "System Volume Information", "Recovery",
    "boot", "efi",

    # Dev Junk
    "node_modules", "venv", ".venv", ".git", "__pycache__", ".idea", ".vscode"
}


def _get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_drives():
    """
    Returns a list of all logical drives on the system.
    On Windows: ['C:\\', 'D:\\', 'E:\\']
    """
    drives = []
    if platform.system() == "Windows":
        import string
        from ctypes import windll
        drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    else:
        # Unix-based systems
        drives = ["/"]
        if os.path.exists("/Volumes"):  # macOS external drives
            drives.extend([os.path.join("/Volumes", d) for d in os.listdir("/Volumes")])
        if os.path.exists("/media"):  # Linux external drives
            drives.extend([os.path.join("/media", d) for d in os.listdir("/media")])
    return drives


def build_index(silent=True):
    conn = _get_conn()
    cursor = conn.cursor()

    # 1. Setup Database
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            name TEXT,
            extension TEXT,
            size_mb REAL,
            modified_date TEXT,
            mtime_raw REAL
        )
    ''')
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON files(name)")

    # 2. Identify Scan Targets
    targets = []

    home = os.path.expanduser("~")
    targets.extend([
        os.path.join(home, "Desktop"),
        os.path.join(home, "Documents"),
        os.path.join(home, "Downloads"),
        os.path.join(home, "Pictures"),
        os.path.join(home, "Music"),
        os.path.join(home, "Videos"),
        r"D:\Python Projects"
    ])

    all_drives = get_all_drives()
    for drive in all_drives:
        if "C:" in drive.upper():
            continue
        targets.append(drive)

    targets = list(set(targets))

    if not silent: print("[System] Loading existing file index...")
    cursor.execute("SELECT path, mtime_raw FROM files")
    existing_files = {row['path']: row['mtime_raw'] for row in cursor.fetchall()}

    updates = []
    seen_paths = set()

    if not silent:
        print(f"[System] Scanning {len(targets)} locations:\n" + "\n".join([f"   - {t}" for t in targets]))

    for folder in targets:
        if not os.path.exists(folder): continue

        for root, dirs, filenames in os.walk(folder):

            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

            for f in filenames:

                if f.startswith("~$") or f.startswith("."): continue

                fullpath = os.path.join(root, f)
                seen_paths.add(fullpath)

                try:
                    # Check Modification Time
                    stats = os.stat(fullpath)
                    current_mtime = stats.st_mtime

                    if fullpath in existing_files and abs(existing_files[fullpath] - current_mtime) < 1.0:
                        continue

                    size_mb = round(stats.st_size / (1024 * 1024), 2)
                    mtime_str = datetime.datetime.fromtimestamp(current_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    ext = os.path.splitext(f)[1].lower()

                    updates.append((fullpath, f, ext, size_mb, mtime_str, current_mtime))

                except (OSError, PermissionError):
                    continue

    # 5. Commit Changes
    if updates:
        if not silent: print(f"[System] Indexing {len(updates)} new/changed files...")
        cursor.executemany('''
            INSERT OR REPLACE INTO files (path, name, extension, size_mb, modified_date, mtime_raw)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', updates)

    deleted_paths = set(existing_files.keys()) - seen_paths
    if deleted_paths:
        deleted_list = list(deleted_paths)
        chunk_size = 900
        for i in range(0, len(deleted_list), chunk_size):
            chunk = deleted_list[i:i + chunk_size]
            cursor.executemany("DELETE FROM files WHERE path = ?", [(p,) for p in chunk])

    conn.commit()
    conn.close()
    return f"Index Updated: {len(updates)} new, {len(deleted_paths)} removed."


def search_db(query):
    conn = _get_conn()
    cursor = conn.cursor()

    sql_query = f"%{query}%"

    cursor.execute('''
        SELECT name, path, modified_date 
        FROM files 
        WHERE name LIKE ? 
        ORDER BY mtime_raw DESC
        LIMIT 10
    ''', (sql_query,))

    results = cursor.fetchall()
    conn.close()

    if not results: return "No files found matching that name."

    return "\n".join([f"- {r['name']} ({r['modified_date']})\n  Path: {r['path']}" for r in results])