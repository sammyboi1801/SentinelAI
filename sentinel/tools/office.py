import os
import pandas as pd
from docx import Document
from openpyxl import load_workbook


def create_word(filename, content):
    """Creates a new Word document with the given content."""
    if not filename.endswith(".docx"):
        filename += ".docx"

    try:
        doc = Document()
        doc.add_paragraph(content)
        doc.save(filename)
        return f"Success: Created Word doc at {os.path.abspath(filename)}"
    except Exception as e:
        return f"Error creating Word doc: {e}"


def create_excel(filename, data_list):
    """
    Creates a new Excel file from a list of dictionaries.
    Example data_list: [{"Name": "Alice", "Age": 30}, {"Name": "Bob", "Age": 25}]
    """
    if not filename.endswith(".xlsx"):
        filename += ".xlsx"

    try:
        df = pd.DataFrame(data_list)
        df.to_excel(filename, index=False)
        return f"Success: Created Excel sheet at {os.path.abspath(filename)}"
    except Exception as e:
        return f"Error creating Excel: {e}"


def append_excel(filename, data_list):
    """Appends data to an existing Excel file."""
    if not os.path.exists(filename):
        return create_excel(filename, data_list)

    try:
        # Load existing data
        df_existing = pd.read_excel(filename)
        df_new = pd.DataFrame(data_list)

        # Combine and save
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
        df_final.to_excel(filename, index=False)
        return f"Success: Appended {len(data_list)} rows to {filename}."
    except Exception as e:
        return f"Error appending to Excel: {e}"


def read_excel(filename):
    """Reads an Excel file and returns a summary."""
    if not os.path.exists(filename):
        return "Error: File not found."

    try:
        df = pd.read_excel(filename)
        # Return markdown string, limit to 50 rows to save tokens
        if len(df) > 50:
            return f"File found. Showing first 50 rows:\n{df.head(50).to_markdown(index=False)}"
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error reading Excel: {e}"