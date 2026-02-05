# FILE: tools/memory_ops.py

import sqlite3
import datetime
import chromadb
import uuid
import json
import re
import gc
from chromadb.utils import embedding_functions
from sentinel.core.config import ConfigManager
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path.home() / ".sentinel-1"
BASE_DIR.mkdir(exist_ok=True)

DB_FILE = BASE_DIR / "brain.db"
CHROMA_PATH = BASE_DIR / "brain_vectors"

# Global references for cleanup
chroma_client = None
collection = None

def ensure_chroma():
    global collection
    if collection is None:
        init_chroma()

def init_chroma():
    """Initializes ChromaDB (Safe re-init)"""
    global chroma_client, collection
    try:
        chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    except Exception as e:
        chroma_client = None
        return

    cfg = ConfigManager()
    openai_key = cfg.get_key("openai")

    if openai_key:
        emb_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=openai_key, model_name="text-embedding-3-small"
        )
    else:
        emb_fn = embedding_functions.DefaultEmbeddingFunction()

    collection = chroma_client.get_or_create_collection(
        name="sentinel_memory", embedding_function=emb_fn
    )

def delete_fact(subject, predicate=None, obj=None):
    """
    Delete matching facts from memory.
    Any field can be None (acts as wildcard).
    """
    ensure_chroma()
    if not collection:
        return "Vector DB unavailable."

    try:
        results = collection.get(include=["metadatas", "documents"])

        ids = results.get("ids", [])
        metadatas = results.get("metadatas", [])
        documents = results.get("documents", [])

        to_delete = []

        for i, meta in enumerate(metadatas):
            text = documents[i]

            match_subject = meta.get("subject") == subject
            match_pred = predicate is None or predicate in text
            match_obj = obj is None or obj in text

            if match_subject and match_pred and match_obj:
                to_delete.append(ids[i])

        if not to_delete:
            return "No matching memory found."

        collection.delete(ids=to_delete)
        return f"Deleted {len(to_delete)} memory entries."

    except Exception as e:
        return f"Delete error: {e}"


# Initialize on import
init_chroma()


def teardown():
    """Releases database locks for wiping."""
    global chroma_client, collection
    try:
        if chroma_client:
            chroma_client.reset()
    except:
        pass

    chroma_client = None
    collection = None
    gc.collect()



def _get_sql_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_memory():
    conn = _get_sql_conn()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            id TEXT PRIMARY KEY, 
            importance INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT, details TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


init_memory()


def _rate_importance(text):
    return 5


def store_fact(subject, predicate, obj, context="user_defined"):
    ensure_chroma()
    if not collection:
        return "Vector DB unavailable."
    fact_text = f"{subject} {predicate} {obj}"
    mem_id = str(uuid.uuid4())
    full_text = f"{fact_text}. Context: {context}"

    collection.add(
        documents=[full_text],
        metadatas=[{"subject": subject, "type": "fact"}],
        ids=[mem_id]
    )

    importance = _rate_importance(fact_text)
    conn = _get_sql_conn()
    conn.execute("INSERT INTO metadata (id, importance) VALUES (?, ?)", (mem_id, importance))
    conn.commit()
    conn.close()
    return f"🧠 Memory Stored: {fact_text}"


def retrieve_relevant_context(query, limit=5):
    ensure_chroma()
    if not collection:
        return ""
    try:
        results = collection.query(query_texts=[query], n_results=20)
    except:
        return ""

    if not results['ids'] or not results['ids'][0]: return ""

    found_ids = results['ids'][0]
    found_texts = results['documents'][0]
    found_distances = results['distances'][0]

    conn = _get_sql_conn()
    placeholders = ','.join(['?'] * len(found_ids))
    sql = f"SELECT * FROM metadata WHERE id IN ({placeholders})"
    rows = conn.execute(sql, found_ids).fetchall()
    conn.close()

    meta_map = {row['id']: dict(row) for row in rows}
    scored_memories = []

    for i, mem_id in enumerate(found_ids):
        meta = meta_map.get(mem_id, {'importance': 5, 'last_accessed': str(datetime.datetime.now())})
        text = found_texts[i]
        relevance = 1.0 - (found_distances[i] / 2.0)
        try:
            last_accessed = datetime.datetime.strptime(meta['last_accessed'], "%Y-%m-%d %H:%M:%S")
            hours_diff = (datetime.datetime.now() - last_accessed).total_seconds() / 3600
            recency_score = 0.99 ** hours_diff
        except:
            recency_score = 1.0

        importance_score = meta['importance'] / 10.0
        final_score = (relevance * 0.5) + (importance_score * 0.3) + (recency_score * 0.2)

        if final_score > 0.4: scored_memories.append((final_score, mem_id, text))

    scored_memories.sort(key=lambda x: x[0], reverse=True)
    top_picks = scored_memories[:limit]

    if top_picks:
        conn = _get_sql_conn()
        winner_ids = [x[1] for x in top_picks]
        placeholders = ','.join(['?'] * len(winner_ids))
        conn.execute(f"UPDATE metadata SET last_accessed = CURRENT_TIMESTAMP WHERE id IN ({placeholders})", winner_ids)
        conn.commit()
        conn.close()

    if not top_picks:
        return "No long-term memories found."

    return "Relevant Memories:\n" + "\n".join([f"- {x[2]}" for x in top_picks])


def log_activity(action, details):
    try:
        conn = _get_sql_conn()
        conn.execute("INSERT INTO logs (action, details) VALUES (?, ?)", (action, details))
        conn.commit()
        conn.close()
    except:
        pass


def reflect_on_day(date_str=None):
    """
    Retrieves activity logs for a specific day.
    Required by registry.py and cognitive.py for Daily Briefings.
    """
    if not date_str:
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    conn = _get_sql_conn()
    c = conn.execute('''
        SELECT time(timestamp) as t, action, details 
        FROM logs 
        WHERE date(timestamp) = ? 
        ORDER BY timestamp ASC
    ''', (date_str,))

    logs = c.fetchall()
    conn.close()

    if not logs: return f"No activity recorded for {date_str}."

    summary = f"Activity Log for {date_str}:\n"
    for log in logs:
        summary += f"[{log['t']}] {log['action']}: {log['details']}\n"

    return summary


def archive_interaction(user_text, ai_text):
    from sentinel.core.llm import LLMEngine
    if not user_text or not ai_text: return
    if len(user_text) < 10 and len(ai_text) < 10: return

    try:
        cfg = ConfigManager()
        brain = LLMEngine(cfg, verbose=False)

        prompt = (
            "Analyze interaction. Extract PERMANENT facts about user. "
            "Return JSON list of strings. If none, return [].\n\n"
            f"User: {user_text}\nAI: {ai_text}"
        )
        response = brain.query(prompt, [])
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            facts = json.loads(match.group(0))
            for fact in facts:
                store_fact("User", "context", fact, context="conversation_archive")
    except Exception:
        pass