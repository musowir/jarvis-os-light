# core/voice.py
import threading
import subprocess
from flask import current_app

def speak_worker(text, engine, locale):
    subprocess.run([
        "termux-tts-speak", "-e", engine, "-l", locale, "-s", "SYSTEM", text
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def speak(text):
    if text.strip():
        # Safeguard pulling values from configuration contexts contextually
        engine = current_app.config.get("TTS_ENGINE", "com.google.android.tts")
        locale = current_app.config.get("TTS_LOCALE", "en-IN")
        threading.Thread(target=speak_worker, args=(text, engine, locale), daemon=True).start()
