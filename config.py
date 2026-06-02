# ==============================================================================
# SYSTEM INSTANCE CODE BASE : JARVIS CORE FRAMEWORK
# MODULE          : config
# DESCRIPTION     : Defines base system variables, environment switches, model configuration,
#                   security secrets, and global operational instructions.
# COORDINATES     : Layer-1 Main Application Bootstrap
# SUBSYSTEM       : Global Configuration Matrix Layer
# ==============================================================================

import os

class BaseConfig:
    """Core configurations shared across all deployment environments."""
    OLLAMA_URL = os.environ.get("JARVIS_OLLAMA_URL", "http://localhost:11434/api/chat")
    MODEL = os.environ.get("JARVIS_MODEL", "qwen2.5:1.5b")
    CPU_THREADS = int(os.environ.get("JARVIS_CPU_THREADS", 4))
    
    TTS_ENGINE = "com.google.android.tts"
    TTS_LOCALE = "en-IN"
    DB_FILE = os.environ.get("JARVIS_DB_FILE", "jarvis_chat.db")
    JWT_SECRET = os.environ.get("JARVIS_JWT_SECRET", "super-secure-jarvis-matrix-key-2026")

    SYSTEM_PROMPT = """You are Jarvis, an advanced assistant. Provide direct answers to the user's prompt. 
Never define words, explain grammar, or give language examples unless explicitly asked to do so. 
Keep answers clean, brief, and conversational. No markdown, no emojis."""

    FILLER_PHRASES = ["On it.", "Just a moment.", "Processing command."]

class DevelopmentConfig(BaseConfig):
    """Local debugging options."""
    DEBUG = True

class ProductionConfig(BaseConfig):
    """Optimized, safe configurations for Termux deployment."""
    DEBUG = False
    # Enforce stronger session handling cookies in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

# Helper lookup dictionary
config_environments = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": ProductionConfig
}
