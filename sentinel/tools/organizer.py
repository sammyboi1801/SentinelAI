import os
import shutil
import datetime
from pathlib import Path
from typing import List, Dict


def get_downloads_folder() -> str:
    """
    Returns the path to the user's Downloads folder.
    Cross-platform implementation using pathlib.
    """
    # This works on Windows, macOS, and Linux
    return str(Path.home() / "Downloads")


def _get_unique_name(destination_folder: Path, filename: str) -> Path:
    """
    If file exists, appends (1), (2), etc. to prevent overwrite.
    """
    file_path = destination_folder / filename
    if not file_path.exists():
        return file_path

    stem = file_path.stem
    suffix = file_path.suffix
    counter = 1

    while file_path.exists():
        file_path = destination_folder / f"{stem} ({counter}){suffix}"
        counter += 1

    return file_path


def organize_files(directory: str, strategy: str = "extension") -> str:
    """
    Organizes files in a directory into subfolders.
    Strategies:
      - 'extension' (Groups by type: Images, Videos, Docs)
      - 'date' (Groups by YYYY-MM-DD)
    """
    if directory.lower() == "downloads":
        directory = get_downloads_folder()

    target_dir = Path(directory)

    if not target_dir.exists():
        return f"Error: Directory '{directory}' not found."

    actions_taken = []

    # Smart grouping for cleaner organization
    TYPE_MAP = {
        # Images
        "jpg": "Images", "jpeg": "Images", "png": "Images", "gif": "Images",
        "svg": "Images", "webp": "Images", "tiff": "Images", "bmp": "Images",
        # Video
        "mp4": "Videos", "mov": "Videos", "avi": "Videos", "mkv": "Videos",
        "wmv": "Videos", "flv": "Videos", "webm": "Videos",
        # Audio
        "mp3": "Audio", "wav": "Audio", "aac": "Audio", "flac": "Audio", "m4a": "Audio",
        # Documents
        "pdf": "Documents", "doc": "Documents", "docx": "Documents",
        "txt": "Documents", "rtf": "Documents", "odt": "Documents",
        "xls": "Spreadsheets", "xlsx": "Spreadsheets", "csv": "Spreadsheets",
        "ppt": "Presentations", "pptx": "Presentations",
        # Archives
        "zip": "Archives", "rar": "Archives", "7z": "Archives",
        "tar": "Archives", "gz": "Archives",
        # Installers
        "exe": "Installers", "msi": "Installers", "dmg": "Installers",
        "deb": "Installers", "pkg": "Installers", "iso": "Installers",
        # Code
        "py": "Code", "js": "Code", "html": "Code", "css": "Code",
        "json": "Code", "java": "Code", "cpp": "Code", "ts": "Code"
    }

    try:
        # List all files (skip directories and hidden files)
        files = [f for f in target_dir.iterdir() if f.is_file() and not f.name.startswith('.')]

        for file_path in files:
            folder_name = "Misc"

            if strategy == "extension":
                ext = file_path.suffix.lstrip('.').lower()
                # Use mapped name if available, else generic folder
                folder_name = TYPE_MAP.get(ext, f"{ext.upper()}_Files")

            elif strategy == "date":
                timestamp = file_path.stat().st_mtime
                date = datetime.datetime.fromtimestamp(timestamp)
                folder_name = date.strftime("%Y-%m-%d")

            else:
                return f"Unknown strategy: {strategy}"

            # Create destination folder
            dest_folder = target_dir / folder_name
            dest_folder.mkdir(exist_ok=True)

            # Move file safely (rename if collision)
            final_path = _get_unique_name(dest_folder, file_path.name)
            shutil.move(str(file_path), str(final_path))

            actions_taken.append(f"Moved {file_path.name} -> {folder_name}/")

        if not actions_taken:
            return "No files needed organizing."

        return f"Organized {len(actions_taken)} files:\n" + "\n".join(actions_taken[:10]) + (
            "\n...and more." if len(actions_taken) > 10 else "")

    except Exception as e:
        return f"Organization failed: {e}"


def bulk_rename(directory: str, pattern: str, replace_with: str) -> str:
    """
    Renames files matching a pattern.
    Example: bulk_rename(".", "Screen Shot", "Capture")
    """
    if directory.lower() == "downloads":
        directory = get_downloads_folder()

    target_dir = Path(directory)
    if not target_dir.exists():
        return f"Error: Directory '{directory}' not found."

    count = 0
    try:
        for file_path in target_dir.iterdir():
            if not file_path.is_file():
                continue

            if pattern in file_path.name:
                new_name = file_path.name.replace(pattern, replace_with)
                new_path = target_dir / new_name

                # Prevent overwrite if destination exists
                if new_path.exists():
                    new_path = _get_unique_name(target_dir, new_name)

                file_path.rename(new_path)
                count += 1

        return f"Renamed {count} files."
    except Exception as e:
        return f"Rename Error: {e}"