/**
 * ScamShield AI - Voice Honeypot Client (Phase 2)
 *
 * Conversational voice interface: tap to talk, tap to send,
 * AI replies play automatically.
 */

// ============================================================================
// Configuration
// ============================================================================

// Use relative URLs so the UI works on any host/port (local, Docker, HF Spaces)
var VOICE_ENDPOINTS = {
    engage: '/api/v1/voice/engage',
    audio: '/api/v1/voice/audio',
    health: '/api/v1/voice/health',
};
var API_KEY = 'sVlunn0LMQZNAkRYqZB-f1-Ye7rgzjB_E3b1gNxnUV8';
var RECORDING_MIME_TYPES = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/mp4',
];

// ============================================================================
// State
// ============================================================================

var appState = {
    sessionId: null,
    mediaRecorder: null,
    audioStream: null,
    audioChunks: [],
    recordingMimeType: '',
    isRecording: false,
    isProcessing: false,
    currentAudio: null,
    extractedIntel: {
        upi_ids: [],
        bank_accounts: [],
        ifsc_codes: [],
        phone_numbers: [],
        phishing_links: [],
    },
    turnCount: 0,
};

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', function () {
    checkVoiceHealth();
    setInterval(checkVoiceHealth, 30000);
});

// ============================================================================
// Voice Health
// ============================================================================

async function checkVoiceHealth() {
    var dot = document.getElementById('healthDot');
    var label = document.getElementById('healthLabel');
    try {
        var response = await fetch(VOICE_ENDPOINTS.health, {
            headers: { 'x-api-key': API_KEY },
        });
        var data = await response.json();
        dot.className = 'health-dot ' + data.status;
        label.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
    } catch (_err) {
        dot.className = 'health-dot unhealthy';
        label.textContent = 'Offline';
    }
}

// ============================================================================
// Toggle Recording (single button)
// ============================================================================

function toggleRecording() {
    if (appState.isProcessing) return;

    if (appState.isRecording) {
        stopAndSend();
    } else {
        startRecording();
    }
}

function getSupportedMimeType() {
    for (var i = 0; i < RECORDING_MIME_TYPES.length; i++) {
        if (MediaRecorder.isTypeSupported(RECORDING_MIME_TYPES[i])) {
            return RECORDING_MIME_TYPES[i];
        }
    }
    return '';
}

async function startRecording() {
    if (appState.isRecording || appState.isProcessing) return;

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showError('Your browser does not support audio recording.');
        return;
    }

    // Stop any playing AI audio so the mic doesn't pick it up
    stopCurrentAudio();

    try {
        var stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        var mimeType = getSupportedMimeType();
        var options = mimeType ? { mimeType: mimeType } : {};

        appState.recordingMimeType = mimeType || 'audio/webm';
        appState.audioChunks = [];
        appState.audioStream = stream;
        appState.mediaRecorder = new MediaRecorder(stream, options);

        appState.mediaRecorder.addEventListener('dataavailable', function (event) {
            if (event.data && event.data.size > 0) {
                appState.audioChunks.push(event.data);
            }
        });

        appState.mediaRecorder.addEventListener('stop', function () {
            // Release microphone
            if (appState.audioStream) {
                appState.audioStream.getTracks().forEach(function (t) { t.stop(); });
                appState.audioStream = null;
            }
            handleRecordingComplete();
        });

        appState.mediaRecorder.start();
        appState.isRecording = true;
        setUIState('recording');
        hideError();
    } catch (err) {
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
            showError('Microphone access denied. Please allow microphone permission.');
        } else if (err.name === 'NotFoundError') {
            showError('No microphone detected. Please connect a microphone.');
        } else {
            showError('Failed to start recording: ' + err.message);
        }
    }
}

function stopAndSend() {
    if (!appState.isRecording || !appState.mediaRecorder) return;
    appState.mediaRecorder.stop();
    appState.isRecording = false;
}

