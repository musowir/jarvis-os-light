# core/memory_manager.py
import requests

def summarize_old_interactions(old_messages: list, ollama_url: str, model_name: str) -> str:
    """
    Takes a block of older messages and runs a rapid, low-token 
    summarization pass through Ollama with fully injected runtime vectors.
    """
    if not old_messages:
        return ""

    formatted_chat = "\n".join([f"{m['role']}: {m['content']}" for m in old_messages])
    
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system", 
                "content": "Compress the following conversation into a dense, single-sentence bullet point tracking key facts and explicit user preferences. Do not use conversational intros."
            },
            {"role": "user", "content": formatted_chat}
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": 2048
        }
    }

    try:
        response = requests.post(
            ollama_url, 
            json=payload, 
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get("message", {}).get("content", "").strip()
    except requests.exceptions.Timeout:
        print("ℹ️ [Memory Manager Check] Background summarization took over 60s. Frame skipped gracefully.")
    except Exception as e:
        print(f"ℹ️ [Memory Manager Check] Background thread paused: {str(e)}")
    
    return ""
