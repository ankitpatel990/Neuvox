/**
 * ScamShield AI - Dashboard Application
 * 
 * Handles all API interactions and UI updates for the honeypot dashboard.
 */

// ============================================================================
// Configuration
// ============================================================================
// Use relative URLs so the UI works on any host/port (local, Docker, HF Spaces)
const API_ENDPOINTS = {
    engage: '/api/v1/honeypot/engage',
    session: '/api/v1/honeypot/session',
    health: '/api/v1/health',
    batch: '/api/v1/honeypot/batch',
};

// Example scam messages for quick testing
const EXAMPLE_MESSAGES = [
    "🎰 Congratulations! You have won 10 LAKH RUPEES in our lucky draw! Send OTP to claim your prize immediately!",
    "🏦 ALERT: Your bank account will be blocked in 24 hours. Update KYC now by sending Rs 500 to processing@paytm",
    "👮 This is CBI calling. You are involved in money laundering case. Pay Rs 50000 immediately or face arrest. Call +919876543210",
    "📱 URGENT: Pay Rs 999 to receive your iPhone 15 Pro. UPI ID: scammer@ybl. Bank: 1234567890123 IFSC: HDFC0001234",
];

// ============================================================================
// State Management
// ============================================================================
let state = {
    sessionId: null,
    messages: [],
    extractedIntel: {
        upi_ids: [],
        bank_accounts: [],
        ifsc_codes: [],
        phone_numbers: [],
        phishing_links: [],
    },
    lastResponse: null,
    isLoading: false,
    lastCallbackPayload: null,  // Store the last GUVI callback payload
};

// ============================================================================
// Initialization
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('🛡️ ScamShield AI Dashboard initialized');
    checkHealth();
    
    // Auto-refresh health every 30 seconds
    setInterval(checkHealth, 30000);
});

// ============================================================================
// API Functions
// ============================================================================

/**
 * Check API health status
 */
async function checkHealth() {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    try {
        const response = await fetch(API_ENDPOINTS.health, {
            headers: {
                'x-api-key': 'dev-key-12345', // Development API key (optional)
            },
        });
        const data = await response.json();
        
        // Update status indicator
        statusDot.className = 'status-dot ' + data.status;
        statusText.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
        
        // Update health grid
        updateHealthStatus('healthGroq', data.dependencies?.groq_api);
        updateHealthStatus('healthPostgres', data.dependencies?.postgres);
        updateHealthStatus('healthRedis', data.dependencies?.redis);
        updateHealthStatus('healthModels', data.dependencies?.models_loaded ? 'online' : 'offline');
        
        console.log('✅ Health check:', data.status);
        return data;
    } catch (error) {
        console.error('❌ Health check failed:', error);
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'Offline';
        
        updateHealthStatus('healthGroq', 'offline');
        updateHealthStatus('healthPostgres', 'offline');
        updateHealthStatus('healthRedis', 'offline');
        updateHealthStatus('healthModels', 'offline');
        
        return null;
    }
}

/**
 * Send message to honeypot API
 */
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message || state.isLoading) return;
    
    // Clear welcome message
    const welcome = document.querySelector('.chat-welcome');
    if (welcome) welcome.remove();
    
    // Set loading state
    setLoading(true);
    input.value = '';
    
    // Add scammer message to UI
    addChatMessage(message, 'scammer');
    
    try {
        const startTime = Date.now();
        
        const payload = {
            message: message,
            language: 'auto',
        };
        
        if (state.sessionId) {
            payload.session_id = state.sessionId;
        }
        
        const response = await fetch(API_ENDPOINTS.engage, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': 'dev-key-12345', // Development API key (optional if not configured on server)
            },
            body: JSON.stringify(payload),
        });
        
        const data = await response.json();
        const responseTime = Date.now() - startTime;
        
        // Update state
        state.lastResponse = data;
        state.sessionId = data.session_id;
        
        // Update session ID display
        document.getElementById('sessionId').textContent = 
            `Session: ${data.session_id.substring(0, 8)}...`;
        
        // Update response time
        document.getElementById('responseTime').textContent = 
            `Last response: ${responseTime}ms`;
        
        // Update detection result
        updateDetectionResult(data);
        
        // Update agent info
        updateAgentInfo(data);
        
        // If scam detected, add agent response
        if (data.scam_detected && data.engagement) {
            addChatMessage(data.engagement.agent_response, 'agent', {
                strategy: data.engagement.strategy,
                persona: data.engagement.persona,
                turn: data.engagement.turn_count,
            });
            
            // Update extracted intelligence
            if (data.extracted_intelligence) {
                updateIntelligence(data.extracted_intelligence);
            }
        }
        
        // Check if GUVI callback was triggered
        if (data.guvi_callback) {
            state.lastCallbackPayload = data.guvi_callback;
            updateCallbackStatus(data.guvi_callback);
        }
        
        console.log('📨 API Response:', data);
        
    } catch (error) {
        console.error('❌ API Error:', error);
        addSystemMessage('Error: Could not connect to API. Make sure the server is running.');
    } finally {
        setLoading(false);
    }
}

