import os

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:1.5b"
CPU_THREADS = 4  

TTS_ENGINE = "com.google.android.tts"
TTS_LOCALE = "en-IN"
DB_FILE = "jarvis_chat.db"

SYSTEM_PROMPT = """You are Jarvis, an advanced assistant. Provide direct answers to the user's prompt. 
Never define words, explain grammar, or give language examples unless explicitly asked to do so. 
Keep answers clean, brief, and conversational. No markdown, no emojis."""

FILLER_PHRASES = ["On it.", "Just a moment.", "Processing command."]

