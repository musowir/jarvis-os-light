#!/usr/bin/env python3
import json
import random
import requests
import threading
import subprocess
import signal
import sys
import time
from flask import Flask, Response, request, render_template, jsonify

import config
from database import init_db, get_db_connection
from system_actions import execute_system_activity
from search_engine import INITIAL_SEARCH_KEYWORDS, FOLLOWUP_SEARCH_KEYWORDS, internet_search

app = Flask(__name__)
init_db()

# Global variable to track the background Ollama daemon process
ollama_process = None

# ==========================================
# 🛠️ DEPENDENCY LIFECYCLE HOOKS
# ==========================================

def start_ollama():
    """Launches Ollama service in background and locks Termux CPU state active."""
    global ollama_process
    
    print("🔒 Requesting Android Wake-Lock handles to prevent deep sleep states...")
    try:
        subprocess.run(["termux-wake-lock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Termux Wake-Lock established. Background socket loops secured.")
    except Exception:
        print("⚠️ Failed to acquire system Wake-Lock interface.")

    print("🤖 Initializing local Ollama inference engine background daemon...")
    try:
        ollama_process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        retries = 5
        while retries > 0:
            try:
                response = requests.get(f"{config.OLLAMA_URL.split('/api')[0]}/api/tags", timeout=1)
                if response.status_code == 200:
                    print("✅ Ollama backend listener is active and attached.")
                    return
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1.5)
            retries -= 1
        print("⚠️ Ollama took a moment to bind. Port might be occupied or initializing.")
    except FileNotFoundError:
        print("❌ Error: 'ollama' binary not found. Please verify your Termux installation.")
        sys.exit(1)