/**
 * Send example message
 */
function sendExample(index) {
    const message = EXAMPLE_MESSAGES[index];
    document.getElementById('messageInput').value = message;
    sendMessage();
}

/**
 * Start new session
 */
function newSession() {
    state.sessionId = null;
    state.messages = [];
    state.extractedIntel = {
        upi_ids: [],
        bank_accounts: [],
        ifsc_codes: [],
        phone_numbers: [],
        phishing_links: [],
    };
    state.lastResponse = null;
    
    // Clear chat
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.innerHTML = `
        <div class="chat-welcome">
            <div class="welcome-icon">🎭</div>
            <h3>Test the Honeypot Agent</h3>
            <p>Send a scam message to see how the AI agent responds and extracts intelligence.</p>
            <div class="example-messages">
                <p><strong>Try these examples:</strong></p>
                <button class="example-btn" onclick="sendExample(0)">🎰 Lottery Scam</button>
                <button class="example-btn" onclick="sendExample(1)">🏦 Bank Fraud</button>
                <button class="example-btn" onclick="sendExample(2)">👮 Police Threat</button>
                <button class="example-btn" onclick="sendExample(3)">📱 UPI Scam</button>
            </div>
        </div>
    `;
    
    // Reset UI
    document.getElementById('sessionId').textContent = 'No active session';
    document.getElementById('detectionResult').innerHTML = 
        '<div class="no-data">Send a message to see detection results</div>';
    
    // Reset intelligence
    resetIntelligence();
    resetAgentInfo();
    resetCallbackStatus();
    
    console.log('🔄 New session started');
}

// ============================================================================
// UI Update Functions
// ============================================================================

/**
 * Add chat message to UI
 */