function handleRecordingComplete() {
    if (appState.audioChunks.length === 0) {
        showError('No audio captured. Please try again.');
        setUIState('ready');
        return;
    }

    var blob = new Blob(appState.audioChunks, { type: appState.recordingMimeType });
    var ext = appState.recordingMimeType.indexOf('webm') !== -1 ? 'webm'
        : appState.recordingMimeType.indexOf('ogg') !== -1 ? 'ogg'
        : appState.recordingMimeType.indexOf('mp4') !== -1 ? 'mp4'
        : 'webm';

    var file = new File([blob], 'recording.' + ext, { type: appState.recordingMimeType });
    sendAudioToAPI(file);
}

// ============================================================================
// File Upload (alternative input)
// ============================================================================

function uploadAudio() {
    if (appState.isRecording || appState.isProcessing) return;
    document.getElementById('audioFileInput').click();
}

function handleFileSelect(event) {
    var files = event.target.files;
    if (!files || files.length === 0) return;

    var file = files[0];
    if (!file.type.startsWith('audio/') && file.type !== 'application/octet-stream') {
        showError('Please select a valid audio file.');
        event.target.value = '';
        return;
    }
    if (file.size > 25 * 1024 * 1024) {
        showError('File too large. Maximum 25 MB.');
        event.target.value = '';
        return;
    }

    sendAudioToAPI(file);
    event.target.value = '';
}

// ============================================================================
// API Communication
// ============================================================================

async function sendAudioToAPI(audioFile) {
    if (appState.isProcessing) return;

    appState.isProcessing = true;
    setUIState('processing');

    clearWelcome();
    addMessage('system', 'Listening...');

    var formData = new FormData();
    formData.append('audio_file', audioFile);

    var languageSelect = document.getElementById('languageSelect');
    var language = languageSelect ? languageSelect.value : 'auto';
    if (language && language !== 'auto') {
        formData.append('language', language);
    }
    if (appState.sessionId) {
        formData.append('session_id', appState.sessionId);
    }

    try {
        var startTime = Date.now();
        var response = await fetch(VOICE_ENDPOINTS.engage, {
            method: 'POST',
            headers: { 'x-api-key': API_KEY },
            body: formData,
        });

        var elapsed = Date.now() - startTime;

        if (!response.ok) {
            var errorBody = null;
            try { errorBody = await response.json(); } catch (_e) { /* ignore */ }
            var errorMsg = (errorBody && errorBody.detail)
                ? (typeof errorBody.detail === 'string' ? errorBody.detail : errorBody.detail.message || JSON.stringify(errorBody.detail))
                : 'Server returned HTTP ' + response.status;
            throw new Error(errorMsg);
        }

        var data = await response.json();
        handleAPIResponse(data, elapsed);

    } catch (err) {
        removeLastSystemMessage();
        addMessage('system', 'Error: ' + err.message);
        showError(err.message);
    } finally {
        appState.isProcessing = false;
        setUIState('ready');
    }
}

// ============================================================================
// Response Handling + Auto-Play
// ============================================================================

function handleAPIResponse(data, elapsedMs) {
    appState.sessionId = data.session_id;
    appState.turnCount = data.turn_count || 0;
    hideError();
    removeLastSystemMessage();

    updateSessionDisplay();
    updateResponseTime(elapsedMs, data.processing_time_ms);

    // Show user's transcribed speech
    if (data.transcription && data.transcription.text) {
        addMessage('user', data.transcription.text, {
            language: data.transcription.language,
            confidence: data.transcription.confidence,
        });
    }

    // Show AI reply with audio player
    // Use relative URL if not already absolute (works on any host/port)
    var audioUrl = null;
    if (data.ai_reply_audio_url) {
        audioUrl = data.ai_reply_audio_url.startsWith('http')
            ? data.ai_reply_audio_url
            : data.ai_reply_audio_url;
    }

    addMessage('ai', data.ai_reply_text, {
        audioUrl: audioUrl,
        turnCount: data.turn_count,
        scamType: data.scam_type,
    });

    // Auto-play the AI audio reply
    if (audioUrl) {
        autoPlayAudio(audioUrl);
    }

    updateTranscriptionMetadata(data.transcription);
    updateDetection(data);
    updateVoiceFraud(data.voice_fraud);
    updateIntelligence(data.extracted_intelligence);
}

