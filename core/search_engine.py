# core/search_engine.py
import requests
import urllib.parse

def web_search(query: str) -> str:
    """
    Executes a privacy-respecting HTML scrape request or DuckDuckGo API lookup.
    Returns a condensed summary text block for Ollama context injection.
    """
    if not query.strip():
        return "No search query provided."

    print(f"🌐 Sourcing live network context for query: '{query}'")
    
    # We use a clean, zero-auth text extraction API layout perfect for lightweight Termux runtimes
    encoded_query = urllib.parse.quote_plus(query)
    search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return f"Search interface responded with status code: {response.status_code}"

        # Simple string processing to pull text snippets without needing heavy bs4 parsing installations
        text = response.text
        snippets = []
        
        # Pull out the result snippets from DuckDuckGo's HTML structure
        start_idx = 0
        while len(snippets) < 3:
            start_idx = text.find('class="result__snippet"', start_idx)
            if start_idx == -1:
                break
            
            open_tag = text.find('>', start_idx)
            close_tag = text.find('</a>', open_tag)
            if open_tag != -1 and close_tag != -1:
                raw_snippet = text[open_tag + 1:close_tag]
                # Clean up residual HTML tags if any exist in the raw string
                clean_snippet = "".join(raw_snippet.split('<')[0].split('>')[-1]).strip()
                if clean_snippet:
                    snippets.append(clean_snippet)
            start_idx = close_tag

        if not snippets:
            return "Search query executed, but no descriptive snippet elements could be parsed."

        return "\n".join([f"- {s}" for s in snippets])

    except Exception as e:
        return f"Network exception encountered during live search execution: {str(e)}"
