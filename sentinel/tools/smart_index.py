import sqlite3
import os
import time
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path

BASE_DIR = Path.home() / ".sentinel-1"
BASE_DIR.mkdir(exist_ok=True)

DB = BASE_DIR / "smart_files.db"

_MODEL = None

def get_model():
    """
    Lazy loads the Transformer model only when needed.
    Prevents the system from hanging at startup.
    """
    global _MODEL
    if _MODEL is None:
        print("\n[System] 🧠 Loading Neural Indexing Model (all-MiniLM-L6-v2)...")
        try:
            _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
            print("[System] ✅ Neural Model Loaded.\n")
        except Exception as e:
            print(f"[System] ❌ Failed to load embedding model: {e}")
            return None
    return _MODEL


def init():
    conn = sqlite3.connect(DB)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS files(
        path TEXT PRIMARY KEY,
        name TEXT,
        ext TEXT,
        embedding BLOB,
        last_opened REAL,
        last_modified REAL
    )
    """)
    conn.commit()
    conn.close()


init()


def embed(text):
    """
    Safely embeds text using the lazy-loaded model.
    """
    model = get_model()
    if model is None:
        return None

    # Return as float32 bytes for storage
    return model.encode(text).astype("float32").tobytes()


def index_file(path):
    if not os.path.exists(path):
        return

    name = os.path.basename(path)
    ext = os.path.splitext(path)[1]

    # Simple strategy: Index the filename.
    # For deeper search, you could add file content here.
    text = name

    emb = embed(text)
    if emb is None:
        return  # Skip if model failed to load

    conn = sqlite3.connect(DB)
    conn.execute("""
    INSERT OR REPLACE INTO files
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        path,
        name,
        ext,
        emb,
        time.time(),
        os.path.getmtime(path)
    ))
    conn.commit()
    conn.close()


def smart_find(query, limit=5):
    """
    Semantic search for files.
    """
    model = get_model()
    if model is None:
        return ["Error: AI Model unavailable."]

    q_emb = model.encode(query)

    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT path, embedding, last_opened FROM files"
    ).fetchall()
    conn.close()

    scored = []
    for path, emb, last in rows:
        vec = np.frombuffer(emb, dtype="float32")

        sim = np.dot(q_emb, vec) / (
                np.linalg.norm(q_emb) * np.linalg.norm(vec)
        )

        recency = 1 / (1 + (time.time() - last))
        score = sim * 0.7 + recency * 0.3

        scored.append((score, path))

    scored.sort(reverse=True)
    return [p for _, p in scored[:limit]]