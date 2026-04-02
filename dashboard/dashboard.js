document.addEventListener('DOMContentLoaded', () => {
    const navItems = document.querySelectorAll('.nav-item');
    
    const user = JSON.parse(localStorage.getItem('jodo_user') || '{}');
    if (!user.email) {
        window.location.href = '/';
        return;
    }

    // Dynamic Base URL based on current host
    const baseUrl = window.location.origin;
    const baseUrlDisplay = document.getElementById('sb-base-url-display');
    if (baseUrlDisplay) baseUrlDisplay.innerText = baseUrl;
    const baseUrlCopyBtn = document.querySelector('.api-key-container .key-row .copy-btn');
    if (baseUrlCopyBtn) {
        baseUrlCopyBtn.setAttribute('onclick', `copyText('${baseUrl}', 'Base URL')`);
    }

    // Update Profile UI
    const welcomeHeading = document.getElementById('welcome-heading');
    if (welcomeHeading) welcomeHeading.textContent = `Welcome back, ${user.name || 'Developer'}`;
    
    // Update Keys UI
    updateKeysUI(user);

    // Tab Switching Logic
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = item.getAttribute('data-tab');
            if (tabId) switchTab(tabId);
        });
    });

    window.switchTab = function(tabId) {
        // Update Nav
        navItems.forEach(nav => {
            nav.classList.remove('active');
            if (nav.getAttribute('data-tab') === tabId) nav.classList.add('active');
        });

        // Update Content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.style.display = 'none';
        });
        const target = document.getElementById(`${tabId}-tab`);
        if (target) {
            target.style.display = 'block';
            target.classList.add('animate');
        }

        // Trigger Tab Specific Loads
        if (tabId === 'transactions') loadTransactions();
        if (tabId === 'webhooks') {
            loadWebhooks();
            loadWebhookLogs();
        }
    };

    // Key Management Event Listeners
    const generateBtn = document.getElementById('generate-keys-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateNewKeys);
    }

    const revealBtn = document.getElementById('reveal-secret-btn');
    const secretDisplay = document.getElementById('sb-secret-display');
    const authDisplay = document.getElementById('sb-auth-header-display');
    
    if (revealBtn && secretDisplay) {
        revealBtn.addEventListener('click', () => {
            const isHidden = secretDisplay.textContent.includes('•');
            if (isHidden) {
                secretDisplay.textContent = user.sandbox_secret || 'N/A';
                if (authDisplay) {
                    const basicAuth = btoa(`${user.sandbox_key}:${user.sandbox_secret}`);
                    authDisplay.textContent = `Basic ${basicAuth}`;
                }
                revealBtn.textContent = 'Hide';
            } else {
                secretDisplay.textContent = '••••••••••••••••••••••••••••••••';
                if (authDisplay) authDisplay.textContent = 'Basic ••••••••••••••••••••••••••••••••';
                revealBtn.textContent = 'Reveal';
            }
        });
    }


    // Initial Load
    loadTransactions();
    loadDashboardStats();
});

// --- UI Helpers ---

function handleLogout() {
    localStorage.removeItem('jodo_user');
    window.location.href = '/dashboard/login.html';
}

// Playground API Interaction Logic
const API_BASE_URL = window.location.origin + '/api/v1/integrations/pay/orders';
const USER_DATA = JSON.parse(localStorage.getItem('jodo_user') || '{}');

async function loadDashboardStats() {
    const user = JSON.parse(localStorage.getItem('jodo_user') || '{}');
    const totalEl = document.getElementById('stat-total-requests');
    const successEl = document.getElementById('stat-success-rate');
    const latencyEl = document.getElementById('stat-avg-latency');
    
    if (!totalEl) return;

    try {
        const res = await fetch(`/api/v1/integrations/pay/orders/stats?email=${user.email}`);
        const result = await res.json();
        
        if (result.status === 'success') {
            const { total_requests_24h, success_rate, avg_latency_ms } = result.data;
            
            // Animate numbers for premium feel
            animateValue(totalEl, 0, total_requests_24h, 1000);
            animatePercentage(successEl, success_rate, 1000);
            latencyEl.textContent = `${avg_latency_ms}ms`;
        }
    } catch (e) { console.error("Stats error:", e); }
}

function animateValue(obj, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start).toLocaleString();
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

