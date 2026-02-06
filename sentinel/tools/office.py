import os
import pandas as pd
from pathlib import Path
from docx import Document

DOCS_DIR = Path.home() / "Documents"

def _get_safe_path(filename, extension):
    """
    Ensures filename has the right extension and saves to Documents.
    """
    if not filename.endswith(extension):
        filename += extension

    full_path = DOCS_DIR / filename

    return full_path


def create_word(filename, content):
    """Creates a new Word document. Fails if file already exists."""
    path = _get_safe_path(filename, ".docx")

    if path.exists():
        return f"❌ Error: '{path.name}' already exists. Please choose a different name or ask to append."

    try:
        doc = Document()
        doc.add_paragraph(str(content))  # Convert to string just in case
        doc.save(path)
        return f"✅ Word document created: {path}"
    except Exception as e:
        return f"❌ Error creating Word doc: {e}"


def create_excel(filename, data_list):
    """
    Creates a new Excel file. Fails if file already exists.
    data_list example: [{"Name": "Alice", "Age": 30}]
    """
    path = _get_safe_path(filename, ".xlsx")

    if path.exists():
        return f"❌ Error: '{path.name}' already exists. Use 'append_excel' to add data."

    try:
        df = pd.DataFrame(data_list)
        df.to_excel(path, index=False)
        return f"✅ Excel sheet created: {path}"
    except Exception as e:
        return f"❌ Error creating Excel: {e}"


def append_excel(filename, data_list):
    """Appends data to an existing Excel file."""
    path = _get_safe_path(filename, ".xlsx")

    if not path.exists():
        return create_excel(filename, data_list)

    try:
        df_existing = pd.read_excel(path)
        df_new = pd.DataFrame(data_list)

        df_final = pd.concat([df_existing, df_new], ignore_index=True)
        df_final.to_excel(path, index=False)

        return f"✅ Added {len(data_list)} rows to {path.name}."
    except Exception as e:
        return f"❌ Error appending to Excel: {e}"


def read_excel(filename):
    """Reads an Excel file and returns a markdown summary."""
    path = _get_safe_path(filename, ".xlsx")

    if not path.exists():
        return f"❌ Error: File not found at {path}"

    try:
        df = pd.read_excel(path)

        if len(df) > 50:
            preview = df.head(50).to_markdown(index=False)
            return f"📂 File: {path.name} (Showing first 50 rows)\n\n{preview}\n\n... ({len(df) - 50} more rows)"

        return f"📂 File: {path.name}\n\n{df.to_markdown(index=False)}"
    except Exception as e:
        return f"❌ Error reading Excel: {e}"