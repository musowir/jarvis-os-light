# ==============================================================================
# SYSTEM INSTANCE CODE BASE : JARVIS CORE FRAMEWORK
# MODULE          : core.system_actions
# DESCRIPTION     : Intercepts and processes native Android device management tasks,
#                   hardware controls, volume scaling, and telemetry collection via Termux APIs.
# COORDINATES     : Layer-2 Core Background Engines
# SUBSYSTEM       : Native Hardware Integration & Peripheral Control Gateway
# ==============================================================================

import subprocess
import shutil

def handle_system_action(prompt: str) -> tuple[bool, str]:
    """
    Checks if a user's message is an explicit device management request.
    Normalizes spatial gaps to intercept hardware flags accurately.
    """
    clean_prompt = prompt.lower().strip()
    
    # COLLAPSE ALL SPACES FOR HARDWARE PERIPHERAL CHECKING
    # This turns "flash light" into "flashlight"
    compressed_prompt = "".join(clean_prompt.split())

    # 1. Flashlight / Torch Peripheral Interceptor
    if "flashlight" in compressed_prompt or "torch" in compressed_prompt:
        if not shutil.which("termux-torch"):
            return True, "Hardware command intercepted, but Termux API torch binaries are not installed on this system instance."
        
        try:
            if any(off_kw in clean_prompt for off_kw in ["off", "disable", "kill"]):
                subprocess.run(["termux-torch", "off"], check=True)
                return True, "Flashlight deactivated successfully."
            
            elif any(on_kw in clean_prompt for on_kw in ["on", "enable", "switch", "turn"]):
                subprocess.run(["termux-torch", "on"], check=True)
                return True, "Flashlight activated successfully."
            
            else:
                return True, "I recognized a flashlight command, but please specify if you want it 'on' or 'off'."
                
        except subprocess.CalledProcessError:
            return True, "Hardware error encountered. Please verify Termux API subsystem permissions."

    # 2. System Status Check
    if clean_prompt in ["status", "system status", "device info"]:
        battery_status = "Unknown"
        if shutil.which("termux-battery-status"):
            try:
                res = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=2)
                battery_status = res.stdout.strip() or "No output received"
            except Exception:
                battery_status = "Telemetry interface timed out."
        else:
            battery_status = "Termux API helper modules not found."
            
        return True, f"System matrix active. Current hardware diagnostic state: {battery_status}"

    # 3. Storage Check Utility
    if clean_prompt in ["check storage", "disk space", "storage info"]:
        try:
            total, used, free = shutil.disk_usage("/")
            gb = 1024 * 1024 * 1024
            storage_feedback = f"Storage Array: Total {total/gb:.1f}GB, Used {used/gb:.1f}GB, Free {free/gb:.1f}GB."
            return True, storage_feedback
        except Exception as e:
            return True, f"Failed to pool storage array vectors: {str(e)}"

    # 4. Volume Layer Modifier
    if clean_prompt.startswith("volume "):
        level = clean_prompt.replace("volume ", "").strip()
        if shutil.which("termux-volume"):
            try:
                subprocess.run(["termux-volume", "music", level], check=True)
                return True, f"Audio streaming track updated to level {level}."
            except Exception:
                pass
        return True, f"Processing peripheral modification request to volume layer: {level}"

    return False, ""
