# FILE: tools/smart_index.py
import sqlite3
import os
import time
import threading
import queue
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path

BASE_DIR = Path.home() / ".sentinel-1"
BASE_DIR.mkdir(exist_ok=True)

DB = BASE_DIR / "smart_files.db"

_MODEL = None
_MODEL_LOCK = threading.Lock()

# ─── Background embedding queue ───────────────────────────────────────────────
# Files land here after metadata indexing; embeddings are computed asynchronously.
_EMBED_QUEUE: queue.Queue = queue.Queue()
_EMBED_WORKER_STARTED = False

# Extensions that can yield useful text snippets for richer embeddings
_TEXT_EXTENSIONS = {'.txt', '.md', '.py', '.json', '.csv', '.html', '.js', '.ts', '.yaml', '.yml', '.toml'}
_DOC_EXTENSIONS  = {'.pdf', '.docx', '.xlsx'}

# Max chars of content to embed (keeps vectors fast & consistent)
_CONTENT_SNIPPET_CHARS = 512


def get_model():
    """Lazy-loads the Transformer model once, thread-safe."""
    global _MODEL
    if _MODEL is None:
        with _MODEL_LOCK:
            if _MODEL is None:  # double-checked locking
                print("\n[System] 🧠 Loading Neural Indexing Model (all-MiniLM-L6-v2)...")
                try:
                    _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
                    print("[System] ✅ Neural Model Loaded.\n")
                except Exception as e:
                    print(f"[System] ❌ Failed to load embedding model: {e}")
    return _MODEL


def init():
    conn = sqlite3.connect(DB)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS files(
        path        TEXT PRIMARY KEY,
        name        TEXT,
        ext         TEXT,
        snippet     TEXT,
        embedding   BLOB,
        last_opened REAL,
        last_modified REAL
    )
    """)
    conn.commit()
    conn.close()


init()


# ─── Content extraction ───────────────────────────────────────────────────────

def _extract_snippet(path: str, ext: str) -> str:
    """
    Returns a short text snippet from the file for richer embeddings.
    Falls back gracefully — worst case returns the filename alone.
    """
    try:
        if ext in _TEXT_EXTENSIONS:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(_CONTENT_SNIPPET_CHARS)

        elif ext == '.pdf':
            try:
                import fitz
                with fitz.open(path) as doc:
                    return doc[0].get_text()[:_CONTENT_SNIPPET_CHARS] if doc.page_count else ""
            except Exception:
                pass

        elif ext == '.docx':
            try:
                from docx import Document
                doc = Document(path)
                text = " ".join(p.text for p in doc.paragraphs if p.text)
                return text[:_CONTENT_SNIPPET_CHARS]
            except Exception:
                pass

    except (OSError, PermissionError):
        pass

    return ""  # filename will carry the embedding on its own


# ─── Core embedding ───────────────────────────────────────────────────────────

def embed(text: str):
    """Encodes text to a float32 byte blob. Returns None if model unavailable."""
    model = get_model()
    if model is None:
        return None
    return model.encode(text).astype("float32").tobytes()


def _build_embed_text(name: str, snippet: str) -> str:
    """
    Combines filename + content snippet into one embedding string.
    Filename is repeated to give it higher weight in the vector space.
    """
    base = os.path.splitext(name)[0].replace("_", " ").replace("-", " ")
    if snippet:
        return f"{base} {base} {snippet[:_CONTENT_SNIPPET_CHARS]}"
    return base


# ─── Database write ───────────────────────────────────────────────────────────

def _write_to_db(path, name, ext, snippet, emb):
    conn = sqlite3.connect(DB)
    conn.execute("""
        INSERT OR REPLACE INTO files
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        path,
        name,
        ext,
        snippet,
        emb,
        time.time(),
        os.path.getmtime(path) if os.path.exists(path) else time.time()
    ))
    conn.commit()
    conn.close()


# ─── Background worker ────────────────────────────────────────────────────────

def _embedding_worker():
    """
    Drains _EMBED_QUEUE in a daemon thread.
    Each item is a (path,) tuple placed there by index_file().
    """
    while True:
        try:
            path = _EMBED_QUEUE.get(timeout=5)
            if not os.path.exists(path):
                _EMBED_QUEUE.task_done()
                continue

            name = os.path.basename(path)
            ext  = os.path.splitext(path)[1].lower()
            snippet = _extract_snippet(path, ext)
            embed_text = _build_embed_text(name, snippet)

            emb = embed(embed_text)
            if emb is None:
                _EMBED_QUEUE.task_done()
                continue

            _write_to_db(path, name, ext, snippet, emb)
            _EMBED_QUEUE.task_done()

        except queue.Empty:
            continue
        except Exception:
            try:
                _EMBED_QUEUE.task_done()
            except Exception:
                pass


def _ensure_worker():
    global _EMBED_WORKER_STARTED
    if not _EMBED_WORKER_STARTED:
        t = threading.Thread(target=_embedding_worker, daemon=True, name="sentinel-embed-worker")
        t.start()
        _EMBED_WORKER_STARTED = True


# ─── Public API ───────────────────────────────────────────────────────────────

def index_file(path: str):
    """
    Queues a file for (re-)embedding.
    Returns instantly — the heavy work happens in the background.
    """
    if not os.path.exists(path):
        return
    _ensure_worker()
    _EMBED_QUEUE.put(path)


def index_file_sync(path: str):
    """
    Synchronous version used during initial bulk indexing.
    Blocks until the file is embedded and written.
    """
    if not os.path.exists(path):
        return

    name = os.path.basename(path)
    ext  = os.path.splitext(path)[1].lower()
    snippet = _extract_snippet(path, ext)
    embed_text = _build_embed_text(name, snippet)

    emb = embed(embed_text)
    if emb is None:
        return

    _write_to_db(path, name, ext, snippet, emb)


def smart_find(query: str, limit: int = 5) -> list:
    """
    Semantic search for files.
    Blends cosine similarity (content-aware) + recency.
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
    for path, emb_blob, last in rows:
        if emb_blob is None:
            continue
        vec = np.frombuffer(emb_blob, dtype="float32")

        norm_q = np.linalg.norm(q_emb)
        norm_v = np.linalg.norm(vec)
        if norm_q == 0 or norm_v == 0:
            continue

        sim = np.dot(q_emb, vec) / (norm_q * norm_v)
        recency = 1 / (1 + (time.time() - (last or 0)))
        score = sim * 0.7 + recency * 0.3

        scored.append((score, path))

    scored.sort(reverse=True)
    return [p for _, p in scored[:limit]]