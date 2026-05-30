# Jarvis OS Light 🤖📱

Jarvis OS Light is a highly modular, localized AI companion architecture optimized to run natively inside Android environments via Termux. By combining a local Ollama LLM backend with custom system intent-intercept wrappers, Jarvis can run hardware-level automated commands (Wi-Fi toggles, device settings drawers, flashlight control) and handle live asynchronous web searches when real-time context is required.

---

## 🚀 Key Features & Architectural Enhancements
* **Hardware Interception Layer:** Isolated action intent parsers translating conversational speech to automated Termux commands seamlessly.
* **Sliding Memory Window Manager:** High-efficiency conversational context wrapper that enforces a 10-message rolling horizon combined with an automated Ollama history condensation algorithm.
* **Session Parameter Binding:** Real-time SQLite session table extraction capable of mapping ephemeral environment variables (e.g., location coordinates, device modes) directly into the prompt stream.
* **Alignment Refusal Recovery Engine:** A defensive regex parsing wrapper that intercepts artificial safety refusals or model hallucinations, automatically re-routing requests with a clean contextual layout.
* **Concurrent Streaming UI:** A dark, responsive terminal dashboard using Server-Sent Events (SSE) for raw token stream updates alongside interactive system log telemetry updates.
* **Asynchronous Voice Output:** Completely decoupled, non-blocking Termux TTS integration running on detached threads to prevent browser client UI freezing.

---

## 🛠️ Prerequisites & Android Permissions

Because this framework interacts natively with physical phone hardware, you must configure the underlying environment correctly before spinning up the server layers:

1. Install **Termux** and **Termux:API** from F-Droid.
2. **Grant System Drawers Overrides:** Go to Android Settings -> Apps -> Special App Access -> Display over other apps. Toggle permissions to Allowed for both Termux and Termux:API.
3. **Configure Background Execution:** Navigate to Android Settings -> Apps -> Termux -> Battery optimization. Switch the configuration to Unrestricted to stop Android from aggressively killing active Python socket loops.

---

## 📦 Automated Installation & Setup

We have completely automated the environment configurations. Execute the following sequence inside your Termux workspace to clone, configure package libraries, install required binaries, compile dependencies, and instantiate database schemas:

```bash
git clone [https://github.com/musowir/jarvis-os-light.git](https://github.com/musowir/jarvis-os-light.git)
cd jarvis-os-light
chmod +x setup.sh
./setup.sh
```

## 🏃 Run the Application

* ​Ensure your local Ollama server instance is active and hosting your target model weights in the background (ollama serve).
* ​Activate your isolated environment space and boot up the primary Flask application thread:

```
source venv/bin/activate
python app.py
```

* ​Access the User Interface: Open any web browser on your phone and navigate to: http://localhost:8080
* ​Stop the Server Safely: Press Ctrl + C in the active Termux window to cleanly break the active socket loops.

## 📅 Development Tracking Workflow

​When handling issues or pushing contributions, please conform to our modular agile lifecycle columns:

1. Todo: Choose an active architectural milestone card. 
2. Development: Move the card here, modify the python source blocks inside Termux, and submit code history updates (git commit -m "feat: text").
3. Test: Pull changes into a real-world debugging environment to check device system states and ensure keywords pass context smoothly.
4. ​Done: Verify edge-cases are handled perfectly and merge!
---
 ## 🤝 Collaboration & Contributing

We absolutely welcome open-source collaborations, feature ideas, and performance optimizations! Whether you're working on expanding hardware intents, optimizing context window usage for local models, or building sleek custom web UI enhancements, your help is welcome.

### ​How to Contribute

* ​Fork the repository down to your GitHub namespace.
* ​Create a clean feature branch tracking your specific enhancement target:
`git checkout -b feature/AmazingNewHardwareFeature`
* ​Commit your code modifications following Conventional Commits tracking structures: 
`git commit -m "feat: patch edge-case loops inside location intent-parsers"`
* ​Push your feature branch straight back up to your remote fork: 
`git push origin feature/AmazingNewHardwareFeature`
* ​Open a Pull Request (PR) detailing your changes.

## ​📄 License
​This project is open-source and licensed under the GNU General Public License v3 (GPLv3) — see the LICENSE file for complete open usability details.