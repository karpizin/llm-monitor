import sqlite3
import os

DB_NAME = os.getenv("DB_PATH", "monitor.db")

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table for models metadata
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS models (
        id TEXT PRIMARY KEY,
        name TEXT,
        context_length INTEGER,
        is_vlm BOOLEAN,
        is_free BOOLEAN,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
    """)
    
    # Table for health checks
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_id TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status_code INTEGER,
        latency_ms INTEGER,
        response_text TEXT,
        success BOOLEAN,
        error_msg TEXT,
        FOREIGN KEY (model_id) REFERENCES models (id)
    )
    """)
    
    conn.commit()
    conn.close()
    print(f"Database {DB_NAME} initialized.")

def save_models(models_list):
    conn = get_connection()
    cursor = conn.cursor()
    
    for m in models_list:
        cursor.execute("""
        INSERT INTO models (id, name, context_length, is_vlm, is_free)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            context_length=excluded.context_length,
            is_vlm=excluded.is_vlm,
            is_free=excluded.is_free,
            last_seen=CURRENT_TIMESTAMP,
            is_active=1
        """, (m['id'], m['name'], m['context'], m['is_vlm'], True))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
