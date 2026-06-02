# ==============================================================================
# SYSTEM INSTANCE CODE BASE : JARVIS CORE FRAMEWORK
# MODULE          : core.search_engine
# DESCRIPTION     : Scrapes live network data from DuckDuckGo, evaluates search intent,
#                   and parses raw text snippets to inject as real-time context vectors.
# COORDINATES     : Layer-2 Core Background Engines
# SUBSYSTEM       : Live Search & External Knowledge Injection Pipeline
# ==============================================================================

import requests
import urllib.parse
import re
from core.markdown_cleaner import strip_markdown

def clean_html_tags(raw_html: str) -> str:
    """
    Strips out nested HTML elements (like <b>, <strong>, etc.) and unescapes 
    common web characters without requiring bs4.
    """
    # Remove all HTML tags completely
    clean_text = re.sub(r'<[^>]+>', '', raw_html)
    # Patch basic HTML entities
    clean_text = clean_text.replace("&amp;", "&").replace("&quot;", '"').replace("&apos;", "'")
    clean_text = clean_text.replace("&lt;", "<").replace("&gt;", ">").replace("&#x27;", "'")
    return re.sub(r'\s+', ' ', clean_text).strip()

def detect_search_intent(prompt: str) -> bool:
    """Scans the prompt globally for local context or explicit search terms."""
    clean = prompt.lower()
    keywords = ["search", "google", "look up", "check for", "malappuram", "munduparamba", "kerala", "district"]
    return any(kw in clean for kw in keywords)

def extract_search_query(prompt: str) -> str:
    """Cleans up the user prompt to pass a high-quality query to the search engine."""
    return re.sub(r'^(google|search|look up|please search for|check for)\s+', '', prompt, flags=re.IGNORECASE).strip()

def web_search(query: str) -> str:
    """
    Executes a privacy-respecting HTML scrape request on DuckDuckGo.
    Returns a pristine, cleaned snippet summary block for context injection.
    """
    if not query.strip():
        return "No search query provided."

    print(f"🌐 Sourcing live network context for query: '{query}'")
    
    encoded_query = urllib.parse