function addChatMessage(text, sender, meta = {}) {
    const chatContainer = document.getElementById('chatContainer');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    
    const avatar = sender === 'scammer' ? '🦹' : '🤖';
    const senderName = sender === 'scammer' ? 'Scammer' : 'Agent';
    
    let metaHtml = '';
    if (meta.strategy) {
        metaHtml = `
            <div class="message-meta">
                <span>Turn ${meta.turn}</span>
                <span>Strategy: ${meta.strategy}</span>
                <span>Persona: ${meta.persona}</span>
            </div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-sender">${senderName}</div>
            <div class="message-text">${escapeHtml(text)}</div>
            ${metaHtml}
        </div>
    `;
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    state.messages.push({ sender, text, meta });
}

/**
 * Add system message
 */
function addSystemMessage(text) {
    const chatContainer = document.getElementById('chatContainer');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'system-message';
    messageDiv.style.cssText = 'text-align: center; padding: 10px; color: var(--warning);';
    messageDiv.textContent = text;
    
    chatContainer.appendChild(messageDiv);
}

/**
 * Update detection result panel
 */
function updateDetectionResult(data) {
    const container = document.getElementById('detectionResult');
    const isScam = data.scam_detected;
    const confidence = (data.confidence * 100).toFixed(0);
    
    container.className = `detection-result ${isScam ? 'scam' : 'safe'}`;
    container.innerHTML = `
        <div class="detection-label">Scam Detection</div>
        <div class="detection-value">${isScam ? '⚠️ SCAM DETECTED' : '✓ SAFE'}</div>
        <div class="confidence-bar">
            <div class="confidence-fill" style="width: ${confidence}%"></div>
        </div>
        <div style="margin-top: 8px; font-size: 0.8rem; color: var(--text-secondary);">
            Confidence: ${confidence}% | Language: ${data.language_detected}
        </div>
    `;
}

/**
 * Update agent info panel
 */
function updateAgentInfo(data) {
    if (data.engagement) {
        document.getElementById('agentPersona').textContent = data.engagement.persona || '-';
        document.getElementById('agentStrategy').textContent = data.engagement.strategy || '-';
        document.getElementById('turnCount').textContent = `${data.engagement.turn_count} / 20`;
    }
    document.getElementById('detectedLanguage').textContent = data.language_detected || '-';
}

/**
 * Reset agent info
 */
function resetAgentInfo() {
    document.getElementById('agentPersona').textContent = '-';
    document.getElementById('agentStrategy').textContent = '-';
    document.getElementById('turnCount').textContent = '0 / 20';
    document.getElementById('detectedLanguage').textContent = '-';
}

/**
 * Update intelligence panel
 */
function updateIntelligence(intel) {
    // Merge with existing intelligence
    if (intel.upi_ids) {
        state.extractedIntel.upi_ids = [...new Set([...state.extractedIntel.upi_ids, ...intel.upi_ids])];
    }
    if (intel.bank_accounts) {
        state.extractedIntel.bank_accounts = [...new Set([...state.extractedIntel.bank_accounts, ...intel.bank_accounts])];
    }
    if (intel.ifsc_codes) {
        state.extractedIntel.ifsc_codes = [...new Set([...state.extractedIntel.ifsc_codes, ...intel.ifsc_codes])];
    }
    if (intel.phone_numbers) {
        state.extractedIntel.phone_numbers = [...new Set([...state.extractedIntel.phone_numbers, ...intel.phone_numbers])];
    }
    if (intel.phishing_links) {
        state.extractedIntel.phishing_links = [...new Set([...state.extractedIntel.phishing_links, ...intel.phishing_links])];
    }
    
    // Update UI
    updateIntelValue('upiIds', state.extractedIntel.upi_ids);
    updateIntelValue('bankAccounts', state.extractedIntel.bank_accounts);
    updateIntelValue('ifscCodes', state.extractedIntel.ifsc_codes);
    updateIntelValue('phoneNumbers', state.extractedIntel.phone_numbers);
    updateIntelValue('phishingLinks', state.extractedIntel.phishing_links);
    
    // Update confidence
    const confidence = intel.extraction_confidence || 0;
    document.getElementById('extractionConfidence').textContent = `${(confidence * 100).toFixed(0)}%`;
    document.getElementById('extractionConfidence').className = 
        `intel-value ${confidence > 0 ? 'has-data' : ''}`;
}

/**
 * Update single intelligence value
 */
function updateIntelValue(elementId, values) {
    const element = document.getElementById(elementId);
    if (values && values.length > 0) {
        element.textContent = values.join(', ');
        element.className = 'intel-value has-data';
    } else {
        element.textContent = '-';
        element.className = 'intel-value';
    }
}

/**
 * Reset intelligence panel
 */
function resetIntelligence() {
    updateIntelValue('upiIds', []);
    updateIntelValue('bankAccounts', []);
    updateIntelValue('ifscCodes', []);
    updateIntelValue('phoneNumbers', []);
    updateIntelValue('phishingLinks', []);
    document.getElementById('extractionConfidence').textContent = '-';
}

/**
 * Update health status indicator
 */
function updateHealthStatus(elementId, status) {
    const element = document.getElementById(elementId);
    let displayStatus = status || 'offline';
    
    // Normalize status values
    if (displayStatus === 'not_configured') displayStatus = 'offline';
    if (displayStatus === true) displayStatus = 'online';
    if (displayStatus === false) displayStatus = 'offline';
    
    element.textContent = displayStatus.charAt(0).toUpperCase() + displayStatus.slice(1);
    element.className = `health-status ${displayStatus}`;
}

/**
 * Set loading state
 */
function setLoading(loading) {
    state.isLoading = loading;
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = loading;
    sendBtn.innerHTML = loading 
        ? '<span>Sending...</span>' 
        : '<span>Send</span><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>';
}

// ============================================================================
// Report Functions
// ============================================================================

/**
 * Export full report
 */
function exportReport() {
    const modal = document.getElementById('reportModal');
    const content = document.getElementById('reportContent');
    
    const report = generateReport();
    
    content.innerHTML = `
        <div class="report-section">
            <h4>📋 Session Information</h4>
            <div class="report-item">
                <span class="report-item-label">Session ID:</span>
                <span class="report-item-value">${report.session_id || 'N/A'}</span>
            </div>
            <div class="report-item">
                <span class="report-item-label">Total Messages:</span>
                <span class="report-item-value">${report.total_messages}</span>
            </div>
            <div class="report-item">
                <span class="report-item-label">Language:</span>
                <span class="report-item-value">${report.language}</span>
            </div>
            <div class="report-item">
                <span class="report-item-label">Detection Status:</span>
                <span class="report-item-value">${report.scam_detected ? '⚠️ SCAM DETECTED' : '✓ Safe'}</span>
            </div>
            <div class="report-item">
                <span class="report-item-label">Confidence:</span>
                <span class="report-item-value">${report.confidence}%</span>
            </div>
        </div>
        
        <div class="report-section">
            <h4>🎭 Agent Performance</h4>
            <div class="report-item">
                <span class="report-item-label">Persona Used:</span>
                <span class="report-item-value">${report.persona}</span>
            </div>
            <div class="report-item">
                <span class="report-item-label">Final Strategy:</span>
                <span class="report-item-value">${report.strategy}</span>
            </div>
            <div class="report-item">
                <span class="report-item-label">Turns Completed:</span>
                <span class="report-item-value">${report.turn_count}</span>
            </div>
        </div>
        
        <div class="report-section">
            <h4>📊 Extracted Intelligence</h4>
            ${formatIntelList('UPI IDs', report.extracted_intelligence.upi_ids)}
            ${formatIntelList('Bank Accounts', report.extracted_intelligence.bank_accounts)}
            ${formatIntelList('IFSC Codes', report.extracted_intelligence.ifsc_codes)}
            ${formatIntelList('Phone Numbers', report.extracted_intelligence.phone_numbers)}
            ${formatIntelList('Phishing Links', report.extracted_intelligence.phishing_links)}
            <div class="report-item">
                <span class="report-item-label">Extraction Confidence:</span>
                <span class="report-item-value">${report.extraction_confidence}%</span>
            </div>
        </div>
        
        <div class="report-section">
            <h4>💬 Conversation History</h4>
            <div style="max-height: 200px; overflow-y: auto; background: var(--bg-card); padding: 12px; border-radius: 8px;">
                ${report.messages.map(m => `
                    <div style="margin-bottom: 8px; padding: 8px; background: var(--bg-tertiary); border-radius: 4px;">
                        <strong>${m.sender === 'scammer' ? '🦹 Scammer' : '🤖 Agent'}:</strong>
                        <span style="color: var(--text-secondary);">${escapeHtml(m.text)}</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    modal.classList.add('active');
}

/**
 * Generate report data
 */
function generateReport() {
    const lastResp = state.lastResponse || {};
    
    return {
        session_id: state.sessionId,
        timestamp: new Date().toISOString(),
        total_messages: state.messages.length,
        language: lastResp.language_detected || 'N/A',
        scam_detected: lastResp.scam_detected || false,
        confidence: ((lastResp.confidence || 0) * 100).toFixed(0),
        persona: lastResp.engagement?.persona || 'N/A',
        strategy: lastResp.engagement?.strategy || 'N/A',
        turn_count: lastResp.engagement?.turn_count || 0,
        extracted_intelligence: state.extractedIntel,
        extraction_confidence: ((lastResp.extracted_intelligence?.extraction_confidence || 0) * 100).toFixed(0),
        messages: state.messages,
    };
}

/**
 * Format intelligence list for report
 */
function formatIntelList(label, items) {
    if (!items || items.length === 0) {
        return `
            <div class="report-item">
                <span class="report-item-label">${label}:</span>
                <span class="report-item-value" style="color: var(--text-muted);">None found</span>
            </div>
        `;
    }
    
    return `
        <div class="report-item">
            <span class="report-item-label">${label}:</span>
            <ul class="report-list">
                ${items.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
            </ul>
        </div>
    `;
}

/**
 * Close modal
 */
function closeModal() {
    document.getElementById('reportModal').classList.remove('active');
}

/**
 * Download report as JSON
 */
function downloadReport() {
    const report = generateReport();
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `scamshield-report-${state.sessionId || 'unknown'}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ============================================================================
// GUVI Callback Functions
// ============================================================================

/**
 * Update callback status display
 */
function updateCallbackStatus(callbackData) {
    const section = document.getElementById('callbackSection');
    const successEl = document.getElementById('callbackSuccess');
    const urlEl = document.getElementById('callbackUrl');
    
    // Show the callback section
    section.style.display = 'block';
    
    // Update status
    if (callbackData.callback_success === true) {
        successEl.textContent = '✅ Sent Successfully';
        successEl.style.color = 'var(--success)';
    } else if (callbackData.callback_success === false) {
        successEl.textContent = '❌ Failed';
        successEl.style.color = 'var(--danger)';
    } else {
        successEl.textContent = '⏳ Pending';
        successEl.style.color = 'var(--warning)';
    }
    
    // Update URL
    if (callbackData.callback_url) {
        urlEl.textContent = callbackData.callback_url;
    }
    
    // Add system message about callback
    addSystemMessage(`🚀 GUVI Callback Triggered! Extraction confidence: ${((state.lastResponse?.extracted_intelligence?.extraction_confidence || 0) * 100).toFixed(0)}%`);
    
    console.log('📡 GUVI Callback Triggered:', callbackData);
}

/**
 * Show callback payload modal
 */
function showCallbackPayload() {
    if (!state.lastCallbackPayload) {
        alert('No callback payload available');
        return;
    }
    
    const modal = document.getElementById('callbackModal');
    const content = document.getElementById('callbackPayloadContent');
    const urlDisplay = document.getElementById('callbackUrlDisplay');
    
    // Build the payload to display (without internal fields)
    const displayPayload = {
        sessionId: state.lastCallbackPayload.sessionId,
        scamDetected: state.lastCallbackPayload.scamDetected,
        totalMessagesExchanged: state.lastCallbackPayload.totalMessagesExchanged,
        extractedIntelligence: state.lastCallbackPayload.extractedIntelligence,
        agentNotes: state.lastCallbackPayload.agentNotes,
    };
    
    // Update URL display
    urlDisplay.textContent = `POST ${state.lastCallbackPayload.callback_url || 'https://hackathon.guvi.in/api/updateHoneyPotFinalResult'}`;
    
    // Format and display JSON
    content.textContent = JSON.stringify(displayPayload, null, 2);
    
    modal.classList.add('active');
}

/**
 * Close callback modal
 */
function closeCallbackModal() {
    document.getElementById('callbackModal').classList.remove('active');
}

/**
 * Copy callback payload to clipboard
 */
function copyCallbackPayload() {
    if (!state.lastCallbackPayload) return;
    
    const displayPayload = {
        sessionId: state.lastCallbackPayload.sessionId,
        scamDetected: state.lastCallbackPayload.scamDetected,
        totalMessagesExchanged: state.lastCallbackPayload.totalMessagesExchanged,
        extractedIntelligence: state.lastCallbackPayload.extractedIntelligence,
        agentNotes: state.lastCallbackPayload.agentNotes,
    };
    
    navigator.clipboard.writeText(JSON.stringify(displayPayload, null, 2))
        .then(() => {
            alert('Callback payload copied to clipboard!');
        })
        .catch(err => {
            console.error('Failed to copy:', err);
            alert('Failed to copy to clipboard');
        });
}

/**
 * Reset callback status
 */
function resetCallbackStatus() {
    const section = document.getElementById('callbackSection');
    section.style.display = 'none';
    state.lastCallbackPayload = null;
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Handle keyboard shortcuts
 */
function handleKeyDown(event) {
    if (event.ctrlKey && event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
