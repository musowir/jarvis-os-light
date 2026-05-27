import subprocess
import json

def execute_system_activity(prompt):
    """
    Parses and fires device environment commands via Termux utilities.
    Uses strict contextual intent checks to prevent conversational keywords 
    (like asking for local time) from falsely triggering system changes.
    """
    p = prompt.lower().strip()
    
    # Normalize variants to avoid parsing gaps
    p = p.replace("flash light", "flashlight")
    p = p.replace("wi-fi", "wifi")
    p = p.replace("cellular", "data").replace("mobile data", "data")
    
    # Define active action modifiers to ensure a command change is intended
    action_words = ["turn", "switch", "enable", "disable", "on", "off", "activate", "deactivate", "open", "toggle"]
    has_action_intent = any(w in p for w in action_words)

    # 1. FLASHLIGHT COMMANDS
    if "flashlight" in p or "torch" in p:
        if any(w in p for w in ["on", "enable", "activate"]):
            subprocess.run(["termux-torch", "on"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, "Flashlight activated successfully."
        if any(w in p for w in ["off", "disable", "deactivate"]):
            subprocess.run(["termux-torch", "off"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, "Flashlight deactivated successfully."

    # 2. MOBILE DATA PANEL DRAWERS (Requires an explicit toggle/action phrase)
    if "data" in p and has_action_intent:
        if any(w in p for w in ["off", "disable", "on", "enable", "switch", "open", "turn"]):
            subprocess.run(["am", "start", "-a", "android.settings.DATA_ROAMING_SETTINGS"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, "Opening Android cellular network settings drawer panel."

    # 3. WIRELESS NETWORKING (WI-FI)
    if "wifi" in p or "wireless" in p:
        if any(w in p for w in ["status", "connection", "check", "info"]):
            try:
                res = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=4)
                if res.returncode == 0 and res.stdout.strip():
                    info = json.loads(res.stdout)
                    return True, f"Network Audit: Attached to network '{info.get('ssid', 'Unknown')}' with local IP address {info.get('ip', 'Unassigned')}."
            except Exception:
                pass
            return True, "Unable to pull live network connection metrics right now."
            
        if any(w in p for w in ["on", "enable", "activate"]):
            subprocess.run(["termux-wifi-enable", "true"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, "Wireless networking enabled."
            
        if any(w in p for w in ["off", "disable", "deactivate"]):
            subprocess.run(["termux-wifi-enable", "false"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, "Wireless networking disabled successfully."

    # 4. LOCATION SERVICES / GPS (Requires explicit action words to bypass conversational queries)
    if ("location" in p or "gps" in p) and has_action_intent:
        if any(w in p for w in ["on", "enable", "off", "disable", "turn", "open", "switch"]):
            subprocess.run(["am", "start", "-a", "android.settings.LOCATION_SOURCE_SETTINGS"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, "Opening system location and GPS service management configurations."
        
    return False, ""

