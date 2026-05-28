# blueprints/chat/routes.py
import json
import random
import requests
from flask import Blueprint, Response, request, jsonify, current_app
from database import get_db_connection
from blueprints.auth.routes import jwt_required
from core.voice import speak
from core.search_engine import web_search
from core.system_actions import handle_system_action

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/sessions', methods=['GET'])
@jwt_required
def get_sessions(current_user_id):
    """Retrieve all chat sessions belonging exclusively to the authenticated user."""
    db = get_db_connection()
    cursor = db.cursor()
    sessions = cursor.execute(
        "SELECT * FROM sessions WHERE user_id = ? ORDER BY id DESC", 
        (current_user_id,)
    ).fetchall()
    
    return jsonify([dict(row) for row in sessions])

@chat_bp.route('/history', methods=['GET'])
@jwt_required
def get_history(current_user_id):
    """Fetch complete message history for an authorized session container."""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({"error": "Session ID required"}), 400

    db = get_db_connection()
    cursor = db.cursor()
    
    # Security cross-check: Ensure the session actually belongs to this user
    session = cursor.execute(
        "SELECT id FROM sessions WHERE id = ? AND user_id = ?", 
        (session_id, current_user_id)
    ).fetchone()
    
    if not session:
        return jsonify({"error": "Unauthorized session access sequence"}), 403

    messages = cursor.execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC", 
        (session_id,)
    ).fetchall()
    
    return jsonify([dict(row) for row in messages])

@chat_bp.route('/sessions/delete', methods=['DELETE'])
@jwt_required
def delete_session(current_user_id):
    """Permanently clear out a conversation thread log."""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({"error": "Missing parameter parameters"}), 400

    db = get_db_connection()
    cursor = db.cursor()
    
    # Security cross-check: Ensure the session belongs to this user before dropping it
    session = cursor.execute(
        "SELECT id FROM sessions WHERE id = ? AND user_id = ?", 
        (session_id, current_user_id)
    ).fetchone()
    
    if not session:
        return jsonify({"error": "Unauthorized teardown request"}), 403

    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    db.commit()
    return jsonify({"status": "success", "message": "Thread safely truncated"})

@chat_bp.route('/stream', methods=['GET'])
@jwt_required
def stream(current_user_id):
    """The central message processing pipeline and inference event-stream generator."""
    prompt = request.args.get('prompt', '').strip()
    session_id_raw = request.args.get('session_id', 'null')

    if not prompt:
        return jsonify({"error": "Prompt field blank"}), 400

    db = get_db_connection()
    cursor = db.cursor()
    allocated_session_id = None

    # Handle transient zero-state generation safely
    if session_id_raw == 'null' or not session_id_raw:
        # Dynamically title thread based on the first prompt segment
        summary_title = prompt[:24] + "..." if len(prompt) > 24 else prompt
        cursor.execute(
            "INSERT INTO sessions (user_id, title) VALUES (?, ?)", 
            (current_user_id, summary_title)
        )
        allocated_session_id = cursor.lastrowid
        db.commit()
    else:
        allocated_session_id = int(session_id_raw)
        # Re-verify owner ownership constraints on existing tracking loops
        valid = cursor.execute(
            "SELECT id FROM sessions WHERE id = ? AND user_id = ?", 
            (allocated_session_id, current_user_id)
        ).fetchone()
        if not valid:
            return jsonify({"error": "Thread execution routing mismatch"}), 403

    # Fire off Android voice system worker safely via active config lists
    speak(random.choice(current_app.config['FILLER_PHRASES']))

    # System parsing layer checking for local terminal execution requirements
    handled, message_feedback = handle_system_action(prompt)
    
    # Intercept web search requests explicitly
    search_triggered = False
    search_context = ""
    if not handled and prompt.lower().startswith("search "):
        search_triggered = True
        search_query = prompt[7:].strip()
        search_context = web_search(search_query)
        cursor.execute(
            "UPDATE sessions SET last_search_query = ? WHERE id = ?", 
            (search_query, allocated_session_id)
        )
        db.commit()

    # CRITICAL: Capture the raw application runtime context proxy object before sliding into the generator
    ctx_app = current_app._get_current_object()

    def generate():
        nonlocal handled, message_feedback
        
        # Explicitly mount the application context boundary layer inside the thread loop
        with ctx_app.app_context():
            db_thread = get_db_connection()
            cursor_thread = db_thread.cursor()

            # Render connection assignments instantly to client UI bindings
            yield f"id: {allocated_session_id}\n"
            yield f"data: \n\n"

            if handled:
                cursor_thread.execute(
                    "INSERT INTO messages (session_id, role, content) VALUES (?, 'user', ?)", 
                    (allocated_session_id, prompt)
                )
                cursor_thread.execute(
                    "INSERT INTO messages (session_id, role, content) VALUES (?, 'assistant', ?)", 
                    (allocated_session_id, message_feedback)
                )
                db_thread.commit()
                
                yield f"data: {message_feedback}\n\n"
                yield "data: [DONE]\n\n"
                speak(message_feedback)
                return

            # Query past parameters up to 12 cycles back to maintain processing memory blocks
            history_rows = cursor_thread.execute(
                "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC LIMIT 12", 
                (allocated_session_id,)
            ).fetchall()

            active_context = [{"role": "system", "content": current_app.config['SYSTEM_PROMPT']}]
            for row in history_rows:
                active_context.append({"role": dict(row)['role'], "content": dict(row)['content']})

            if search_triggered:
                active_context.append({
                    "role": "user", 
                    "content": f"Context data from search engine:\n{search_context}\n\nQuery: {prompt}"
                })
            else:
                active_context.append({"role": "user", "content": prompt})

            # Process inference stream via active configuration settings
            ollama_payload = {
                "model": current_app.config['MODEL'],
                "messages": active_context,
                "stream": True,
                "options": {
                    "temperature": 0.4, 
                    "num_ctx": 4096, 
                    "num_thread": current_app.config['CPU_THREADS']
                }
            }

            full_response_text = ""
            try:
                response = requests.post(
                    current_app.config['OLLAMA_URL'], 
                    json=ollama_payload, 
                    stream=True, 
                    timeout=30
                )
                
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode('utf-8'))
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            full_response_text += content
                            # Escape newlines for Server-Sent Events structure
                            yield f"data: {content.replace('\n', '\\n')}\n\n"
                            
            except Exception as e:
                error_feedback = f"\n[Backend Connection Error: {str(e)}]"
                full_response_text += error_feedback
                yield f"data: {error_feedback}\n\n"

            # Log conversation elements cleanly to SQLite layers
            cursor_thread.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, 'user', ?)", 
                (allocated_session_id, prompt)
            )
            cursor_thread.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, 'assistant', ?)", 
                (allocated_session_id, full_response_text)
            )
            db_thread.commit()

            yield "data: [DONE]\n\n"
            speak(full_response_text)

    return Response(generate(), mimetype='text/event-stream')
