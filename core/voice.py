# core/voice.py
import subprocess
import threading
from flask import current_app

def _execute_tts(text: str, engine: str, locale: str):
    """Internal system call to fire Termux TTS hardware engines safely with configuration flags."""
    try:
        clean_text = text.replace('"', '').replace("'", "")
        subprocess.run(
            ["termux-tts-speak", "-e", engine, "-l", locale, clean_text], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            timeout=10 
        )
    except Exception:
        pass

def speak(text: str):
    """
    Spits out audio responses asynchronously. Completely non-blocking 
    to ensure local thread loops never hang the user interface.
    """
    if not text or not text.strip():
        return
        
    # Safely extract voice profile settings within the safe application context window
    try:
        engine = current_app.config.get("TTS_ENGINE", "com.google.android.tts")
        locale = current_app.config.get("TTS_LOCALE", "en-IN")
    except Exception:
        engine = "com.google.android.tts"
        locale = "en-IN"
        
    # Spin up an independent worker thread to decouple audio hardware channels
    audio_thread = threading.Thread(target=_execute_tts, args=(text, engine, locale))
    audio_thread.daemon = True
    audio_thread.start()
