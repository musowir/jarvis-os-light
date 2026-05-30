# blueprints/chat/routes.py
import json
import random
import re
import requests
from flask import Blueprint, Response, request, jsonify, current_app
from database import get_db_connection
from blueprints.auth.routes import jwt_required
from core.voice import speak
from core.search_engine import web_search
from core.system_actions import handle_system_action
from core.parameter_binder import bind_session_metadata, fetch_active_parameters

chat_bp = Blueprint('chat', __name__)

# --- DEFENSIVE INTENT & SAFETY UTILITIES ---
def detect_search_intent(prompt: str) -> bool:
    """Scans the prompt globally for local context or explicit search terms."""
    clean = prompt.lower()
    keywords = ["search", "google", "look up", "check for", "malappuram", "munduparamba", "kerala", "district"]
    return any(kw in clean for kw in keywords)

def extract_search_query(prompt: str) -> str:
    """Cleans up the user prompt to pass a high-quality query to the search engine."""
    return re.sub(r'^(google|search|look up|please search for|check for)\s+', '', prompt, flags=re.IGNORECASE).strip()

def contains_refusal_hallucination(response_text: str) -> bool:
    """Detects if the over-aligned model triggered an artificial refusal pattern."""
    clean = response_text.lower()
    refusal_patterns = [
        r"i don't have the capability to perform web searches",
        r"cannot access the internet",
        r"unable to browse",
        r"please confirm if there's a specific topic",
        r"accurate information"
    ]
    return any(re.search(pattern, clean) for pattern in refusal_patterns)
# --------------------------------------------

