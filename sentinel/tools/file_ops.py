import os
import fitz  # PyMuPDF
import pandas as pd
from docx import Document
from sentinel.tools.smart_index import index_file


def read_file(path):
    """
    Reads a file from a specific path.
    Supports: PDF, DOCX, XLSX, CSV, TXT, PY, MD, JSON.
    """
    index_file(path)

    if not os.path.exists(path):
        return "Error: File not found."

    ext = os.path.splitext(path)[1].lower()

    try:
        if ext == '.pdf':
            text = ""
            try:
                with fitz.open(path) as doc:
                    # Limit to first 20 pages to avoid overloading the LLM context
                    for page in doc[:20]:
                        text += page.get_text() + "\n"
                return text if text.strip() else "[PDF contains no selectable text (Scanned?)]"
            except Exception as e:
                return f"[Error reading PDF: {e}]"

        # --- Word Docs ---
        elif ext == '.docx':
            try:
                doc = Document(path)
                return "\n".join([p.text for p in doc.paragraphs])
            except Exception as e:
                return f"[Error reading DOCX: {e}]"

        # --- Excel (Data View) ---
        elif ext in ['.xlsx', '.xls']:
            try:
                # Read first sheet, max 50 rows to keep it readable
                df = pd.read_excel(path, nrows=50)
                return df.to_markdown(index=False)
            except Exception as e:
                return f"[Error reading Excel: {e}]"

        # --- CSV ---
        elif ext == '.csv':
            try:
                df = pd.read_csv(path, nrows=50)
                return df.to_markdown(index=False)
            except Exception as e:
                return f"[Error reading CSV: {e}]"

        # --- Code / Text ---
        else:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(10000)  # Limit to first 10k characters to prevent lag

    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path, content):
    index_file(path)

    try:
        # Ensure directory exists
        folder = os.path.dirname(path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Saved to {path}"
    except Exception as e:
        return str(e)