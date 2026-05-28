# database.py
import sqlite3
import os
from flask import g, current_app

def get_db_connection():
    """
    Creates or returns an existing thread-safe database connection 
    attached securely to the current application request context (g).
    """
    # Use Flask's 'g' object to ensure a thread doesn't share its connection with another request
    if 'db' not in g:
        # Pull DB file path directly out of our newly configured app engine settings
        db_file = current_app.config.get('DB_FILE', 'jarvis_chat.db') if current_app else "jarvis_chat.db"
        g.db = sqlite3.connect(db_file)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_db(e=None):
    """Safely tears down the request-locked connection when a route ends execution."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app=None):
    """Initializes the multi-tenant schema architecture inside the targeted database file."""
    # Fallback to direct resolution if executed outside active application loops
    db_file = app.config['DB_FILE'] if app else "jarvis_chat.db"
    
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # 1. Users Security Core
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Flexible Variable Overrides 
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                setting_key TEXT NOT NULL,
                setting_value TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(user_id, setting_key)
            )
        """)

        # 3. User-Scoped Conversational Sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, 
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_search_query TEXT DEFAULT '',
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Migration Safety Fallback: Ensure user_id column exists for legacy iterations
        try:
            cursor.execute("ALTER TABLE sessions ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;")
        except sqlite3.OperationalError:
            pass

        # 4. Message Content Layer
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                role TEXT,
                content TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
    print("💾 Robust database schema layers validated and locked.")