/**
 * Auto-play AI audio response. Stops any currently playing audio first.
 */
function autoPlayAudio(url) {
    stopCurrentAudio();

    var audio = new Audio(url);
    appState.currentAudio = audio;

    audio.addEventListener('ended', function () {
        appState.currentAudio = null;
    });

    audio.addEventListener('error', function () {
        appState.currentAudio = null;
    });

    // Browsers may block autoplay; catch and ignore
    var playPromise = audio.play();
    if (playPromise && playPromise.catch) {
        playPromise.catch(function () {
            // Autoplay blocked; user can click the inline player instead
        });
    }
}

function stopCurrentAudio() {
    if (appState.currentAudio) {
        try {
            appState.currentAudio.pause();
            appState.currentAudio.currentTime = 0;
        } catch (_e) { /* ignore */ }
        appState.currentAudio = null;
    }
}

// ============================================================================
// UI - Messages
// ============================================================================

function clearWelcome() {
    var welcome = document.getElementById('conversationWelcome');
    if (welcome) welcome.remove();
}

function removeLastSystemMessage() {
    var container = document.getElementById('conversationContainer');
    var msgs = container.querySelectorAll('.message.system');
    if (msgs.length > 0) {
        msgs[msgs.length - 1].remove();
    }
}

function addMessage(type, text, meta) {
    meta = meta || {};
    var container = document.getElementById('conversationContainer');

    var msgEl = document.createElement('div');
    msgEl.className = 'message ' + type;

    if (type === 'system') {
        msgEl.innerHTML = '<div class="message-bubble">' + escapeHtml(text) + '</div>';
        container.appendChild(msgEl);
        container.scrollTop = container.scrollHeight;
        return;
    }

    var avatar = type === 'user' ? '&#x1F9B9;' : '&#x1F916;';
    var senderName = type === 'user' ? 'You' : 'AI Agent';

    var metaHtml = '';
    if (type === 'user' && meta.language) {
        metaHtml = '<div class="message-meta">'
            + '<span>' + escapeHtml(meta.language) + '</span>'
            + '<span>' + formatPercent(meta.confidence) + '</span>'
            + '</div>';
    }
    if (type === 'ai' && meta.turnCount) {
        metaHtml = '<div class="message-meta">'
            + '<span>Turn ' + meta.turnCount + '</span>'
            + (meta.scamType ? '<span>' + escapeHtml(meta.scamType) + '</span>' : '')
            + '</div>';
    }

    // Inline audio player (for replay; autoplay handled separately)
    var audioHtml = '';
    if (type === 'ai' && meta.audioUrl) {
        audioHtml = '<div class="ai-audio-player">'
            + '<audio controls preload="auto" src="' + escapeAttr(meta.audioUrl) + '"></audio>'
            + '</div>';
    }

    msgEl.innerHTML = '<div class="message-avatar">' + avatar + '</div>'
        + '<div class="message-body">'
        + '<div class="message-sender">' + escapeHtml(senderName) + '</div>'
        + '<div class="message-bubble">' + escapeHtml(text) + '</div>'
        + audioHtml
        + metaHtml
        + '</div>';

    container.appendChild(msgEl);
    container.scrollTop = container.scrollHeight;
}

// ============================================================================
// UI State Machine
// ============================================================================