def cleanup_and_exit(signum, frame):
    """Gracefully terminates background dependencies and releases wake-locks."""
    global ollama_process
    print("\n🛑 Teardown sequence triggered! Cleaning up active sockets...")
    
    try:
        print("🔓 Releasing Termux system Wake-Lock profile restraints...")
        subprocess.run(["termux-wake-unlock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Wake-Lock released successfully.")
    except Exception:
        pass

    if ollama_process:
        print("🔌 Terminating local background Ollama daemon...")
        ollama_process.terminate()  
        try:
            ollama_process.wait(timeout=3)
            print("💀 Ollama stopped successfully.")
        except subprocess.TimeoutExpired:
            ollama_process.kill()  
            print("⚡ Ollama forced closed.")
            
    print("👋 Jarvis OS Light framework offline. Exiting terminal shell safely.")
    sys.exit(0)


# Register POSIX signal handlers to capture environment termination events
signal.signal(signal.SIGINT, cleanup_and_exit)   # Catches manual Ctrl + C
signal.signal(signal.SIGTERM, cleanup_and_exit)  # Catches system level kills

# ==========================================
# 🔊 ORIGINAL VOICE WORKER IMPLEMENTATIONS
# ==========================================

def speak_worker(text):
    subprocess.run([
        "termux-tts-speak", "-e", config.TTS_ENGINE, "-l", config.TTS_LOCALE, "-s", "SYSTEM", text
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def speak(text):
    if text.strip():
        threading.Thread(target=speak_worker, args=(text,), daemon=True).start()

# ==========================================
# 🌐 ORIGINAL APP ROUTING LAYER
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sessions', methods=['GET'])
def get_sessions():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY id DESC")
        return jsonify([dict(r) for r in cursor.fetchall()])

@app.route('/sessions/new', methods=['POST'])
def new_session():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (title) VALUES ('New Chat Thread')")
        session_id = cursor.lastrowid
        conn.commit()
        return jsonify({"session_id": session_id})

@app.route('/sessions/delete', methods=['DELETE'])
def delete_session():
    session_id = request.args.get('session_id')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        return jsonify({"status": "success"})

@app.route('/history', methods=['GET'])
def get_history():
    session_id = request.args.get('session_id')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
        return jsonify([dict(r) for r in cursor.fetchall()])

@app.route('/stream')
def stream():
    user_prompt = request.args.get('prompt', '').strip()
    session_id = request.args.get('session_id')
    
    # 1. System Action Parsing Intercept
    intercepted, system_message = execute_system_activity(user_prompt)
    if intercepted:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO messages (session_id, role, content) VALUES (?, 'user', ?)", (session_id, user_prompt))
            cursor.execute("INSERT INTO messages (session_id, role, content) VALUES (?, 'assistant', ?)", (session_id, system_message))
            cursor.execute("SELECT title FROM sessions WHERE id = ?", (session_id,))
            if cursor.fetchone()[0] == "New Chat Thread":
                new_title = user_prompt[:22] + "..." if len(user_prompt) > 22 else user_prompt
                cursor.execute("UPDATE sessions SET title = ? WHERE id = ?", (new_title, session_id))
            conn.commit()
            
        def generate_system_reply():
            speak(system_message)
            yield f"data: {system_message}\n\n"
            yield "data: [DONE]\n\n"
        return Response(generate_system_reply(), mimetype='text/event-stream')

    # 2. Standard LLM Pipeline
    speak(random.choice(config.FILLER_PHRASES))
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (session_id, role, content) VALUES (?, 'user', ?)", (session_id, user_prompt))
        cursor.execute("SELECT title FROM sessions WHERE id = ?", (session_id,))
        if cursor.fetchone()[0] == "New Chat Thread":
            new_title = user_prompt[:22] + "..." if len(user_prompt) > 22 else user_prompt
            cursor.execute("UPDATE sessions SET title = ? WHERE id = ?", (new_title, session_id))
        cursor.execute("SELECT last_search_query FROM sessions WHERE id = ?", (session_id,))
        last_search_query = cursor.fetchone()[0]
        conn.commit()

    is_initial_search = any(word in user_prompt.lower() for word in INITIAL_SEARCH_KEYWORDS)
    is_followup_search = last_search_query and any(word in user_prompt.lower() for word in FOLLOWUP_SEARCH_KEYWORDS)
    should_search = is_initial_search or is_followup_search
    
    if should_search:
        search_query = user_prompt
        with get_db_connection() as conn:
            conn.cursor().execute("UPDATE sessions SET last_search_query = ? WHERE id = ?", (search_query, session_id))
            conn.commit()

    def generate():
        compiled_response = ""
        active_context = [{"role": "system", "content": config.SYSTEM_PROMPT}]
        
        # Load exact previous logs to stop hallucinated loops
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
            for row in cursor.fetchall():
                active_context.append({"role": row["role"], "content": row["content"]})

        if should_search:
            yield f"Pulling details from system search engines...\n\n"
            web_context = internet_search(user_prompt)
            execution_prompt = f"Live updates context: {web_context}\n\nUsing this structural real-time data, reply to: '{user_prompt}'."
            # Swap latest user input slice for the enriched version
            if active_context and active_context[-1]["role"] == "user":
                active_context[-1]["content"] = execution_prompt

        payload = {
            "model": config.MODEL,
            "messages": active_context,
            "stream": True,
            "options": {"temperature": 0.4, "num_ctx": 4096, "num_thread": config.CPU_THREADS},
        }

        try:
            # Extended fallback timeout window to avoid "Connection lost" faults
            resp = requests.post(config.OLLAMA_URL, json=payload, stream=True, timeout=45)
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    content = chunk.get("message", {}).get("content", "")
                    compiled_response += content
                    yield f"data: {content}\n\n"
                    
            speak(compiled_response)
            with get_db_connection() as conn:
                conn.cursor().execute("INSERT INTO messages (session_id, role, content) VALUES (?, 'assistant', ?)", (session_id, compiled_response))
                conn.commit()
        except Exception as e:
            yield f"data: Connection to engine backend delayed. ({str(e)})\n\n"
        yield "data: [DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    # Initialize background process before opening network port bounds
    start_ollama()
    
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)

