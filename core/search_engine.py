# core/search_engine.py
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
    
    encoded_query = urllib.parse.quote_plus(query)
    search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return f"Search interface responded with status code: {response.status_code}"

        text = response.text
        snippets = []
        start_idx = 0
        
        # Pull out up to 4 dense snippets to provide rich contextual anchoring
        while len(snippets) < 4:
            start_idx = text.find('class="result__snippet"', start_idx)
            if start_idx == -1:
                break
            
            open_tag = text.find('>', start_idx)
            close_tag = text.find('</a>', open_tag)
            
            if open_tag != -1 and close_tag != -1:
                # Capture the full snippet span containing inner markup
                raw_snippet = text[open_tag + 1:close_tag]
                clean_snippet = clean_html_tags(raw_snippet)
                
                # Filter out search-engine layout junk/boilerplate
                if clean_snippet and not clean_snippet.startswith("Forward to"):
                    snippets.append(clean_snippet)
                    
            start_idx = close_tag

        if not snippets:
            return "Search query executed, but no descriptive snippet elements could be parsed."

        # Compile the raw text snippets list
        raw_context = "\n".join([f"- {s}" for s in snippets])
        
        # Purge markdown text structures completely to preserve token processing densities
        return strip_markdown(raw_context)

    except Exception as e:
        return f"Network exception encountered during live search execution: {str(e)}"
