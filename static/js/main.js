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
const hamburgerBtn = document.getElementById('hamburgerBtn');
const customConfirmModal = document.getElementById('customConfirmModal');
const modalPromptText = document.getElementById('modalPromptText');
const modalConfirmBtn = document.getElementById('modalConfirmBtn');
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
