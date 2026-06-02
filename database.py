# ==============================================================================
# SYSTEM INSTANCE CODE BASE : JARVIS CORE FRAMEWORK
# MODULE          : database
# DESCRIPTION     : Establishes context-bound database connection managers and
#                   validates multi-tenant schema tables, migrations, and cascade rules.
# COORDINATES     : Layer-1 Main Application Bootstrap
# SUBSYSTEM       : Relational SQLite Storage Engine
# ==============================================================================

import sqlite3
from flask import g, current_app

def get_db_connection():
    """
    Creates or returns an existing thread-safe database connection 
    attached securely to the current application request context (g).
    """
    if 'db' not in g:
        db_file = current_app.config.get('DB_FILE', 'jarvis_chat.db') if current_app else "jarvis_chat.db"
        g.db = sqlite3.connect(db_file)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Closes the current request-bound database connection cleanly."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app=None):
    """Initializes the multi-tenant schema architecture inside the targeted database file."""
    db_file = app.config['DB_FILE'] if app else "jarvis_chat.db"
    
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        
        # 1. Users Security Container Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Session Context Metadata Index Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                last_search_query TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # --- PHASE 2 MEMORY INTEGRATION MIGRATION ENGINE ---
        try:
            cursor.execute("ALTER TABLE sessions ADD COLUMN history_summary TEXT DEFAULT '';")
        except sqlite3.OperationalError:
            pass
        # --- END PHASE 2 MEMORY INTEGRATION MIGRATION ENGINE ---

        # 4. Message Content Layer
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)

        # 5. Session Environmental Parameter Table (Phase 2)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                param_key TEXT NOT NULL,
                param_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                UNIQUE(session_id, param_key)
            )
        """)

        # 6. Independent Hardware & System Telemetry Log (Phase 2 Cleanups)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hardware_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                action_prompt TEXT NOT NULL,
                execution_feedback TEXT NOT NULL,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
    print("💾 Robust database schema layers validated and locked.")
