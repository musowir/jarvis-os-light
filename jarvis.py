#!/usr/bin/env python3
"""
Jarvis – Fully Fixed, Reliable Voice Assistant with Live Web Browsing.
Uses robust browser header emulation and bulletproof text extraction.
"""

import os
import subprocess
import time
import requests
import re
import sys
import select
import random
import json
import urllib.parse

# ===================== CONFIGURATION =====================
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:1.5b"
CPU_THREADS = 4  

TTS_ENGINE = "com.google.android.tts"
TTS_LOCALE = "en-IN"

SYSTEM_PROMPT = """You are Jarvis, a real-time smart assistant. 
Keep your conversational responses brief, helpful, and split into clear sentences. No markdown, no emojis.

You have access to tools. If you do not know the answer to a question, or if the user asks for real-time information (like weather, news, updates), or a device action, you MUST call a tool by adding a JSON block at the very end of your message.

Tool format rules:
To search the web: {"tool": "search", "query": "search keywords here"}
To toggle flashlight: {"tool": "flashlight", "state": "on"} or {"tool": "flashlight", "state": "off"}
To check battery: {"tool": "battery"}
To check Wi-Fi: {"tool": "wifi"}

When you receive the tool results from the system, summarize the data naturally for the user in 1 or 2 normal sentences. Do not make up facts or repeat the JSON block."""

CHAT_HISTORY = [{"role": "system", "content": SYSTEM_PROMPT}]
FILLER_PHRASES = ["On it, sir.", "Just a moment.", "Looking that up.", "Processing."]
# =========================================================

def ensure_ollama_running():
    try:
        requests.get("http://localhost:11434/api/version", timeout=1)
    except Exception:
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

def check_for_enter():
    if sys.stdin in select.select([sys.stdin], [], [], 0.0)[0]:
        sys.stdin.readline()
        return True
    return False

def listen():
    print("\n🎤 Listening... (Silence for 5s, or press ENTER to stop)")
    full_prompt = []
    last_speech_time = time.time()
    silence_timeout = 5
    
    while True:
        if check_for_enter():
            break

        current_time = time.time()
        if current_time - last_speech_time >= silence_timeout:
            if full_prompt:
                break
            else:
                return input("Type your command: ").strip()

        try:
            result = subprocess.run(["termux-speech-to-text"], capture_output=True, text=True, timeout=10)
            heard = result.stdout.strip()
        except subprocess.TimeoutExpired:
            heard = ""

        if check_for_enter():
            if heard:
                full_prompt.append(heard)
            break

        if heard:
            last_speech_time = time.time()
            clean_heard = heard.lower().strip('.!?,')
            if clean_heard in ["send", "done"]:
                break
            elif clean_heard in ["cancel", "abort"]:
                return ""
            print(f"  + {heard}")
            full_prompt.append(heard)

    return " ".join(full_prompt).strip()

