# Jarvis OS Light 🤖📱

Jarvis OS Light is a highly modular, localized AI companion architecture optimized to run natively inside Android environments via Termux. By combining a local Ollama LLM backend with custom system intent-intercept wrappers, Jarvis can run hardware-level automated commands (Wi-Fi toggles, device settings drawers, flashlight control) and fallback to live asynchronous web searches when real-time context is needed.

---

## 🚀 Features Under Active Development
* Hardware Interception Layer: Isolated action intent parsers translating conversational speech to automated Termux commands.
* Localized Core Engines: Integrated lightweight SQL-backed thread architecture for robust chat memory logging.
* Concurrent Streaming UI: A dark, responsive terminal dashboard using server-sent events (SSE) for fast token streaming.
* Asynchronous Voice Output: Non-blocking TTS integration mapping responses to spoken audio layers dynamically.

---

## 🛠️ Prerequisites & Android Permissions

Because this framework interacts natively with physical phone hardware, you must configure the underlying environment correctly before spinning up the server layers:

1. Install Termux & Termux:API from F-Droid.
2. Grant System Drawers Overrides: Go to Android Settings -> Apps -> Special App Access -> Display over other apps. Toggle permissions to Allowed for both Termux and Termux:API.
3. Configure Background Execution: Navigate to Android Settings -> Apps -> Termux -> Battery optimization. Switch the configuration to Unrestricted to stop Android from aggressively killing active Python socket loops.

---

## 📦 Local Installation & Setup

Execute the following commands sequentially inside your Termux terminal workspace to initialize your dependencies:

- pkg update && pkg upgrade -y
- pkg install python git termux-api -y
- git clone https://github.com/musowir/jarvis-os-light.git
- cd jarvis-os-light
- pip install flask requests
- termux-wake-lock

---

## 🏃 Run the Application

Ensure your local Ollama server instance is active and hosting your configured target model weights in the background. Then, start the primary Flask app framework thread:

- python app.py

* Access the User Interface: Open any web browser on your phone and navigate to: http://localhost:8080
* Stop the Server safely: Press Ctrl + C in the Termux window to break the active socket loops.

---

## 📅 Development Tracking Workflow

This project maps directly to a strict 1 hour/day timeline tracked via our custom 60-Day Sprint Project Board. 

When handling issues or pushing contributions, please conform to our modular agile lifecycle columns:
1. Todo: Choose an active architectural milestone card.
2. Development: Move the card here, modify the python source blocks inside Termux, and submit code history updates (git push).
3. Test: Pull changes into a real-world debugging environment to check device system states and ensure keywords pass context smoothly.
4. Done: Verify edge-cases are handled perfectly and merge!

---

## 🤝 Collaboration & Contributing

We absolutely welcome open-source collaborations, feature ideas, and performance optimizations! Whether you're working on expanding hardware intents, optimizing context window usage for local models, or building sleek custom web UI enhancements, your help is welcome.

### How to Contribute
1. Fork the repository down to your GitHub namespace.
2. Create a clean feature branch tracking your specific enhancement target: git checkout -b feature/AmazingNewHardwareFeature
3. Commit your code modifications following clean, descriptive tracking notes: git commit -m "Patched edge-case loops inside location intent-parsers"
4. Push your feature branch straight back up to your remote fork: git push origin feature/AmazingNewHardwareFeature
5. Open a Pull Request (PR) detailing your changes.

---

## 📄 License
This project is open-source and licensed under the GNU General Public License v3 (GPLv3) — see the LICENSE file for complete open usability details.
