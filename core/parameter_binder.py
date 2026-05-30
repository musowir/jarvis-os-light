# core/parameter_binder.py
import datetime
import sqlite3

def bind_session_metadata(session_id: int, prompt: str) -> dict:
    """
    Scans incoming tokens for rapid environmental updates and stores them 
    cleanly in the database with strict type casting and error barriers.
    """
    inferred_metadata = {}
    clean_prompt = prompt.lower()
    
    inferred_metadata["last_interaction_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if "timezone" in clean_prompt or "time in" in clean_prompt:
        inferred_metadata["tracked_timezone"] = "UTC+5:30"
        
    try:
        from flask import current_app
        db_file = current_app.config.get('DB_FILE', 'jarvis_chat.db') if current_app else "jarvis_chat.db"
        
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            for key, val in inferred_metadata.items():
                cursor.execute("""
                    INSERT INTO session_parameters (session_id, param_key, param_value)
                    VALUES (?, ?, ?)
                    ON CONFLICT(session_id, param_key) DO UPDATE SET 
                        param_value = excluded.param_value,
                        updated_at = CURRENT_TIMESTAMP
                """, (session_id, key, val))
            conn.commit()
    except Exception as e:
        print(f"ℹ️ [Parameter Binder Warning] Background registration skipped: {str(e)}")
        
    return inferred_metadata

def fetch_active_parameters(session_id: int) -> str:
    """Retrieves all bound parameters, explicitly forcing primitive string extraction."""
    try:
        from flask import current_app
        db_file = current_app.config.get('DB_FILE', 'jarvis_chat.db') if current_app else "jarvis_chat.db"
        
        with sqlite3.connect(db_file) as conn:
            conn.row_factory = None 
            cursor = conn.cursor()
            rows = cursor.execute(
                "SELECT param_key, param_value FROM session_parameters WHERE session_id = ?", 
                (session_id,)
            ).fetchall()
            if not rows:
                return ""
            return "\n".join([f"- Current {row[0]}: {row[1]}" for row in rows])
    except Exception as e:
        print(f"ℹ️ [Parameter Fetch Warning] Extraction bypassed: {str(e)}")
        return ""
