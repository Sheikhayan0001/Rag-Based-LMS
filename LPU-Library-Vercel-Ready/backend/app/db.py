import json
import psycopg
from psycopg.rows import dict_row
from .config import settings

def connect():
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured. Connect a Postgres database in Vercel and add DATABASE_URL.")
    return psycopg.connect(settings.database_url, row_factory=dict_row, connect_timeout=8)

def init_db():
    with connect() as con:
        con.execute("CREATE EXTENSION IF NOT EXISTS vector")
        con.execute("""CREATE TABLE IF NOT EXISTS library_chunks (
            id TEXT PRIMARY KEY, content TEXT NOT NULL, metadata JSONB NOT NULL, embedding vector(1536) NOT NULL
        )""")
        con.execute("CREATE INDEX IF NOT EXISTS library_chunks_metadata_idx ON library_chunks USING GIN (metadata)")
        con.execute("""CREATE TABLE IF NOT EXISTS chat_messages (
            id BIGSERIAL PRIMARY KEY, conversation_id TEXT NOT NULL, role TEXT NOT NULL,
            content TEXT NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW()
        )""")
        con.execute("CREATE INDEX IF NOT EXISTS chat_messages_conversation_idx ON chat_messages(conversation_id, id)")

def chunk_count():
    with connect() as con:
        return con.execute("SELECT COUNT(*) AS n FROM library_chunks").fetchone()["n"]

def add_message(conversation_id: str, role: str, content: str):
    with connect() as con:
        con.execute("INSERT INTO chat_messages(conversation_id,role,content) VALUES (%s,%s,%s)", (conversation_id,role,content))

def get_messages(conversation_id: str):
    with connect() as con:
        rows=con.execute("SELECT role,content,created_at FROM chat_messages WHERE conversation_id=%s ORDER BY id",(conversation_id,)).fetchall()
        return [{"role":r["role"],"content":r["content"],"created_at":r["created_at"].isoformat()} for r in rows]

def delete_conversation(conversation_id: str):
    with connect() as con:
        con.execute("DELETE FROM chat_messages WHERE conversation_id=%s",(conversation_id,))
