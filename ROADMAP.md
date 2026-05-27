# Jarvis OS Light: 60-Day Development Roadmap
Target: 1 Hour/Day Commitment Over 2 Months

## Phase 1: Robust System Interception & Device Control (Weeks 1–2)
* Focus: Fixing silent failures, intent bleeding, and background persistence issues.
* **Days 1–3**: `am` Command Failures & Fallbacks. Wrap all system intents in try/except blocks; trigger a `termux-toast` notice on failure.
* **Days 4–7**: Semantic Routing Integration. Move from loose keyword checks to clean action phrase verification or regex patterns.
* **Days 8–10**: State Synchronization Engine. Run background verification (`termux-wifi-connectioninfo`) right after hardware toggles execute to confirm state change.
* **Days 11–14**: Termux Wake-Lock Automation. Inject automated wake-lock calls into initialization scripts to keep background sockets alive.

## Phase 2: Memory Optimization & Context Engineering (Weeks 3–4)
* Focus: Resolving LLM hallucinations, conversation history bloating, and tracking session variables.
* **Days 15–18**: Sliding Memory Window Manager. Implement a rolling window that only feeds the system prompt, the last 5–10 message pairs, and a compressed summary of older history.
* **Days 19–22**: Session Parameter Binding. Store temporary context variables (like timezone/location) directly in SQLite tables linked to the session ID.
* **Days 23–26**: Hallucination Guardrails. Deploy an output validation layer to catch and intercept random or invented AI responses.
* **Days 27–28**: System Event History Cleanups. Exclude device system alerts from cluttering the long-term conversational memory log.

## Phase 3: Live RAG & Intelligent Web Search (Weeks 5–6)
* Focus: Optimizing real-time information retrieval without timing out the local inference pipeline.
* **Days 29–32**: Non-blocking Search Pipeline. Handle web queries concurrently using background threads while streaming a "Searching..." indicator to the UI.
* **Days 33–36**: Search Results Scraping & Summarization. Clean up raw web text by stripping headers/footers to save context space.
* **Days 37–41**: Temporal Context Injection. Automatically inject a precise date/time header constraint into every system prompt.
* **Days 42–44**: Query Expansion Layer. Add a pre-processing layer to rewrite brief requests into explicit search engine queries.

## Phase 4: UI Refinement, Core Features & Async TTS (Weeks 7–8)
* Focus: Cleaning up frontend visual components, responsive layouts, and smooth voice synthesis.
* **Days 45–48**: Asynchronous Audio Queues (TTS). Construct an active processing queue thread so text streams display natively without waiting for voice synthesis to finish.
* **Days 49–52**: Markdown/LaTeX Rendering. Integrate a rendering script into `index.html` to perfectly display code blocks, lists, and formatted data.
* **Days 53–56**: Custom Web-UI Confirmation Modals. Replace raw browser alerts with styled overlay modals matching the dark terminal theme.
* **Days 57–60**: Performance Diagnostics. Add a tiny resource monitor tracking tokens-per-second, database write times, and current CPU allocation.
