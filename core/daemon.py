# core/daemon.py
import subprocess
import signal
import sys
import time
import requests
from flask import current_app

ollama_process = None

def start_ollama():
    global ollama_process
    print("🔒 Requesting Android Wake-Lock handles...")
    try:
        subprocess.run(["termux-wake-lock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Termux Wake-Lock established.")
    except Exception:
        print("⚠️ Failed to acquire system Wake-Lock interface.")

    print("🤖 Initializing local Ollama backend daemon...")
    try:
        ollama_process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        retries = 5
        # Fallback if config isn't read via context yet
        url = current_app.config.get("OLLAMA_URL", "http://localhost:11434/api/chat") if current_app else "http://localhost:11434/api/chat"
        base_url = url.split('/api')[0] + "/api/tags"
        
        while retries > 0:
            try:
                response = requests.get(base_url, timeout=1)
                if response.status_code == 200:
                    print("✅ Ollama backend listener is active.")
                    return
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1.5)
            retries -= 1
    except FileNotFoundError:
        print("❌ Error: 'ollama' binary not found.")
        sys.exit(1)

def cleanup_and_exit(signum, frame):
    global ollama_process
    print("\n🛑 Teardown sequence triggered...")
    try:
        subprocess.run(["termux-wake-unlock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    if ollama_process:
        ollama_process.terminate()  
        try:
            ollama_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            ollama_process.kill()  
    print("👋 Jarvis offline. Exiting safely.")
    sys.exit(0)

def init_signals():
    signal.signal(signal.SIGINT, cleanup_and_exit)   
    signal.signal(signal.SIGTERM, cleanup_and_exit)
