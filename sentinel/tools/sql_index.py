# FILE: tools/sql_index.py
import sqlite3
import os
import datetime
import platform
import threading
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

# ─── Watchdog watcher state ───────────────────────────────────────────────────
_watcher_thread = None
_watcher_active = False

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_drives():
    """Returns a list of all logical drives on the system."""
    drives = []
    if platform.system() == "Windows":
        import string
        drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    else:
        drives = ["/"]
        if os.path.exists("/Volumes"):
            drives.extend([os.path.join("/Volumes", d) for d in os.listdir("/Volumes")])
        if os.path.exists("/media"):
            drives.extend([os.path.join("/media", d) for d in os.listdir("/media")])
    return drives


def _get_scan_targets():
    """Returns the list of directories to watch / scan."""
    home = os.path.expanduser("~")
    targets = [
        os.path.join(home, "Desktop"),
        os.path.join(home, "Documents"),
        os.path.join(home, "Downloads"),
        os.path.join(home, "Pictures"),
        os.path.join(home, "Music"),
        os.path.join(home, "Videos"),
        r"D:\Python Projects"
    ]
    all_drives = get_all_drives()
    for drive in all_drives:
        if "C:" in drive.upper():
            continue
        targets.append(drive)
    return list(set(targets))


def _upsert_file(fullpath: str):
    """Insert or update a single file record. Safe to call from any thread."""
    if not os.path.exists(fullpath):
        return
    fname = os.path.basename(fullpath)
    if fname.startswith("~$") or fname.startswith("."):
        return
    try:
        stats = os.stat(fullpath)
        size_mb = round(stats.st_size / (1024 * 1024), 2)
        current_mtime = stats.st_mtime
        mtime_str = datetime.datetime.fromtimestamp(current_mtime).strftime('%Y-%m-%d %H:%M:%S')
        ext = os.path.splitext(fname)[1].lower()

        conn = _get_conn()
        conn.execute('''
            INSERT OR REPLACE INTO files (path, name, extension, size_mb, modified_date, mtime_raw)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (fullpath, fname, ext, size_mb, mtime_str, current_mtime))
        conn.commit()
        conn.close()
    except (OSError, PermissionError):
        pass


def _delete_file(fullpath: str):
    """Remove a file record when it's deleted/moved."""
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM files WHERE path = ?", (fullpath,))
        conn.commit()
        conn.close()
    except Exception:
        pass


# ─── Filesystem Watcher ───────────────────────────────────────────────────────

def _start_watcher(watch_dirs: list):
    """
    Starts a watchdog observer in a daemon thread.
    Monitors watched dirs and keeps the index live without full rescans.
    """
    global _watcher_thread, _watcher_active

    if _watcher_active:
        return

    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class _IndexHandler(FileSystemEventHandler):
            def on_created(self, event):
                if not event.is_directory:
                    _upsert_file(event.src_path)

            def on_modified(self, event):
                if not event.is_directory:
                    _upsert_file(event.src_path)

            def on_deleted(self, event):
                if not event.is_directory:
                    _delete_file(event.src_path)

            def on_moved(self, event):
                if not event.is_directory:
                    _delete_file(event.src_path)
                    _upsert_file(event.dest_path)

        observer = Observer()
        handler = _IndexHandler()

        watched_count = 0
        for d in watch_dirs:
            if os.path.exists(d):
                observer.schedule(handler, d, recursive=True)
                watched_count += 1

        if watched_count == 0:
            return

        observer.start()
        _watcher_active = True

        def _keep_alive():
            try:
                observer.join()
            except Exception:
                pass

        _watcher_thread = threading.Thread(target=_keep_alive, daemon=True)
        _watcher_thread.start()

        print(f"[System] 👁  File Watcher active on {watched_count} directories.")

    except ImportError:
        print("[System] ⚠  watchdog not installed — live indexing disabled. Run: pip install watchdog")
    except Exception as e:
        print(f"[System] ⚠  File Watcher failed to start: {e}")


# ─── Full index build (initial scan) ─────────────────────────────────────────

def build_index(silent=True):
    conn = _get_conn()
    cursor = conn.cursor()

    # Setup
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

    targets = _get_scan_targets()

    cursor.execute("SELECT path, mtime_raw FROM files")
    existing_files = {row['path']: row['mtime_raw'] for row in cursor.fetchall()}

    updates = []
    seen_paths = set()

    if not silent:
        print(f"[System] Scanning {len(targets)} locations...")

    for folder in targets:
        if not os.path.exists(folder):
            continue

        for root, dirs, filenames in os.walk(folder):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

            for f in filenames:
                if f.startswith("~$") or f.startswith("."):
                    continue

                fullpath = os.path.join(root, f)
                seen_paths.add(fullpath)

                try:
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

    if updates:
        if not silent:
            print(f"[System] Indexing {len(updates)} new/changed files...")
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

    # After first scan, start the watcher so future changes are instant
    _start_watcher(targets)

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

    if not results:
        return "No files found matching that name."

    return "\n".join([f"- {r['name']} ({r['modified_date']})\n  Path: {r['path']}" for r in results])