function animatePercentage(obj, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = (progress * end).toFixed(1) + '%';
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

function updateKeysUI(user) {
    const miniKey = document.getElementById('mini-key-display');
    const fullKey = document.getElementById('sb-key-display');
    const fullSecret = document.getElementById('sb-secret-display');
    const authDisplay = document.getElementById('sb-auth-header-display');
    
    if (miniKey) miniKey.textContent = user.sandbox_key || 'jodo_sb_••••••••••••';
    if (fullKey) fullKey.textContent = user.sandbox_key || 'jodo_sb_••••••••••••';
    if (fullSecret) fullSecret.textContent = '••••••••••••••••••••••••••••••••';
    if (authDisplay) authDisplay.textContent = 'Basic ••••••••••••••••••••••••••••••••';
    
    const revealBtn = document.getElementById('reveal-secret-btn');
    if (revealBtn) revealBtn.textContent = 'Reveal';
}

async function generateNewKeys() {
    const user = JSON.parse(localStorage.getItem('jodo_user') || '{}');
    const btn = document.getElementById('generate-keys-btn');
    
    if (!confirm("Are you sure? This will immediately invalidate your current Sandbox keys.")) return;
    
    btn.disabled = true;
    btn.textContent = "⏳ Generating...";
    
    try {
        const response = await fetch('/api/v1/auth/keys/rotate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: user.email })
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            // Update Local Storage
            user.sandbox_key = result.sandbox_key;
            user.sandbox_secret = result.sandbox_secret;
            localStorage.setItem('jodo_user', JSON.stringify(user));
            
            // Update UI
            updateKeysUI(user);
            showToast("🚀 New Keys Generated Successfully!");
        } else {
            alert("Error: " + result.message);
        }
    } catch (e) {
        console.error(e);
        alert("Failed to connect to security server.");
    } finally {
        btn.disabled = false;
        btn.textContent = "Generate New Key";
    }
}

window.copyToClipboard = function(elementId, label) {
    const user = JSON.parse(localStorage.getItem('jodo_user') || '{}');
    let text = "";
    
    if (elementId === 'sb-key-display') text = user.sandbox_key;
    else if (elementId === 'sb-secret-display') text = user.sandbox_secret;
    else if (elementId === 'sb-auth-header-display') {
        text = `Basic ${btoa(user.sandbox_key + ':' + user.sandbox_secret)}`;
    }
    
    if (!text) {
        // Fallback to DOM content if not in user object
        text = document.getElementById(elementId).textContent;
        if (text.includes('•')) {
            alert(`Please reveal the secret before copying the ${label}.`);
            return;
        }
    }

    navigator.clipboard.writeText(text).then(() => {
        showToast(`📋 ${label} Copied!`);
    });
};

window.copyText = function(text, label) {
    navigator.clipboard.writeText(text).then(() => {
        showToast(`📋 ${label} Copied!`);
    });
};

function showToast(message) {
    const toast = document.createElement('div');
    toast.style = "position: fixed; bottom: 30px; right: 30px; background: #6366f1; color: white; padding: 15px 25px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); z-index: 1000; font-size: 0.9rem; font-weight: 600; transition: opacity 0.3s ease;";
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
}

// --- Data Fetching Functions ---

async function loadTransactions() {
    const user = JSON.parse(localStorage.getItem('jodo_user') || '{}');
    const listEl = document.getElementById('transaction-list');
    if (!listEl) return;

    try {
        const response = await fetch(`/api/v1/integrations/pay/orders/list?email=${user.email}`);
        const result = await response.json();
        
        if (result.status === 'success') {
            listEl.innerHTML = '';
            result.data.forEach(order => {
                const tr = document.createElement('tr');
                tr.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
                tr.innerHTML = `
                    <td style="padding: 16px; font-size: 0.85rem; font-family: monospace;">${order.id}</td>
                    <td style="padding: 16px; font-size: 0.85rem; font-weight: 600;">₹${order.amount.toFixed(2)}</td>
                    <td style="padding: 16px;">
                        <span style="font-size: 0.7rem; padding: 4px 10px; border-radius: 12px; font-weight: 700; text-transform: uppercase; background: ${getStatusColor(order.status)};">
                            ${order.status}
                        </span>
                    </td>
                    <td style="padding: 16px; font-size: 0.85rem; text-transform: capitalize;">${order.pg}</td>
                    <td style="padding: 16px; font-size: 0.8rem; color: var(--text-muted);">${new Date(order.created_at).toLocaleDateString()}</td>
                `;
                listEl.appendChild(tr);
            });
        }
    } catch (error) {
        console.error("Error loading transactions:", error);
    }
}

function getStatusColor(status) {
    switch (status) {
        case 'paid': return 'rgba(16, 185, 129, 0.2); color: #10b981;';
        case 'settled': return 'rgba(59, 130, 246, 0.2); color: #3b82f6;';
        case 'failed': return 'rgba(239, 68, 68, 0.2); color: #ef4444;';
        default: return 'rgba(148, 163, 184, 0.2); color: #94a3b8;';
    }
}

async function loadWebhooks() {
    const user = JSON.parse(localStorage.getItem('jodo_user') || '{}');
    const listEl = document.getElementById('endpoint-list');
    if (!listEl) return;

    try {
        const response = await fetch(`/api/v1/webhooks?email=${user.email}`);
        const result = await response.json();
        
        if (result.status === 'success') {
            listEl.innerHTML = '';
            result.data.forEach((hook, index) => {
                const url = typeof hook === 'string' ? hook : hook.url;
                const events = hook.events || ['*'];
                
                const div = document.createElement('div');
                div.className = 'card';
                div.style.padding = '16px';
                div.style.marginBottom = '12px';
                div.style.display = 'block';
                div.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 0.85rem; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${url}</span>
                        <button onclick="removeWebhook(${index})" style="background: none; border: none; color: #ef4444; cursor: pointer; font-size: 1.2rem;">&times;</button>
                    </div>
                    <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                        ${events.map(ev => `
                            <span style="font-size: 0.65rem; background: rgba(99, 102, 241, 0.15); color: #818cf8; padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(99, 102, 241, 0.2);">
                                ${ev.replace('order.payment.', '')}
                            </span>
                        `).join('')}
                    </div>
                `;
                listEl.appendChild(div);
            });
        }
    } catch (e) { console.error(e); }
}

async function addWebhook() {
    const user = JSON.parse(localStorage.getItem('jodo_user') || '{}');
    const input = document.getElementById('webhook-url-input');
    const url = input.value.trim();
    if (!url) return;

    // Collect events
    const checkboxes = document.querySelectorAll('input[name="webhook-event"]:checked');
    const events = Array.from(checkboxes).map(cb => cb.value);

    try {
        const response = await fetch('/api/v1/webhooks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: user.email, url, events })
        });
        const result = await response.json();
        if (result.status === 'success') {
            input.value = '';
            loadWebhooks();
        } else {
            alert(result.message);
        }
    } catch (e) { console.error(e); }
}

async function removeWebhook(index) {
    if (!confirm("Are you sure you want to remove this webhook?")) return;
    const user = JSON.parse(localStorage.getItem('jodo_user') || '{}');
    
    try {
        const response = await fetch(`/api/v1/webhooks/${index}?email=${user.email}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        if (result.status === 'success') {
            loadWebhooks();
        }
    } catch (e) { console.error(e); }
}

async function loadWebhookLogs() {
    const user = JSON.parse(localStorage.getItem('jodo_user') || '{}');
    const listEl = document.getElementById('webhook-logs');
    if (!listEl) return;

    try {
        const response = await fetch(`/api/v1/webhooks/logs?email=${user.email}`);
        const result = await response.json();
        
        if (result.status === 'success') {
            listEl.innerHTML = '';
            result.data.forEach(log => {
                const div = document.createElement('div');
                div.className = 'log-entry';
                div.style.padding = '12px';
                div.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
                div.style.cursor='pointer';
                div.onclick = () => showLogDetails(log);
                div.innerHTML = `
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-size: 0.8rem; font-weight: 700; color: var(--secondary);">${log.event}</span>
                        <span style="font-size: 0.7rem; color: ${log.status === 'success' ? '#10b981' : '#ef4444'};">${log.status.toUpperCase()}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted);">
                        <span>${log.url.slice(0, 30)}...</span>
                        <span>${new Date(log.timestamp).toLocaleTimeString()}</span>
                    </div>
                `;
                listEl.appendChild(div);
            });
        }
    } catch (e) { console.error(e); }
}

function showLogDetails(log) {
    const modal = document.getElementById('log-viewer');
    const title = document.getElementById('modal-title');
    const content = document.getElementById('modal-content');
    
    title.textContent = `Webhook Log: ${log.event}`;
    content.textContent = JSON.stringify(log, null, 2);
    modal.style.display = 'flex';
}
