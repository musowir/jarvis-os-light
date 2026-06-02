// ==============================================================================
// SYSTEM INSTANCE CODE BASE : JARVIS CORE FRAMEWORK
// MODULE          : static.js.main
// DESCRIPTION     : Client-side event controller handling DOM element node hooks,
//                   asynchronous event-stream processing, auth interception, and device telemetry mapping.
// COORDINATES     : Layer-4 Frontend Layout Logic Matrix
// SUBSYSTEM       : User Interface UX, Context Router & Stream Integration Layer
// ==============================================================================

// Runtime DOM Node Hooks
const chatBox = document.getElementById('chatBox');
const userInput = document.getElementById('userInput');
const sessionList = document.getElementById('sessionList');
const hardwareLogList = document.getElementById('hardwareLogList');
const sidebarMenu = document.getElementById('sidebarMenu');
const sidebarOverlay = document.getElementById('sidebarOverlay');
const modalOverlay = document.getElementById('modalOverlay');
const hamburgerBtn = document.getElementById('hamburgerBtn');
const customConfirmModal = document.getElementById('customConfirmModal');
const modalPromptText = document.getElementById('modalPromptText');
const modalConfirmBtn = document.getElementById('modalConfirmBtn');
const modalCancelBtn = document.getElementById('modalCancelBtn');
const modalHeading = document.getElementById('modalHeading');

const chatsPanel = document.getElementById('chatsPanel');
const hardwarePanel = document.getElementById('hardwarePanel');
const settingsPanel = document.getElementById('settingsPanel');
const chatsTab = document.getElementById('chatsTab');
const hardwareTab = document.getElementById('hardwareTab');
const settingsTab = document.getElementById('settingsTab');

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
let modalDeleteMode = 'session'; // Modes: 'session' | 'account'

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
    if (!chatsTab || !hardwareTab || !settingsTab || !chatsPanel || !hardwarePanel || !settingsPanel) return;
    
    // Reset active visual states across all tabs
    chatsTab.classList.remove('active');
    hardwareTab.classList.remove('active');
    settingsTab.classList.remove('active');
    chatsPanel.classList.add('hidden-panel');
    hardwarePanel.classList.add('hidden-panel');
    settingsPanel.classList.add('hidden-panel');

    if (panelTarget === 'chats') {
        chatsTab.classList.add('active');
        chatsPanel.classList.remove('hidden-panel');
        loadSessions();
    } else if (panelTarget === 'hardware') {
        hardwareTab.classList.add('active');
        hardwarePanel.classList.remove('hidden-panel');
        loadHardwareTelemetry();
    } else if (panelTarget === 'settings') {
        settingsTab.classList.add('active');
        settingsPanel.classList.remove('hidden-panel');
        fetchUserProfileDetails();
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
            
            // Force re-reveal of hamburger layout controls natively
            const hamburger = document.getElementById('hamburgerBtn');
            if (hamburger) {
                hamburger.classList.remove('hidden');
                hamburger.style.display = 'flex';
            }
            
            switchSidebarPanel('chats');
            loadSessions(true);
            loadHardwareTelemetry();
        } else {
            triggerCustomAlertModal("SUCCESS", "Account instance mapped safely. Processing entry handshakes.");
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
        const hamburger = document.getElementById('hamburgerBtn');
        if (hamburger) hamburger.classList.add('hidden');
        return true;
    }
    return false;
}

// ==========================================
// 🛠️ PROFILE SETTINGS MANAGEMENT & LOGOUT API
// ==========================================
function fetchUserProfileDetails() {
    const errorNode = document.getElementById('settingsErrorMsg');
    const successNode = document.getElementById('settingsSuccessMsg');
    if (errorNode) errorNode.style.display = 'none';
    if (successNode) successNode.style.display = 'none';

    fetch('/profile')
        .then(res => {
            if (interceptUnauthorized(res.status)) return null;
            if (!res.ok) throw new Error("Failed to pull profile data schema.");
            return res.json();
        })
        .then(user => {
            if (!user) return;
            const nameInput = document.getElementById('settingsName');
            const emailInput = document.getElementById('settingsEmail');
            if (nameInput) nameInput.value = user.name || '';
            if (emailInput) emailInput.value = user.email || '';
        })
        .catch(err => {
            if (errorNode) {
                errorNode.innerText = `[ERROR]: ${err.message}`;
                errorNode.style.display = 'block';
            }
        });
}

