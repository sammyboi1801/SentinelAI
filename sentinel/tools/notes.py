import json
import os
import datetime
from pathlib import Path

BASE_DIR = Path.home() / ".sentinel-1"
BASE_DIR.mkdir(exist_ok=True)
NOTES_FILE = BASE_DIR / "memory.json"


def _load_notes():
    """Helper to load notes from JSON file"""
    if not os.path.exists(NOTES_FILE):
        return []
    try:
        with open(NOTES_FILE, 'r') as f:
            return json.load(f)
    except:
        return []


def _save_notes(notes):
    """Helper to save notes to JSON file"""
    with open(NOTES_FILE, 'w') as f:
        json.dump(notes, f, indent=2)


def add_note(category, content):
    """
    Saves a persistent memory.
    Args:
        category: (str) "user_pref", "project_status", "todo", "concept"
        content: (str) The actual information to remember.
    """
    notes = _load_notes()
    note = {
        "id": len(notes) + 1,
        "timestamp": str(datetime.datetime.now()),
        "category": category,
        "content": content
    }
    notes.append(note)
    _save_notes(notes)
    return f"Note added to {category}: {content}"


def list_notes(category=None):
    """
    Retrieves memories.
    Args:
        category: (Optional) Filter by "user_pref", "todo", etc.
    """
    notes = _load_notes()
    if category:
        filtered = [n for n in notes if n["category"].lower() == category.lower()]
        if not filtered:
            return f"No notes found in category '{category}'."
        return json.dumps(filtered, indent=2)

    # If no category, return all (summarized)
    return json.dumps(notes, indent=2)


def delete_note(note_id):
    """Removes a note by ID."""
    notes = _load_notes()
    try:
        note_id = int(note_id)
    except:
        pass

    new_notes = [n for n in notes if n["id"] != note_id]
    if len(notes) == len(new_notes):
        return "Error: Note ID not found."

    _save_notes(new_notes)
    return f"Note {note_id} deleted."