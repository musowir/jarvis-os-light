// Runtime DOM Node Hooks
const chatBox = document.getElementById('chatBox');
const userInput = document.getElementById('userInput');
const sessionList = document.getElementById('sessionList');
const hardwareLogList = document.getElementById('hardwareLogList');
const sidebarMenu = document.getElementById('sidebarMenu');
const sidebarOverlay = document.getElementById('sidebarOverlay');
const hamburgerBtn = document.getElementById('hamburgerBtn');
const customConfirmModal = document.getElementById('customConfirmModal');
const modalPromptText = document.getElementById('modalPromptText');
const modalConfirmBtn = document.getElementById('modalConfirmBtn');

const chatsPanel = document.getElementById('chatsPanel');
const hardwarePanel = document.getElementById('hardwarePanel');
const chatsTab = document.getElementById('chatsTab');
const hardwareTab = document.getElementById('hardwareTab');

const authOverlay = document.getElementById('authOverlay');
const regFieldsContainer = document.getElementById('regFieldsContainer');
const authTitle = document.getElementById('authTitle');
const authSubtitle = document.getElementById('authSubtitle');
const authSubmitBtn = document.getElementById('authSubmitBtn');
const authToggleMsg = document.getElementById('authToggleMsg');
const authToggleLink = document.getElementById('authToggleLink');
const authErrorMsg = document.getElementById('authErrorMsg');

let currentSessionId = null;
let pendingDeleteId = null;
let isLoginState = true;

// Window Instantiation Setup Handler
window.onload = function() { 
    currentSessionId = null;
    if (chatBox) chatBox.innerHTML = '';
    loadSessions(true); 
    loadHardwareTelemetry();
};

// ==========================================
// 🎛️ SIDEBAR VIEW CONTROLLERS
// ==========================================
function switchSidebarPanel(panelTarget) {
    if (!chatsTab || !hardwareTab || !chatsPanel || !hardwarePanel) return;
    
    if (panelTarget === 'chats') {
        chatsTab.classList.add('active');
        hardwareTab.classList.remove('active');
        chatsPanel.classList.remove('hidden-panel');
        hardwarePanel.classList.add('hidden-panel');
        loadSessions();
    } else {
        hardwareTab.classList.add('active');
        chatsTab.classList.remove('active');
        hardwarePanel.classList.remove('hidden-panel');
        chatsPanel.classList.add('hidden-panel');
        loadHardwareTelemetry();
    }
}

// ==========================================
// 🔐 FRONTEND SECURITY SYSTEM INTERCEPTORS
// ==========================================
function toggleAuthContext() {
    isLoginState = !isLoginState;
    if (authErrorMsg) authErrorMsg.style.display = 'none';
    
    if (isLoginState) {
        if (authTitle) authTitle.innerText = "SYSTEM_ACCESS";
        if (authSubtitle) authSubtitle.innerText = "Provide security keys to sync matrix profile.";
        if (regFieldsContainer) regFieldsContainer.style.display = "none";
        if (authSubmitBtn) authSubmitBtn.innerText = "Synchronize";
        if (authToggleMsg) authToggleMsg.innerText = "New user instance?";
        if (authToggleLink) authToggleLink.innerText = "Register Account";
    } else {
        if (authTitle) authTitle.innerText = "REGISTER_INSTANCE";
        if (authSubtitle) authSubtitle.innerText = "Provision global credentials across internal database fields.";
        if (regFieldsContainer) regFieldsContainer.style.display = "block";
        if (authSubmitBtn) authSubmitBtn.innerText = "Initialize Core";
        if (authToggleMsg) authToggleMsg.innerText = "Active entity key?";
        if (authToggleLink) authToggleLink.innerText = "Access Framework";
    }
}

function processAuthSubmission() {
    if (authErrorMsg) authErrorMsg.style.display = 'none';
    const usernameField = document.getElementById('authUsername');
    const passwordField = document.getElementById('authPassword');
    
    const username = usernameField ? usernameField.value.trim() : '';
    const password = passwordField ? passwordField.value : '';
    
    if (!username || !password) {
        renderAuthError("Identity parameters cannot hold unassigned records.");
        return;
    }

    let targetUrl = '/login';
    let payload = { username, password };

    if (!isLoginState) {
        const nameField = document.getElementById('authName');
        const emailField = document.getElementById('authEmail');
        const name = nameField ? nameField.value.trim() : '';
        const email = emailField ? emailField.value.trim() : '';
        
        if (!name || !email) {
            renderAuthError("Demographic metadata blocks are required.");
            return;
        }
        targetUrl = '/register';
        payload = { username, password, name, email };
    }

    fetch(targetUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(async res => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Authentication validation failure.");
        return data;
    })
    .then(data => {
        if (isLoginState) {
            if (authOverlay) authOverlay.classList.remove('active');
            loadSessions();
            loadHardwareTelemetry();
        } else {
            alert("Account instance mapped safely. Processing entry handshakes.");
            toggleAuthContext();
        }
    })
    .catch(err => renderAuthError(err.message));
}

