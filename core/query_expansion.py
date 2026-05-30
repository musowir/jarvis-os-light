# core/query_expansion.py
import re
import datetime

def expand_search_query(user_prompt: str) -> str:
    """
    Pre-processes conversational or brief requests into explicit, optimized
    search engine queries by resolving temporal references and removing conversational fluff.
    """
    if not user_prompt:
        return ""

    # 1. Lowercase for uniform keyword analysis
    query = user_prompt.lower().strip()

    # 2. Extract and strip conversation conversational fillers/prefixes
    fillers = [
        r"can you look up", r"search for", r"find out about", r"what happened to",
        r"google", r"check the status of", r"tell me about", r"what is", r"who is"
    ]
    for filler in fillers:
        query = re.sub(rf"^{filler}\s+", "", query)

    # 3. Dynamic Temporal Resolution (Anchoring 2026 Reality)
    today = datetime.date.today()
    
    if "yesterday" in query:
        yesterday = today - datetime.timedelta(days=1)
        query = query.replace("yesterday", yesterday.strftime("%B %d %Y"))
    elif "tomorrow" in query:
        tomorrow = today + datetime.timedelta(days=1)
        query = query.replace("tomorrow", tomorrow.strftime("%B %d %Y"))
    elif "last week" in query:
        query = query.replace("last week", f"week of {(today - datetime.timedelta(weeks=1)).strftime('%B %d %Y')}")
    elif "this year" in query:
        query = query.replace("this year", "2026")
    elif "current market" in query or "stock market today" in query:
        query = re.sub(r"current market|stock market today", f"stock market indices {today.strftime('%B %d %Y')}", query)

    # 4. Inject implicit domain expansion hints
    # Weather tracking expansion
    if any(w in query for w in ["weather", "rain", "temperature", "forecast"]):
        if not any(loc in query for loc in ["in ", "at ", "for "]):
            # If no location is explicitly named, safely anchor to system geoloc context hints
            query += " current weather forecast data statistics"

    # News tracking expansion
    if any(n in query for n in ["news", "latest event", "breaking"]):
        if "2026" not in query and not re.search(r'\b\d{4}\b', query):
            query += f" breaking news updates {today.strftime('%B %Y')}"

    # Clean up redundant spaces left behind by replacements
    query = re.sub(r'\s+', ' ', query).strip()
    
    return query if query else user_prompt
