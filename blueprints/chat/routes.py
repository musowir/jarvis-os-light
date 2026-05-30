# blueprints/chat/routes.py
import json
import random
import re
import requests
import datetime
from flask import Blueprint, Response, request, jsonify, current_app
from database import get_db_connection
from blueprints.auth.routes import jwt_required
from core.search_engine import web_search, detect_search_intent, extract_search_query
from core.hardware_automation import handle_hardware_intent, speak
from core.markdown_cleaner import strip_markdown
from core.query_expansion import expand_search_query

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/sessions', methods=['GET'])
@jwt_required
def get_sessions(current_user_id):
    """Retrieves all active message thread profiles mapped to the authenticated client."""
    db = get_db_connection()
    cursor = db.cursor()
    sessions = cursor.execute(
        "SELECT id, title, created_at FROM sessions WHERE user_id = ? ORDER BY id DESC",
        (current_user_id,)
    ).fetchall()
    return jsonify([dict(row) for row in sessions])

@chat_bp.route('/history', methods=['GET'])
@jwt_required
def get_history(current_user_id):
    """Sinks historic conversation data packages back to the frontend on thread swapping requests."""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({"error": "Missing profile tracking context parameter"}), 400
        
    db = get_db_connection()
    cursor = db.cursor()
    messages = cursor.execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    ).fetchall()
    return jsonify([dict(row) for row in messages])

@chat_bp.route('/telemetry/logs', methods=['GET'])
@jwt_required
def get_telemetry_logs(current_user_id):
    """Pulls execution footprints left behind by peripheral matrix component automation requests."""
    db = get_db_connection()
    cursor = db.cursor()
    
    logs = cursor.execute("""
        SELECT h.action_prompt, h.execution_feedback, 
               datetime(h.executed_at, 'localtime') as executed_at
        FROM hardware_logs h
        JOIN sessions s ON h.session_id = s.id
        WHERE s.user_id = ?
        ORDER BY h.id DESC LIMIT 30
    """, (current_user_id,)).fetchall()
    
    return jsonify([dict(row) for row in logs])

@chat_bp.route('/sessions/delete', methods=['DELETE'])
@jwt_required
def delete_session(current_user_id):
    """Destroys an isolated chat history array record without resetting global user schema fields."""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({"error": "Missing target record reference ID"}), 400
        
    db = get_db_connection()
    cursor = db.cursor()
    
    session = cursor.execute("SELECT id FROM sessions WHERE id = ? AND user_id = ?", (session_id, current_user_id)).fetchone()
    if not session:
        return jsonify({"error": "Resource reference lookup unauthorized or non-existent"}), 403
        
    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM hardware_logs WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    db.commit()
    return jsonify({"status": "success", "message": "Thread safely truncated"})