@chat_bp.route('/sessions', methods=['GET'])
@jwt_required
def get_sessions(current_user_id):
    """Retrieve all chat sessions belonging exclusively to the authenticated user."""
    db = get_db_connection()
    cursor = db.cursor()
    sessions = cursor.execute(
        "SELECT id, user_id, title, history_summary, last_search_query FROM sessions WHERE user_id = ? ORDER BY id DESC", 
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

    if session_id_raw == 'null' or not session_id_raw:
        summary_title = prompt[:24] + "..." if len(prompt) > 24 else prompt
        cursor.execute(
            "INSERT INTO sessions (user_id, title) VALUES (?, ?)", 
            (current_user_id, summary_title)
        )
        allocated_session_id = cursor.lastrowid
        db.commit()
    else:
        allocated_session_id = int(session_id_raw)
        valid = cursor.execute(
            "SELECT id FROM sessions WHERE id = ? AND user_id = ?", 
            (allocated_session_id, current_user_id)
        ).fetchone()
        if not valid:
            return jsonify({"error": "Thread execution routing mismatch"}), 403

    handled, message_feedback = handle_system_action(prompt)
    
    # --- UPGRADED WEB SEARCH GUARDRAIL DETECTOR ---
    search_triggered = False
    search_context = ""
    user_is_correcting = any(word in prompt.lower() for word in ["false", "wrong", "mistake", "lying", "not true", "incorrect"])

    if not handled:
        if detect_search_intent(prompt):
            search_triggered = True
            search_query = extract_search_query(prompt)
            search_context = web_search(search_query)
        elif user_is_correcting:
            search_triggered = True
            last_msg = cursor.execute(
                "SELECT content FROM messages WHERE session_id = ? AND role = 'user' ORDER BY id DESC LIMIT 1",
                (allocated_session_id,)
            ).fetchone()
            search_query = last_msg['content'] if last_msg else prompt
            search_context = f"[USER CORRECTION CRITICAL DATA]: The user flagged the last answer as false. Verify info for: {search_query}.\n" + web_search(search_query)

        if search_triggered:
            cursor.execute(
                "UPDATE sessions SET last_search_query = ? WHERE id = ?", 
                (search_query, allocated_session_id)
            )
            db.commit()
    # -----------------------------------------------

    ctx_app = current_app._get_current_object()

    def generate():
        nonlocal handled, message_feedback
        
        with ctx_app.app_context():
            db_thread = get_db_connection()
            cursor_thread = db_thread.cursor()

            yield f"id: {allocated_session_id}\n"
            yield f"data: \n\n"

            speak(random.choice(current_app.config['FILLER_PHRASES']))

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

            session_meta = cursor_thread.execute(
                "SELECT history_summary FROM sessions WHERE id = ?", (allocated_session_id,)
            ).fetchone()
            
            rolling_summary = dict(session_meta).get('history_summary') if session_meta else ""
            if rolling_summary is None:
                rolling_summary = ""

            bind_session_metadata(allocated_session_id, prompt)
            environmental_context = fetch_active_parameters(allocated_session_id)

            recent_rows = cursor_thread.execute(
                "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT 10", 
                (allocated_session_id,)
            ).fetchall()
            
            recent_messages = [dict(row) for row in reversed(recent_rows)]

            system_instruction = current_app.config['SYSTEM_PROMPT']
            
            # Anti-alignment override injection
            system_instruction += (
                "\n\nYou have direct access to the latest conversation history below. "
                "If the user says 'false', 'wrong', or points out a hallucination, you are explicitly authorized "
                "to acknowledge it and correct yourself using the search results provided. Do not use an AI safety template response."
            )

            if rolling_summary:
                system_instruction += f"\n\n[Condensed summary vector of older conversation elements]:\n{rolling_summary}"
            if environmental_context:
                system_instruction += f"\n\n[Active Device Environment Metadata]:\n{environmental_context}"

            active_context = [{"role": "system", "content": system_instruction}]
            for msg in recent_messages:
                active_context.append({"role": msg['role'], "content": msg['content']})

            if search_triggered:
                active_context.append({
                    "role": "user", 
                    "content": f"Context data from live Google query:\n{search_context}\n\nQuery: {prompt}"
                })
            else:
                active_context.append({"role": "user", "content": prompt})

            ollama_payload = {
                "model": current_app.config['MODEL'],
                "messages": active_context,
                "stream": True,
                "options": {
                    "temperature": 0.3, 
                    "num_ctx": 4048, 
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
                            yield f"data: {content}\n\n"
                            
            except Exception as e:
                error_feedback = f"\n[Backend Connection Error: {str(e)}]"
                full_response_text += error_feedback
                yield f"data: {error_feedback}\n\n"

            # --- ALIGNMENT REFUSAL RECOVERY OVERRIDE ---
            if search_triggered and contains_refusal_hallucination(full_response_text):
                correction_prompt = (
                    "Correction: You are allowed to answer this. Do not use a pre-programmed apology template. "
                    "Use the search context data directly to state the precise facts."
                )
                ollama_payload["messages"].append({"role": "user", "content": correction_prompt})
                ollama_payload["stream"] = False
                try:
                    corrected_res = requests.post(current_app.config['OLLAMA_URL'], json=ollama_payload, timeout=30)
                    if corrected_res.status_code == 200:
                        full_response_text = "[Guardrail Override]: " + corrected_res.json().get("message", {}).get("content", "").strip()
                        yield f"data: \n\n"
                        yield f"data: {full_response_text}\n\n"
                except Exception:
                    pass
            # ---------------------------------------------

            cursor_thread.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, 'user', ?)", 
                (allocated_session_id, prompt)
            )
            cursor_thread.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, 'assistant', ?)", 
                (allocated_session_id, full_response_text)
            )
            db_thread.commit()

            total_count = cursor_thread.execute(
                "SELECT COUNT(*) as count FROM messages WHERE session_id = ?", (allocated_session_id,)
            ).fetchone()['count']

            if total_count > 12:
                excess_rows = cursor_thread.execute(
                    "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC LIMIT ?",
                    (allocated_session_id, total_count - 10)
                ).fetchall()
                
                try:
                    from core.memory_manager import summarize_old_interactions
                    new_summary_chunk = summarize_old_interactions(
                        [dict(r) for r in excess_rows],
                        ollama_url=current_app.config['OLLAMA_URL'],
                        model_name=current_app.config['MODEL']
                    )
                    if new_summary_chunk:
                        updated_summary = f"{rolling_summary}\n- {new_summary_chunk}".strip()
                        cursor_thread.execute(
                            "UPDATE sessions SET history_summary = ? WHERE id = ?",
                            (updated_summary, allocated_session_id)
                        )
                        db_thread.commit()
                except Exception as e:
                    print(f"⚠️ [Memory Manager Sync Delay] System cores busy, skipping frame: {str(e)}")

            yield "data: [DONE]\n\n"
            speak(full_response_text)

    return Response(generate(), mimetype='text/event-stream')