// Update runtime settings
function updateProfileSettings() {
    const errorNode = document.getElementById('settingsErrorMsg');
    const successNode = document.getElementById('settingsSuccessMsg');
    if (errorNode) errorNode.style.display = 'none';
    if (successNode) successNode.style.display = 'none';

    const name = document.getElementById('settingsName').value.trim();
    const email = document.getElementById('settingsEmail').value.trim();
    const password = document.getElementById('settingsPassword').value;

    if (!name || !email) {
        if (errorNode) {
            errorNode.innerText = "[ERROR]: Identity coordinates cannot be unassigned.";
            errorNode.style.display = 'block';
        }
        return;
    }

    const payload = { name, email };
    if (password) payload.password = password;

    fetch('/profile/update', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(async res => {
        if (interceptUnauthorized(res.status)) return null;
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Failed to finalize profile update adjustments.");
        return data;
    })
    .then(data => {
        if (!data) return;
        if (successNode) {
            successNode.innerText = "[SUCCESS]: Identity matrix parameters modified.";
            successNode.style.display = 'block';
        }
        const passwordInput = document.getElementById('settingsPassword');
        if (passwordInput) passwordInput.value = '';
    })
    .catch(err => {
        if (errorNode) {
            errorNode.innerText = `[ERROR]: ${err.message}`;
            errorNode.style.display = 'block';
        }
    });
}

function executeLogout() {
    fetch('/logout', { method: 'POST' })
        .then(() => {
            if (chatBox) chatBox.innerHTML = '';
            currentSessionId = null;
            
            const hamburger = document.getElementById('hamburgerBtn');
            if (hamburger) hamburger.classList.add('hidden');
            
            if (sidebarMenu) sidebarMenu.classList.remove('open');
            if (sidebarOverlay) sidebarOverlay.classList.remove('active');
            if (authOverlay) authOverlay.classList.add('active');
        });
}

function triggerAccountDeletionModal() {
    modalDeleteMode = 'account';
    pendingDeleteId = null;
    
    if (modalHeading) modalHeading.innerText = "Purge Account Instance";
    if (modalPromptText) modalPromptText.innerText = "CRITICAL DATA HAZARD: Are you sure you want to completely erase your user profile instance? This operation cannot be undone.";
    
    if (modalCancelBtn) modalCancelBtn.style.display = "inline-block";
    if (modalConfirmBtn) {
        modalConfirmBtn.style.background = "#ef4444";
        modalConfirmBtn.innerText = "Purge Permanently";
        modalConfirmBtn.onclick = executeDeletion;
    }
    
    if (customConfirmModal) customConfirmModal.classList.add('active');
    if (modalOverlay) modalOverlay.classList.add('active');
}

// ==========================================
// 🚨 CUSTOM WEB ALERT/CONFIRMATION MODAL ENGINE
// ==========================================
function triggerCustomAlertModal(title, text) {
    if (modalHeading) modalHeading.innerText = title;
    if (modalPromptText) modalPromptText.innerText = text;
    
    // Hide cancel option for descriptive message panels
    if (modalCancelBtn) modalCancelBtn.style.display = "none";
    
    if (modalConfirmBtn) {
        modalConfirmBtn.style.background = "#111521";
        modalConfirmBtn.style.border = "1px solid #1e2538";
        modalConfirmBtn.innerText = "Dismiss Acknowledgement";
        modalConfirmBtn.onclick = closeCustomModal;
    }
    
    if (customConfirmModal) customConfirmModal.classList.add('active');
    if (modalOverlay) modalOverlay.classList.add('active');
}

function triggerCustomDeleteModal(id, title) {
    modalDeleteMode = 'session';
    pendingDeleteId = id;
    
    if (modalHeading) modalHeading.innerText = "Delete Thread";
    if (modalPromptText) modalPromptText.innerText = "Are you sure you want to permanently delete \"" + title + "\"?";
    
    if (modalCancelBtn) modalCancelBtn.style.display = "inline-block";
    if (modalConfirmBtn) {
        modalConfirmBtn.style.background = "#ef4444";
        modalConfirmBtn.style.border = "none";
        modalConfirmBtn.innerText = "Delete";
        modalConfirmBtn.onclick = executeDeletion;
    }

    if (customConfirmModal) customConfirmModal.classList.add('active');
    if (modalOverlay) modalOverlay.classList.add('active');
}

function closeCustomModal() { 
    if (customConfirmModal) customConfirmModal.classList.remove('active'); 
    if (modalOverlay) modalOverlay.classList.remove('active');
    pendingDeleteId = null; 
}

function executeDeletion() {
    if (modalDeleteMode === 'account') {
        fetch('/profile/delete', { method: 'DELETE' })
            .then(async res => {
                if (interceptUnauthorized(res.status)) return;
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || "Failed to purge profile context.");
                closeCustomModal();
                executeLogout();
            })
            .catch(err => triggerCustomAlertModal("CRITICAL ERASURE ERROR", err.message));
        return;
    }

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
                hardwareLogList.innerHTML = '<div style="text-align:center; padding:20px; font-size:12px; color:#475569; font-family:monospace;">NO SYSTEM TELEMETRY ENTROLLER STORED</div>';
                return;
            }
            logs.forEach(log => {
                const item = document.createElement('div');
                item.className = 'telemetry-item';
                
                const fullTimestamp = log.executed_at ? log.executed_at : '0000-00-00 00:00:00';
                
                let sysIcon = "⚙️";
                const feedbackText = log.execution_feedback ? log.execution_feedback.toLowerCase() : '';
                if (feedbackText.includes("torch") || feedbackText.includes("flashlight")) sysIcon = "🔦";
                else if (feedbackText.includes("volume") || feedbackText.includes("audio")) sysIcon = "🔊";
                else if (feedbackText.includes("battery")) sysIcon = "🔋";

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
    
    if (text.startsWith("[System Action]:") || text.startsWith("[SYSTEM_ACTION_EXECUTE]")) {
        const payload = text.replace("[System Action]:", "").replace("[SYSTEM_ACTION_EXECUTE]", "").trim();
        return appendTelemetryAction(payload);
    }

    if (!chatBox) return null;
    const div = document.createElement('div');
    div.className = "msg " + role;

    if (role === 'assistant') {
        div.innerHTML = marked.parse(text);
        Prism.highlightAllUnder(div);
    } else {
        div.innerText = text;
    }

    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
}

// ==========================================
// ⚡ ISOLATED, NON-BLOCKING STREAM CONTROLLER
// ==========================================
async function sendPrompt() {
    if (!userInput) return;
    const text = userInput.value.trim();
    if (!text) return;
    
    userInput.value = '';
    appendMessage('user', text);
    
    let assistantDiv = null;
    let telemetryDiv = null;
    let searchingDiv = null;
    let accumulatedBuffer = "";

    const targetSession = currentSessionId ? currentSessionId : 'null';

    try {
        const response = await fetch('/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: text, session_id: targetSession })
        });

        if (interceptUnauthorized(response.status)) return;
        if (!response.ok) throw new Error("Connection loop error on system socket");

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunkStr = decoder.decode(value);
            const lines = chunkStr.split('\n');

            for (let line of lines) {
                if (line.startsWith('id:')) {
                    currentSessionId = parseInt(line.replace('id:', '').trim());
                } else if (line.startsWith('data:')) {
                    const dataContent = line.slice(5);
                    if (!dataContent) continue;

                    if (dataContent.trim() === "[DONE]") {
                        if (searchingDiv) { searchingDiv.remove(); searchingDiv = null; }
                        loadSessions();
                        if (hardwareTab && hardwareTab.classList.contains('active')) loadHardwareTelemetry();
                        
                        if (currentSessionId) {
                            fetch(`/history?session_id=${currentSessionId}`)
                                .then(res => res.json())
                                .then(messages => {
                                    if (messages && messages.length > 0) {
                                        const lastMsg = messages[messages.length - 1];
                                        if (lastMsg && lastMsg.content) {
                                            if (lastMsg.content.startsWith("[System Action]:") || lastMsg.content.startsWith("[SYSTEM_ACTION_EXECUTE]")) {
                                                if (assistantDiv) { assistantDiv.remove(); assistantDiv = null; }
                                                const cleanContent = lastMsg.content
                                                    .replace("[System Action]:", "")
                                                    .replace("[SYSTEM_ACTION_EXECUTE]", "")
                                                    .trim();
                                                
                                                if (!telemetryDiv) {
                                                    telemetryDiv = appendTelemetryAction(cleanContent);
                                                } else {
                                                    const textSpan = telemetryDiv.querySelector('span:last-child');
                                                    if (textSpan) textSpan.innerText = cleanContent;
                                                }
                                            } else if (assistantDiv) {
                                                assistantDiv.innerHTML = marked.parse(lastMsg.content);
                                                Prism.highlightAllUnder(assistantDiv);
                                            }
                                        }
                                    }
                                })
                                .catch(() => {});
                        }
                        break;
                    }

                    if (dataContent.trim() === "[SYSTEM_SEARCHING]") {
                        searchingDiv = appendTelemetryAction("Jarvis is crawling live web data links...");
                        searchingDiv.classList.add("searching-pulse-animation");
                        continue;
                    }

                    if (searchingDiv) {
                        searchingDiv.remove();
                        searchingDiv = null;
                    }

                    accumulatedBuffer += dataContent;

                    if (accumulatedBuffer.includes("[SYSTEM_ACTION_EXECUTE]") || accumulatedBuffer.includes("[System Action]:")) {
                        const cleanedHardwareAlert = accumulatedBuffer
                            .replace("[SYSTEM_ACTION_EXECUTE]", "")
                            .replace("[System Action]:", "")
                            .trim();
                        
                        if (assistantDiv) { assistantDiv.remove(); assistantDiv = null; }
                        
                        if (!telemetryDiv) {
                            telemetryDiv = appendTelemetryAction(cleanedHardwareAlert);
                        } else {
                            const textSpan = telemetryDiv.querySelector('span:last-child');
                            if (textSpan) textSpan.innerText = cleanedHardwareAlert;
                        }
                    } else {
                        if (!assistantDiv && accumulatedBuffer.trim().length > 0) { 
                            if (!"[SYSTEM_ACTION_EXECUTE]".startsWith(accumulatedBuffer.trim())) {
                                assistantDiv = appendMessage('assistant', ' '); 
                            }
                        }
                        if (assistantDiv) {
                            assistantDiv.innerHTML = marked.parse(accumulatedBuffer);
                            Prism.highlightAllUnder(assistantDiv);
                        }
                    }
                    if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
                }
            }
        }
    } catch (err) {
        if (searchingDiv) searchingDiv.remove();
        triggerCustomAlertModal("PIPELINE ROUTING EXCEPTION", err.message);
    }
}