@chat_bp.route('/stream', methods=['POST'])
@jwt_required
def stream(current_user_id):
    """The central message processing pipeline and inference event-stream generator."""
    payload_data = request.get_json() or {}
    prompt = payload_data.get('prompt', '').strip()
    session_id_raw = payload_data.get('session_id', 'null')

    if not prompt:
        return jsonify({"error": "Prompt field blank"}), 400

    db = get_db_connection()
    cursor = db.cursor()

    allocated_session_id = None
    if session_id_raw != 'null' and session_id_raw is not None:
        allocated_session_id = int(session_id_raw)
    else:
        generated_title = prompt[:32] + "..." if len(prompt) > 32 else prompt
        cursor.execute(
            "INSERT INTO sessions (user_id, title) VALUES (?, ?)",
            (current_user_id, generated_title)
        )
        db.commit()
        allocated_session_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, 'user', ?)",
        (allocated_session_id, prompt)
    )
    db.commit()

    handled, message_feedback = handle_hardware_intent(prompt)
    
    search_triggered = False
    search_query = ""
    user_is_correcting = any(word in prompt.lower() for word in ["false", "wrong", "mistake", "lying", "not true", "incorrect"])

    if not handled:
        if detect_search_intent(prompt):
            search_triggered = True
            raw_query = extract_search_query(prompt)
            search_query = expand_search_query(raw_query)
        elif user_is_correcting:
            search_triggered = True
            last_msg = cursor.execute(
                "SELECT content FROM messages WHERE session_id = ? AND role = 'assistant' ORDER BY id DESC LIMIT 1",
                (allocated_session_id,)
            ).fetchone()
            raw_query = last_msg['content'] if last_msg else prompt
            search_query = expand_search_query(raw_query)

    ctx_app = current_app._get_current_object()

    def generate():
        nonlocal handled, message_feedback, search_triggered, search_query
        
        with ctx_app.app_context():
            db_thread = get_db_connection()
            cursor_thread = db_thread.cursor()

            yield f"id: {allocated_session_id}\n"
            yield f"data: \n\n"

            search_context = ""
            if search_triggered and not handled:
                yield f"data: [SYSTEM_SEARCHING]\n\n"
                
                if user_is_correcting:
                    raw_search = web_search(search_query)
                    search_context = f"[USER CORRECTION CRITICAL DATA]: The user flagged the last answer as false. Verify info for: {search_query}.\n" + strip_markdown(raw_search)
                else:
                    raw_search = web_search(search_query)
                    search_context = strip_markdown(raw_search)
                
                cursor_thread.execute(
                    "UPDATE sessions SET last_search_query = ? WHERE id = ?", 
                    (search_query, allocated_session_id)
                )
                db_thread.commit()

            speak(random.choice(current_app.config['FILLER_PHRASES']))

            if handled:
                cursor_thread.execute("""
                    INSERT INTO hardware_logs (session_id, action_prompt, execution_feedback) 
                    VALUES (?, ?, ?)
                """, (allocated_session_id, prompt, message_feedback))
                db_thread.commit()
                
                yield f"data: [System Action]: {message_feedback}\n\n"
                yield "data: [DONE]\n\n"
                speak(message_feedback)
                return

            recent_rows = cursor_thread.execute(
                "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT 10",
                (allocated_session_id,)
            ).fetchall()
            
            recent_messages = [dict(row) for row in reversed(recent_rows)]

            current_timestamp = datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
            system_instruction = current_app.config['SYSTEM_PROMPT']
            system_instruction += f"\n\n[CURRENT EXECUTABLE SYSTEM ENVIRONMENT TIMESTAMP]: {current_timestamp}"
            
            system_instruction += (
                "\n\nYou have direct access to the latest conversation history below. "
                "If the user says 'false', 'wrong', or points out a hallucination, you are explicitly authorized "
                "to completely overturn your previous assumptions based on the live verified search records supplied below."
            )

            payload = {
                "model": current_app.config['OLLAMA_MODEL'],
                "messages": [
                    {"role": "system", "content": system_instruction},
                    *recent_messages
                ],
                "stream": True
            }

            if search_context:
                payload["messages"].append({"role": "system", "content": f"[LIVE WEB SEARCH VERIFIED RESULTS]:\n{search_context}"})

            try:
                ollama_res = requests.post(
                    f"{current_app.config['OLLAMA_BASE_URL']}/api/chat",
                    json=payload,
                    timeout=45,
                    stream=True
                )
                
                full_response_text = ""
                for line in ollama_res.iter_lines():
                    if line:
                        chunk = json.loads(line.decode('utf-8'))
                        content_token = chunk.get('message', {}).get('content', '')
                        full_response_text += content_token
                        yield f"data: {content_token}\n\n"

                cursor_thread.execute(
                    "INSERT INTO messages (session_id, role, content) VALUES (?, 'assistant', ?)",
                    (allocated_session_id, full_response_text)
                )
                db_thread.commit()
                
                yield "data: [DONE]\n\n"
                speak(full_response_text)

            except Exception as e:
                yield f"data: [Pipeline Error: {str(e)}]\n\n"
                yield "data: [DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream')