function renderAuthError(msg) {
    if (!authErrorMsg) return;
    authErrorMsg.innerText = "[ERROR]: " + msg;
    authErrorMsg.style.display = 'block';
}

function interceptUnauthorized(status) {
    if (status === 401) {
        if (authOverlay) authOverlay.classList.add('active');
        return true;
    }
    return false;
}

// ==========================================
// 💬 LAYOUT RUNTIMES & SESSION API SYNC
// ==========================================
function toggleSidebar() {
    if (!sidebarMenu || !sidebarOverlay || !hamburgerBtn) return;
    const isOpen = sidebarMenu.classList.toggle('open');
    sidebarOverlay.classList.toggle('active');
    if (isOpen) { hamburgerBtn.classList.add('hidden'); } 
    else { hamburgerBtn.classList.remove('hidden'); }
}

function loadSessions(isInitialLoad = false) {
    if (!sessionList) return;
    fetch('/sessions')
        .then(res => {
            if (interceptUnauthorized(res.status)) return null;
            return res.json();
        })
        .then(data => {
            if (!data) return;
            sessionList.innerHTML = '';
            data.forEach((session) => {
                const div = document.createElement('div');
                div.className = "session-item " + (session.id === currentSessionId ? 'active' : '');
                
                const textSpan = document.createElement('span');
                textSpan.className = 'session-text';
                textSpan.innerText = session.title || "Thread Line " + session.id;
                textSpan.onclick = function() { switchSession(session.id); toggleSidebar(); };
                
                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'delete-btn';
                deleteBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>';
                deleteBtn.onclick = function(e) { e.stopPropagation(); triggerCustomDeleteModal(session.id, textSpan.innerText); };
                
                div.appendChild(textSpan);
                div.appendChild(deleteBtn);
                sessionList.appendChild(div);
            });
        }).catch(() => {});
}

function loadHardwareTelemetry() {
    if (!hardwareLogList) return;
    fetch('/telemetry/logs')
        .then(res => {
            if (interceptUnauthorized(res.status)) return null;
            if (res.status === 404) return [];
            return res.json();
        })
        .then(logs => {
            if (!logs) return;
            hardwareLogList.innerHTML = '';
            if (logs.length === 0) {
                hardwareLogList.innerHTML = '<div style="text-align:center; padding:20px; font-size:12px; color:#475569; font-family:monospace;">NO SYSTEM TELEMETRY ENTRIES STORED</div>';
                return;
            }
            logs.forEach(log => {
                const item = document.createElement('div');
                item.className = 'telemetry-item';
                
                const fullTimestamp = log.executed_at ? log.executed_at : '0000-00-00 00:00:00';
                
                // Assign a clean contextual icon based on the executed feedback text
                let sysIcon = "⚙️";
                const feedbackText = log.execution_feedback ? log.execution_feedback.toLowerCase() : '';
                if (feedbackText.includes("torch") || feedbackText.includes("flashlight")) sysIcon = "🔦";
                else if (feedbackText.includes("volume") || feedbackText.includes("audio")) sysIcon = "🔊";
                else if (feedbackText.includes("battery")) sysIcon = "🔋";

                // Rendered with just the action tracking details and the unified timestamp
                item.innerHTML = `
                    <div class="telemetry-meta">
                        <span>${sysIcon} SYS_EXEC</span>
                        <span>${fullTimestamp}</span>
                    </div>
                    <div class="telemetry-res" style="font-family: monospace; font-weight: 500;">&gt; ${log.execution_feedback || 'Action executed successfully'}</div>
                `;
                hardwareLogList.appendChild(item);
            });
        }).catch(() => {});
}


function triggerCustomDeleteModal(id, title) {
    pendingDeleteId = id;
    if (modalPromptText) modalPromptText.innerText = "Are you sure you want to permanently delete \"" + title + "\"?";
    if (customConfirmModal) customConfirmModal.classList.add('active');
    if (modalConfirmBtn) modalConfirmBtn.onclick = executeDeletion;
}

