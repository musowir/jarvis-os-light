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

    # Helper function to execute commands securely with fallback alerts
    def run_secure_command(cmd_args, success_msg, error_toast_text):
        try:
            # check=True forces an exception if the underlying command returns non-zero status
            subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return True, success_msg
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fire an immediate red visual banner overlay on your Android screen
            alert_msg = f"Jarvis Alert: {error_toast_text} failed to execute."
            subprocess.run(["termux-toast", "-b", "red", "-c", "white", alert_msg])
            return False, f"Hardware execution crashed. Triggered toast alert: '{alert_msg}'"

    # ==========================================
    # 1. FLASHLIGHT COMMANDS
    # ==========================================
    if "flashlight" in p or "torch" in p:
        if any(w in p for w in ["on", "enable", "activate"]):
            return run_secure_command(["termux-torch", "on"], "Flashlight activated successfully.", "Torch ON")
        if any(w in p for w in ["off", "disable", "deactivate"]):
            return run_secure_command(["termux-torch", "off"], "Flashlight deactivated successfully.", "Torch OFF")

    # ==========================================
    # 2. MOBILE DATA PANEL DRAWERS
    # ==========================================
    if "data" in p and has_action_intent:
        if any(w in p for w in ["off", "disable", "on", "enable", "switch", "open", "turn"]):
            return run_secure_command(
                ["am", "start", "-a", "android.settings.DATA_ROAMING_SETTINGS"],
                "Opening Android cellular network settings drawer panel.",
                "Mobile Data Drawer"
            )

    # ==========================================
    # 3. WIRELESS NETWORKING (WI-FI)
    # ==========================================
    if "wifi" in p or "wireless" in p:
        # Check status / Info (Preserved your exact logic)
        if any(w in p for w in ["status", "connection", "check", "info"]):
            try:
                res = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=4)
                if res.returncode == 0 and res.stdout.strip():
                    info = json.loads(res.stdout)
                    return True, f"Network Audit: Attached to network '{info.get('ssid', 'Unknown')}' with local IP address {info.get('ip', 'Unassigned')}."
            except Exception:
                pass
            return True, "Unable to pull live network connection metrics right now."

        # Active toggles upgraded with immediate state verification hooks
        if any(w in p for w in ["on", "enable", "activate"]):
            success = run_secure_command(["termux-wifi-enable", "true"], "", "Wi-Fi Activation")
            if success[0]:
                time.sleep(1.5) # Give hardware radio a brief window to spin up
                # Verify state sync
                check = subprocess.run(["termux-wifi-enable"], capture_output=True, text=True)
                if "true" in check.stdout.lower():
                    return True, "Wireless networking verified active via state synchronization loop."
                return True, "Wi-Fi command sent, but state synchronization verification timed out."
            return success

        if any(w in p for w in ["off", "disable", "deactivate"]):
            success = run_secure_command(["termux-wifi-enable", "false"], "", "Wi-Fi Deactivation")
            if success[0]:
                time.sleep(1.5)
                # Verify state sync
                check = subprocess.run(["termux-wifi-enable"], capture_output=True, text=True)
                if "false" in check.stdout.lower():
                    return True, "Wireless networking safely disabled and verified offline."
                return True, "Wi-Fi disable command sent, but state verification reflects a hanging state."
            return success

    # ==========================================
    # 4. LOCATION SERVICES / GPS
    # ==========================================
    if ("location" in p or "gps" in p) and has_action_intent:
        if any(w in p for w in ["on", "enable", "off", "disable", "turn", "open", "switch"]):
            return run_secure_command(
                ["am", "start", "-a", "android.settings.LOCATION_SOURCE_SETTINGS"],
                "Opening system location and GPS service management configurations.",
                "Location Settings Drawer"
            )

    return False, ""

