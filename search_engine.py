import re
import requests
import urllib.parse

INITIAL_SEARCH_KEYWORDS = [
    "list", "member", "who is", "what is", "weather", "news", "score", "latest", 
    "current", "election", "mla", "minister", "president", "temperature", "team",
    "google", "search", "find", "lookup", "duckduckgo", "ddg", "browse"
]

FOLLOWUP_SEARCH_KEYWORDS = ["full", "more", "all", "complete", "continue", "detail", "list", "explain more"]

def internet_search(query):
    clean_query = query.lower()
    for prefix in ["google about ", "google ", "search for ", "search ", "find out about ", "find ", "lookup "]:
        if clean_query.startswith(prefix):
            query = query[len(prefix):]
            break

    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', res.text, re.DOTALL)
            lines = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets]
            if lines:
                return " ".join(lines[:6])
    except Exception:
        return ""
    return ""

