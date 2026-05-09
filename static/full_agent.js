// dashboards/static/full_agent.js
// ODIN Dashboard Agent Logic - Auto-Connect Version

let dashboardConfig = {};

async function initDashboard() {
    updateTerminal("Initializing ODIN Interface...");
    
    // 1. Fetch System Config
    try {
        const response = await fetch('/config');
        dashboardConfig = await response.json();
        console.log("System Config Loaded:", dashboardConfig);
        updateTerminal(`Model Sync: ${dashboardConfig.model} [CONNECTED]`);
        
        // Update UI displays if they exist
        const modelDisplay = document.querySelector('#active-model-display');
        if (modelDisplay) modelDisplay.textContent = dashboardConfig.model;
    } catch (e) {
        console.warn("Could not fetch system config. Using defaults.");
        updateTerminal("Config Sync: OFFLINE (Using local defaults)");
    }

    // 2. Check Bridge Connection
    try {
        const bridgeRes = await fetch('http://localhost:8099/health');
        const bridgeStatus = await bridgeRes.json();
        if (bridgeStatus.status === 'online') {
            updateTerminal(`Bridge (Port 8099): ONLINE`);
            updateConnectionBadge(true);
        }
    } catch (e) {
        updateTerminal(`Bridge (Port 8099): OFFLINE - Run root/odin_controller.py`);
        updateConnectionBadge(false);
    }
}

function updateConnectionBadge(online) {
    const badge = document.querySelector('#bridge-status-badge');
    if (badge) {
        badge.textContent = online ? 'ONLINE' : 'OFFLINE';
        badge.style.backgroundColor = online ? '#0a3d0a' : '#3d0a0a';
        badge.style.color = online ? '#4caf50' : '#f44';
    }
}

async function triggerOdinAction(actionType, details) {
    console.log(`Triggering ODIN action: ${actionType}`, details);
    try {
        const response = await fetch('http://localhost:8099/execute_task', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: actionType, ...details })
        });
        const result = await response.json();
        updateTerminal(result.output || result.msg || JSON.stringify(result));
    } catch (error) {
        console.error('Error triggering ODIN action:', error);
        updateTerminal(`Error: ${error.message}`);
    }
}

function updateTerminal(text) {
    const terminal = document.querySelector('.terminal-container div:last-child');
    if (terminal) {
        const timestamp = new Date().toLocaleTimeString();
        terminal.innerHTML += `<br><span style="color: #4a9eff;">[${timestamp}]</span> PS C:\\> ${text}`;
        terminal.scrollTop = terminal.scrollHeight;
    }
}

// Wire up the UI
document.addEventListener('DOMContentLoaded', () => {
    initDashboard();

    const psBtn = document.querySelector('.powershell-btn');
    if (psBtn) {
        psBtn.addEventListener('click', () => {
            const cmd = prompt("Enter PowerShell Command:");
            if (cmd) triggerOdinAction("run_cmd", { command: cmd });
        });
    }

    // Support the "Send to ODIN" button in the chat area
    const sendBtn = document.querySelector('.workspace .powershell-btn');
    if (sendBtn) {
        sendBtn.addEventListener('click', () => {
            const input = document.querySelector('#agentInput');
            if (input && input.value.trim()) {
                triggerOdinAction("run_cmd", { command: input.value });
                input.value = '';
            }
        });
    }
});