function setUIState(state) {
    var btn = document.getElementById('btnTalk');
    var icon = document.getElementById('talkButtonIcon');
    var label = document.getElementById('talkButtonLabel');
    var statusEl = document.getElementById('recordingStatus');
    var statusLabel = document.getElementById('recordingLabel');
    var uploadBtn = document.getElementById('btnUploadAudio');

    btn.classList.remove('recording', 'processing');
    statusEl.className = 'recording-status ' + state;

    if (state === 'ready') {
        icon.innerHTML = '&#x1F3A4;';
        label.textContent = 'Tap to Talk';
        statusLabel.textContent = 'Ready';
        btn.disabled = false;
        uploadBtn.disabled = false;
    } else if (state === 'recording') {
        btn.classList.add('recording');
        icon.innerHTML = '&#x23F9;';
        label.textContent = 'Tap to Send';
        statusLabel.textContent = 'Recording...';
        btn.disabled = false;
        uploadBtn.disabled = true;
    } else if (state === 'processing') {
        btn.classList.add('processing');
        icon.innerHTML = '&#x23F3;';
        label.textContent = 'Thinking...';
        statusLabel.textContent = 'Processing...';
        btn.disabled = true;
        uploadBtn.disabled = true;
    }
}

// ============================================================================
// Metadata Panel Updates
// ============================================================================

function updateTranscriptionMetadata(transcription) {
    if (!transcription) return;
    setText('metaTranscription', transcription.text || '-');
    setText('metaASRLanguage', transcription.language || '-');
    setText('metaASRConfidence', formatPercent(transcription.confidence));
}

function updateDetection(data) {
    var container = document.getElementById('detectionResult');
    var isScam = data.scam_detected;
    var confidence = data.scam_confidence || 0;
    var percent = (confidence * 100).toFixed(0);

    container.className = 'detection-result ' + (isScam ? 'scam' : 'safe');
    container.innerHTML = '<div class="detection-badge">'
        + (isScam ? 'SCAM DETECTED' : 'SAFE')
        + '</div>'
        + '<div class="confidence-bar"><div class="confidence-fill" style="width:' + percent + '%"></div></div>'
        + '<div class="detection-details">'
        + 'Confidence: ' + percent + '%'
        + (data.scam_type ? ' | Type: ' + escapeHtml(data.scam_type) : '')
        + ' | Turn: ' + (data.turn_count || 0)
        + '</div>';
}

function updateVoiceFraud(fraud) {
    var section = document.getElementById('voiceFraudSection');
    var container = document.getElementById('voiceFraudResult');
    if (!fraud) { section.style.display = 'none'; return; }

    section.style.display = 'block';
    var riskClass = fraud.risk_level === 'high' ? 'high-risk'
        : fraud.risk_level === 'medium' ? 'medium-risk' : 'low-risk';

    container.className = 'fraud-result ' + riskClass;
    container.innerHTML = '<div class="metadata-grid">'
        + '<div class="metadata-card"><span class="metadata-label">Synthetic</span>'
        + '<span class="metadata-value ' + (fraud.is_synthetic ? 'danger' : 'success') + '">'
        + (fraud.is_synthetic ? 'Yes' : 'No') + '</span></div>'
        + '<div class="metadata-card"><span class="metadata-label">Confidence</span>'
        + '<span class="metadata-value">' + formatPercent(fraud.confidence) + '</span></div>'
        + '<div class="metadata-card full-width"><span class="metadata-label">Risk</span>'
        + '<span class="metadata-value ' + riskClass.replace('-risk', '') + '">'
        + fraud.risk_level.toUpperCase() + '</span></div></div>';
}

