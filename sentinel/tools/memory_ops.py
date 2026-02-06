import sqlite3
import datetime
import chromadb
import uuid
import json
import re
import gc
from chromadb.utils import embedding_functions
from sentinel.core.config import ConfigManager
from sentinel.paths import DB_PATH, VECTOR_PATH

# Global references
chroma_client = None
collection = None


def _get_sql_conn():
    """
    Returns a connection. Use with context manager for safety.
    """
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_chroma():
    """Initializes ChromaDB with safe re-entry."""
    global chroma_client, collection

    # If already initialized, skip
    if collection is not None:
        return

    try:
        chroma_client = chromadb.PersistentClient(path=str(VECTOR_PATH))

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
    except Exception as e:
        print(f"❌ ChromaDB Init Error: {e}")
        chroma_client = None


def ensure_chroma():
    if collection is None:
        init_chroma()


def store_fact(subject, predicate, obj, context="user_defined"):
    ensure_chroma()
    if not collection:
        return "❌ Vector DB unavailable."

    fact_text = f"{subject} {predicate} {obj}"
    mem_id = str(uuid.uuid4())
    full_text = f"{fact_text}. Context: {context}"

    collection.add(
        documents=[full_text],
        metadatas=[{"subject": subject, "type": "fact", "context": context}],
        ids=[mem_id]
    )

    importance = 5

    with _get_sql_conn() as conn:
        conn.execute("INSERT INTO metadata (id, importance) VALUES (?, ?)", (mem_id, importance))

    return f"🧠 Memory Stored: {fact_text}"


def delete_fact(subject=None, predicate=None):
    """
    Deletes facts using efficient metadata filtering.
    """
    ensure_chroma()
    if not collection: return "❌ Vector DB unavailable."

    where_clause = {}
    if subject:
        where_clause["subject"] = subject

    try:
        if not where_clause:
            return "❌ Safety: Please provide at least a subject to delete."

        collection.delete(where=where_clause)
        return f"🗑️ Deleted memories matching: {where_clause}"

    except Exception as e:
        return f"❌ Delete error: {e}"


def retrieve_relevant_context(query, limit=5):
    ensure_chroma()
    if not collection: return ""

    try:
        results = collection.query(query_texts=[query], n_results=10)
    except Exception:
        return ""

    if not results['ids'] or not results['ids'][0]:
        return ""

    found_ids = results['ids'][0]
    found_texts = results['documents'][0]
    found_distances = results['distances'][0]

    placeholders = ','.join(['?'] * len(found_ids))
    with _get_sql_conn() as conn:
        rows = conn.execute(f"SELECT * FROM metadata WHERE id IN ({placeholders})", found_ids).fetchall()
        conn.execute(f"UPDATE metadata SET last_accessed = CURRENT_TIMESTAMP WHERE id IN ({placeholders})", found_ids)

    meta_map = {row['id']: dict(row) for row in rows}
    scored_memories = []

    for i, mem_id in enumerate(found_ids):
        text = found_texts[i]
        relevance = 1.0 - (found_distances[i] if found_distances[i] < 1.0 else 1.0)

        if relevance > 0.3:
            scored_memories.append((relevance, text))

    scored_memories.sort(key=lambda x: x[0], reverse=True)
    top_picks = scored_memories[:limit]

    if not top_picks:
        return "No relevant memories found."

    return "🧠 **Relevant Context:**\n" + "\n".join([f"- {x[1]}" for x in top_picks])


def init_memory():
    """Creates the SQLite tables if missing."""
    with _get_sql_conn() as conn:
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


init_memory()


def log_activity(action, details):
    try:
        with _get_sql_conn() as conn:
            conn.execute("INSERT INTO logs (action, details) VALUES (?, ?)", (action, details))
    except:
        pass


def reflect_on_day(date_str=None):
    """
    Retrieves activity logs for a specific day.
    Required by registry.py and cognitive.py for Daily Briefings.
    """
    if not date_str:
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    try:
        with _get_sql_conn() as conn:
            c = conn.execute('''
                SELECT time(timestamp) as t, action, details 
                FROM logs 
                WHERE date(timestamp) = ? 
                ORDER BY timestamp ASC
            ''', (date_str,))
            logs = c.fetchall()

        if not logs:
            return f"No activity recorded for {date_str}."

        summary = f"📅 **Activity Log for {date_str}:**\n"
        for log in logs:
            summary += f"[{log['t']}] {log['action']}: {log['details']}\n"

        return summary

    except Exception as e:
        return f"❌ Error reflecting on day: {e}"

def archive_interaction(user_text, ai_text):
    """
    Extracts facts from conversation and saves them.
    Lazy imports LLM to avoid circular dependency.
    """
    if not user_text or not ai_text: return
    if len(user_text) < 10: return  # Ignore short greetings

    try:
        from sentinel.core.llm import LLMEngine
        cfg = ConfigManager()
        brain = LLMEngine(cfg, verbose=False)

        prompt = (
            "Extract 1-2 permanent facts about the user from this chat.\n"
            "Return ONLY a JSON list of strings. Example: [\"User lives in Boston\"]\n"
            "If no facts, return [].\n\n"
            f"User: {user_text}\nAI: {ai_text}"
        )

        response = brain.query(prompt, [])

        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            facts = json.loads(match.group(0))
            for fact in facts:
                if isinstance(fact, str):
                    store_fact("User", "revealed", fact, context="chat_archive")
    except Exception:
        pass


def teardown():
    """
    Releases database locks (ChromaDB & SQLite) to allow safe deletion.
    """
    global chroma_client, collection
    chroma_client = None
    collection = None
    gc.collect()