function closeCustomModal() { 
    if (customConfirmModal) customConfirmModal.classList.remove('active'); 
    pendingDeleteId = null; 
}

function executeDeletion() {
    if (!pendingDeleteId) return;
    fetch('/sessions/delete?session_id=' + pendingDeleteId, { method: 'DELETE' })
        .then(res => {
            if (interceptUnauthorized(res.status)) return null;
            return res.json();
        })
        .then(data => {
            if (!data) return;
            if (data.status === "success") {
                if (currentSessionId === pendingDeleteId) { 
                    currentSessionId = null; 
                    if (chatBox) chatBox.innerHTML = '';
                }
                closeCustomModal();
                loadSessions();
            }
        }).catch(() => {});
}

function createNewChat() {
    currentSessionId = null;
    if (chatBox) chatBox.innerHTML = '';
    loadSessions();
    if (sidebarMenu && sidebarMenu.classList.contains('open')) toggleSidebar();
}

function switchSession(sessionId) {
    currentSessionId = sessionId;
    if (chatBox) chatBox.innerHTML = '';
    fetch('/history?session_id=' + sessionId)
        .then(res => {
            if (interceptUnauthorized(res.status)) return null;
            return res.json();
        })
        .then(messages => {
            if (!messages) return;
            messages.forEach(msg => { 
                if (msg.role !== 'system') { appendMessage(msg.role, msg.content); } 
            });
            loadSessions(); 
        }).catch(() => {});
}

function appendTelemetryAction(text) {
    if (!chatBox) return null;
    let hardwareIcon = "⚙️";
    const lowerText = text.toLowerCase();
    if (lowerText.includes("flashlight") || lowerText.includes("torch")) hardwareIcon = "🔦";
    else if (lowerText.includes("volume") || lowerText.includes("audio")) hardwareIcon = "🔊";
    else if (lowerText.includes("storage") || lowerText.includes("disk")) hardwareIcon = "💾";
    else if (lowerText.includes("battery") || lowerText.includes("diagnostic")) hardwareIcon = "🔋";

    const div = document.createElement('div');
    div.className = "system-telemetry-badge";
    div.innerHTML = `<span>${hardwareIcon}</span> <span>${text}</span>`;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
}

function appendMessage(role, text) {
    if (!text) return null;
    if (text.startsWith("[System Action]:")) {
        return appendTelemetryAction(text.replace("[System Action]:", "").trim());
    }

    if (!chatBox) return null;
    const div = document.createElement('div');
    div.className = "msg " + role;
    div.innerText = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
}

// ==========================================
// ⚡ ISOLATED, NON-BLOCKING STREAM CONTROLLER
// ==========================================
function sendPrompt() {
    if (!userInput) return;
    const text = userInput.value.trim();
    if (!text) return;
    
    userInput.value = '';
    appendMessage('user', text);
    
    let assistantDiv = null;
    let telemetryDiv = null;
    let accumulatedBuffer = "";

    const targetSession = currentSessionId ? currentSessionId : 'null';
    const eventSource = new EventSource('/stream?prompt=' + encodeURIComponent(text) + '&session_id=' + targetSession);
    
    eventSource.onmessage = function(event) {
        if (event.data === "[DONE]") {
            eventSource.close();
            loadSessions();
            if (hardwareTab && hardwareTab.classList.contains('active')) loadHardwareTelemetry();
        } else {
            accumulatedBuffer += event.data;

            if (accumulatedBuffer.startsWith("[System Action]:")) {
                const cleanedHardwareAlert = accumulatedBuffer.replace("[System Action]:", "").trim();
                
                if (assistantDiv) { 
                    assistantDiv.remove(); 
                    assistantDiv = null; 
                }
                
                if (!telemetryDiv) {
                    telemetryDiv = appendTelemetryAction(cleanedHardwareAlert);
                } else {
                    const textSpan = telemetryDiv.querySelector('span:last-child');
                    if (textSpan) textSpan.innerText = cleanedHardwareAlert;
                }
            } else {
                if (!assistantDiv) { 
                    assistantDiv = appendMessage('assistant', ' '); 
                }
                if (assistantDiv) assistantDiv.innerText = accumulatedBuffer;
            }
            
            if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
        }
    };

    eventSource.addEventListener('message', function(event) {
        if (event.lastEventId) {
            currentSessionId = parseInt(event.lastEventId);
        }
    });

    eventSource.onerror = function(err) { 
        eventSource.close(); 
        fetch('/sessions').then(res => interceptUnauthorized(res.status)).catch(() => {});
    };
}