def internet_search(query):
    """Fetches web snippets using updated classes and a regex backup loop."""
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    
    # Heavy browser emulation headers to get past anti-scraping filters
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            # Method A: Try parsing through the 'pup' HTML selector utility
            process = subprocess.Popen(['pup', 'a.result__snippet text{}'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, _ = process.communicate(input=res.text)
            lines = [line.strip() for line in stdout.split('\n') if line.strip()]
            
            # Method B: Regular Expression extraction backup if the system's HTML layout shifts
            if not lines:
                snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', res.text, re.DOTALL)
                lines = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets]
            
            summary = " ".join(lines[:3])
            return summary if summary else "Web search completed but the results page returned no text snippets."
            
        elif res.status_code == 403:
            return "Search request was rejected by the server firewall. Try again in a brief moment."
            
    except Exception as e:
        return f"Web search failed due to a processing link issue: {e}"
        
    return "Could not retrieve online details."

def process_json_tool(tool_obj):
    tool_name = tool_obj.get("tool")
    
    if tool_name == "search":
        query = tool_obj.get("query", "")
        print(f"\n🌐 [WEB LOG]: Searching the internet for -> {query}")
        return internet_search(query)
        
    elif tool_name == "flashlight":
        state = tool_obj.get("state", "off")
        print(f"\n⚙️ [SYSTEM LOG]: Toggling Flashlight -> {state}")
        subprocess.run(["termux-torch", state], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"The device flashlight has been turned {state}."
        
    elif tool_name == "battery":
        print(f"\n⚙️ [SYSTEM LOG]: Reading battery layout")
        res = subprocess.run(["termux-battery-status"], capture_output=True, text=True)
        return res.stdout.strip() if res.stdout else "Battery details unavailable."
        
    elif tool_name == "wifi":
        print(f"\n⚙️ [SYSTEM LOG]: Fetching connection profiles")
        res = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True)
        return res.stdout.strip() if res.stdout else "Wi-Fi link details unavailable."
        
    return "Unknown tool call requested."

def speak(text):
    if not text.strip():
        return
    subprocess.run([
        "termux-tts-speak", "-e", TTS_ENGINE, "-l", TTS_LOCALE,
        "-s", "SYSTEM", text
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def think_and_stream(user_input, is_system_feedback=False):
    role = "system" if is_system_feedback else "user"
    CHAT_HISTORY.append({"role": role, "content": user_input})
    
    payload = {
        "model": MODEL,
        "messages": CHAT_HISTORY,
        "stream": True,
        "options": {
            "temperature": 0.1, 
            "num_ctx": 2048,   
            "num_thread": CPU_THREADS 
        },
    }
    
    if not is_system_feedback:
        filler = random.choice(FILLER_PHRASES)
        print(f"\rJarvis: {filler}")
        speak(filler)

    try:
        resp = requests.post(OLLAMA_URL, json=payload, stream=True)
        resp.raise_for_status()
        
        full_response_text = ""
        audio_buffer = ""
        printed_header = False
        
        for line in resp.iter_lines():
            if line:
                chunk = json.loads(line.decode('utf-8'))
                content = chunk.get("message", {}).get("content", "")
                
                full_response_text += content
                audio_buffer += content
                
                # Intercept the JSON block strings entirely before they can print or speak
                if "{" in full_response_text and "}" not in full_response_text:
                    continue
                
                if content and "{" not in content and "}" not in content:
                    if not printed_header and not is_system_feedback:
                        print("Jarvis: ", end="", flush=True)
                        printed_header = True
                    print(content, end="", flush=True)

                if any(punct in audio_buffer for punct in [".", "!", "?", "\n"]):
                    if "{" in audio_buffer:
                        audio_buffer = ""
                        continue
                    clean_audio = audio_buffer.replace("\n", " ").strip()
                    if clean_audio:
                        speak(clean_audio)
                    audio_buffer = ""

        if audio_buffer.strip() and "{" not in full_response_text:
            speak(audio_buffer.strip())
            
        print() 

        # Scan for structured JSON tool requests safely
        match = re.search(r"\{.*?\}", full_response_text)
        if match:
            try:
                tool_data = json.loads(match.group(0))
                tool_output = process_json_tool(tool_data)
                
                system_message = (
                    f"System Environment Data Result:\n{tool_output}\n\n"
                    "Instruction: Relay these live data facts cleanly to the user in 1-2 conversational sentences. "
                    "Do not make up external information or call another tool."
                )
                return think_and_stream(system_message, is_system_feedback=True)
            except Exception:
                pass 
        else:
            CHAT_HISTORY.append({"role": "assistant", "content": full_response_text})
            
    except Exception as e:
        if not is_system_feedback:
            CHAT_HISTORY.pop()
        print(f"\nError: {e}")

def main():
    subprocess.run(["killall", "termux-microphone-record"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ensure_ollama_running()
    print(f"Jarvis Online. Operational flaws resolved.\n")

    while True:
        user_speech = listen()
        if not user_speech:
            continue
        print(f"You: {user_speech}")

        if user_speech.lower() in ("exit", "quit", "stop"):
            speak("Powering down systems. Goodbye, sir.")
            break

        think_and_stream(user_speech)

if __name__ == "__main__":
    main()