function updateIntelligence(intel) {
    if (!intel) return;
    mergeIntelArray('upi_ids', intel.upi_ids);
    mergeIntelArray('bank_accounts', intel.bank_accounts);
    mergeIntelArray('ifsc_codes', intel.ifsc_codes);
    mergeIntelArray('phone_numbers', intel.phone_numbers);
    mergeIntelArray('phishing_links', intel.phishing_links);

    renderIntelValue('intelUPI', appState.extractedIntel.upi_ids);
    renderIntelValue('intelBank', appState.extractedIntel.bank_accounts);
    renderIntelValue('intelPhone', appState.extractedIntel.phone_numbers);
    renderIntelValue('intelLinks', appState.extractedIntel.phishing_links);

    var conf = intel.extraction_confidence;
    var confEl = document.getElementById('intelConfidence');
    if (confEl) {
        confEl.textContent = conf != null ? formatPercent(conf) : '-';
        confEl.className = 'intel-value' + (conf > 0 ? ' has-data' : '');
    }
}

function mergeIntelArray(key, incoming) {
    if (!incoming || !incoming.length) return;
    var set = {};
    appState.extractedIntel[key].forEach(function (v) { set[v] = true; });
    incoming.forEach(function (v) { set[v] = true; });
    appState.extractedIntel[key] = Object.keys(set);
}

function renderIntelValue(elementId, values) {
    var el = document.getElementById(elementId);
    if (!el) return;
    if (values && values.length > 0) {
        el.textContent = values.join(', ');
        el.className = 'intel-value has-data';
    } else {
        el.textContent = '-';
        el.className = 'intel-value';
    }
}

// ============================================================================
// Session / Display Helpers
// ============================================================================

function updateSessionDisplay() {
    var el = document.getElementById('sessionIdDisplay');
    el.value = appState.sessionId || '';
}

function updateResponseTime(clientMs, serverMs) {
    var el = document.getElementById('responseTime');
    var parts = [];
    if (clientMs != null) parts.push('RTT: ' + clientMs + 'ms');
    if (serverMs != null) parts.push('Server: ' + serverMs + 'ms');
    el.textContent = parts.length > 0 ? parts.join(' | ') : '-';
}

function newSession() {
    stopCurrentAudio();
    appState.sessionId = null;
    appState.turnCount = 0;
    appState.extractedIntel = {
        upi_ids: [], bank_accounts: [], ifsc_codes: [],
        phone_numbers: [], phishing_links: [],
    };

    var container = document.getElementById('conversationContainer');
    container.innerHTML = '<div id="conversationWelcome" class="conversation-welcome">'
        + '<div class="welcome-icon">&#x1F3A4;</div>'
        + '<h3>Voice Honeypot Testing</h3>'
        + '<p>Tap the microphone to speak. When you stop, the AI will '
        + 'transcribe your words, detect scam intent, and reply with voice automatically.</p>'
        + '</div>';

    updateSessionDisplay();
    document.getElementById('detectionResult').className = 'detection-result';
    document.getElementById('detectionResult').innerHTML = '<div class="no-data">Send audio to see detection results</div>';
    setText('metaTranscription', '-');
    setText('metaASRLanguage', '-');
    setText('metaASRConfidence', '-');
    document.getElementById('voiceFraudSection').style.display = 'none';
    renderIntelValue('intelUPI', []);
    renderIntelValue('intelBank', []);
    renderIntelValue('intelPhone', []);
    renderIntelValue('intelLinks', []);
    var confEl = document.getElementById('intelConfidence');
    if (confEl) { confEl.textContent = '-'; confEl.className = 'intel-value'; }
    document.getElementById('responseTime').textContent = '-';
    hideError();
}

// ============================================================================
// Error Handling
// ============================================================================

function showError(message) {
    var banner = document.getElementById('errorBanner');
    banner.textContent = message;
    banner.classList.add('visible');
}

function hideError() {
    var banner = document.getElementById('errorBanner');
    banner.classList.remove('visible');
    banner.textContent = '';
}

// ============================================================================
// Utility
// ============================================================================

function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

function escapeAttr(text) {
    return (text || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function formatPercent(value) {
    if (value == null) return '-';
    return (value * 100).toFixed(1) + '%';
}

function setText(id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text;
}
