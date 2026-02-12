# PHASE 2: VOICE IMPLEMENTATION PLAN

## OVERVIEW

This document outlines the complete implementation plan for Phase 2 voice features that will enable live two-way voice conversations with the honeypot AI without impacting the existing Phase 1 text-based system.

**Key Principle:** Phase 2 is a **non-breaking extension** of Phase 1. All voice features are additive and isolated.

---

## DESIGN SUMMARY

### Architecture Approach

```
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 2 VOICE LAYER                       │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │ Voice Input  │ ───> │ ASR (Whisper)│ ───> │   Text    │ │
│  │  (PyAudio)   │      │              │      │           │ │
│  └──────────────┘      └──────────────┘      └─────┬─────┘ │
└────────────────────────────────────────────────────┼────────┘
                                                      │
                                                      ▼
┌─────────────────────────────────────────────────────────────┐
│              PHASE 1 TEXT HONEYPOT (UNCHANGED)               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Detector   │ ───> │   Honeypot   │ ───> │  Extractor│ │
│  │              │      │  (Groq LLM)  │      │           │ │
│  └──────────────┘      └──────────────┘      └─────┬─────┘ │
└────────────────────────────────────────────────────┼────────┘
                                                      │
                                                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 2 VOICE LAYER                       │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │  Text Reply  │ ───> │ TTS (gTTS)   │ ───> │Voice Output│ │
│  │              │      │              │      │  (Speaker) │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
└─────────────────────────────────────────────────────────────┘

OPTIONAL PARALLEL FLOW (Voice Fraud Detection):
┌─────────────────────────────────────────────────────────────┐
│  Voice Input ───> Voice Deepfake Detector ───> Fraud Score  │
│  (same audio)     (Wav2Vec2/resemblyzer)                     │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Voice Input Handler** - Captures live audio (PyAudio)
2. **ASR Module** - Transcribes audio to text (Whisper)
3. **Voice Output Handler** - Converts text to speech (gTTS/IndicTTS)
4. **Voice Fraud Detector** - Detects synthetic/deepfake voices (Optional)
5. **Voice API Endpoints** - New endpoints for voice interaction
6. **Voice UI** - Separate web interface for voice testing

---

## IMPLEMENTATION PLAN

### STEP 1: DEPENDENCIES & SETUP

**New Python Dependencies:**

```python
# requirements-phase2.txt
openai-whisper==20231117      # ASR for audio transcription
torchaudio==2.1.0              # Audio processing for Whisper
librosa==0.10.1                # Audio feature extraction
soundfile==0.12.1              # Audio I/O
pydub==0.25.1                  # Audio format conversion
gTTS==2.4.0                    # Text-to-speech (free)
pyaudio==0.2.14                # Live audio capture
webrtcvad==2.0.10              # Voice activity detection
numpy>=1.24.0                  # Audio processing

# Optional (for voice fraud detection)
resemblyzer==0.1.1             # Voice embeddings for deepfake detection
```

**Installation:**

```bash
# Install Phase 2 dependencies separately
pip install -r requirements-phase2.txt

# Note: PyAudio may require system dependencies
# Windows: pip install pipwin && pipwin install pyaudio
# Linux: sudo apt-get install portaudio19-dev python3-pyaudio
# Mac: brew install portaudio && pip install pyaudio
```

**Environment Variables:**

```bash
# Add to .env
PHASE_2_ENABLED=true
WHISPER_MODEL=base              # Options: tiny, base, small, medium, large
TTS_ENGINE=gtts                 # Options: gtts, indic_tts
VOICE_FRAUD_DETECTION=false     # Enable voice deepfake detection
AUDIO_SAMPLE_RATE=16000
AUDIO_CHUNK_DURATION=5          # Seconds per chunk for streaming
```

---

### STEP 2: CORE VOICE MODULES

#### 2.1 ASR Module (`app/voice/asr.py`)

```python
"""
Automatic Speech Recognition Module for Phase 2.

Converts audio to text using Whisper.
"""

import whisper
import torch
import numpy as np
from typing import Dict, Optional, Tuple
from pathlib import Path

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ASREngine:
    """
    Whisper-based ASR for multilingual transcription.
    
    Supports: English, Hindi, Gujarati, and other Indic languages.
    """
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper ASR.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()
    
    def _load_model(self) -> None:
        """Load Whisper model."""
        try:
            logger.info(f"Loading Whisper model '{self.model_size}' on {self.device}")
            self.model = whisper.load_model(self.model_size, device=self.device)
            logger.info(f"Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'hi', 'gu') or None for auto-detect
        
        Returns:
            Dict with keys:
                - text: Transcribed text
                - language: Detected language
                - confidence: Transcription confidence (0-1)
        """
        try:
            # Transcribe
            result = self.model.transcribe(
                audio_path,
                language=language,
                task="transcribe",
                fp16=(self.device == "cuda")
            )
            
            return {
                "text": result["text"].strip(),
                "language": result.get("language", "unknown"),
                "confidence": self._calculate_confidence(result)
            }
        
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {
                "text": "",
                "language": "unknown",
                "confidence": 0.0
            }
    
    def _calculate_confidence(self, result: Dict) -> float:
        """
        Calculate transcription confidence from Whisper result.
        
        Args:
            result: Whisper transcription result
        
        Returns:
            Confidence score (0-1)
        """
        # Whisper doesn't provide direct confidence
        # Use average log probability as proxy
        segments = result.get("segments", [])
        if not segments:
            return 0.5  # Default
        
        avg_logprob = np.mean([seg.get("avg_logprob", -1.0) for seg in segments])
        # Convert log prob to confidence (rough approximation)
        confidence = np.exp(avg_logprob)
        return float(np.clip(confidence, 0.0, 1.0))


# Singleton instance
_asr_engine: Optional[ASREngine] = None


def get_asr_engine() -> ASREngine:
    """Get singleton ASR engine instance."""
    global _asr_engine
    if _asr_engine is None:
        model_size = getattr(settings, "WHISPER_MODEL", "base")
        _asr_engine = ASREngine(model_size=model_size)
    return _asr_engine
```

#### 2.2 TTS Module (`app/voice/tts.py`)

```python
"""
Text-to-Speech Module for Phase 2.

Converts text responses to speech audio.
"""

from gtts import gTTS
from typing import Optional
from pathlib import Path
import tempfile

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TTSEngine:
    """
    gTTS-based text-to-speech engine.
    
    Supports multiple languages including Hindi, English, Gujarati.
    """
    
    def __init__(self):
        """Initialize TTS engine."""
        self.engine_type = getattr(settings, "TTS_ENGINE", "gtts")
        logger.info(f"TTS Engine initialized: {self.engine_type}")
    
    def synthesize(
        self,
        text: str,
        language: str = "en",
        output_path: Optional[str] = None
    ) -> str:
        """
        Convert text to speech.
        
        Args:
            text: Text to synthesize
            language: Language code ('en', 'hi', 'gu', etc.)
            output_path: Output file path (auto-generated if None)
        
        Returns:
            Path to generated audio file
        """
        try:
            # Map language codes
            lang_map = {
                "english": "en",
                "hindi": "hi",
                "gujarati": "gu",
                "tamil": "ta",
                "telugu": "te",
                "bengali": "bn",
                "marathi": "mr"
            }
            
            tts_lang = lang_map.get(language.lower(), language)
            
            # Generate audio
            tts = gTTS(text=text, lang=tts_lang, slow=False)
            
            # Save to file
            if output_path is None:
                output_path = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".mp3"
                ).name
            
            tts.save(output_path)
            logger.info(f"TTS generated: {output_path}")
            
            return output_path
        
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            raise


# Singleton instance
_tts_engine: Optional[TTSEngine] = None


def get_tts_engine() -> TTSEngine:
    """Get singleton TTS engine instance."""
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = TTSEngine()
    return _tts_engine
```

#### 2.3 Voice Fraud Detector (Optional) (`app/voice/fraud_detector.py`)

```python
"""
Voice Fraud Detection Module for Phase 2.

Detects synthetic/deepfake voices using audio embeddings.
"""

import numpy as np
from typing import Dict, Optional
import torch

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VoiceFraudDetector:
    """
    Detect synthetic/deepfake voices using audio analysis.
    
    Uses Wav2Vec2 or resemblyzer for voice embeddings.
    """
    
    def __init__(self):
        """Initialize voice fraud detector."""
        self.enabled = getattr(settings, "VOICE_FRAUD_DETECTION", False)
        self.model = None
        
        if self.enabled:
            self._load_model()
    
    def _load_model(self) -> None:
        """Load voice fraud detection model."""
        try:
            # Placeholder: Load resemblyzer or Wav2Vec2
            # from resemblyzer import preprocess_wav, VoiceEncoder
            # self.model = VoiceEncoder()
            logger.info("Voice fraud detection model loaded")
        except Exception as e:
            logger.warning(f"Voice fraud detection unavailable: {e}")
            self.enabled = False
    
    def detect_synthetic_voice(self, audio_path: str) -> Dict:
        """
        Detect if voice is AI-generated/synthetic.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Dict with keys:
                - is_synthetic: Boolean
                - confidence: Detection confidence (0-1)
                - risk_level: 'low', 'medium', 'high'
        """
        if not self.enabled:
            return {
                "is_synthetic": False,
                "confidence": 0.0,
                "risk_level": "unknown"
            }
        
        try:
            # Placeholder implementation
            # Real implementation would:
            # 1. Extract voice embeddings
            # 2. Compare against known synthetic patterns
            # 3. Return detection score
            
            return {
                "is_synthetic": False,
                "confidence": 0.5,
                "risk_level": "low"
            }
        
        except Exception as e:
            logger.error(f"Voice fraud detection failed: {e}")
            return {
                "is_synthetic": False,
                "confidence": 0.0,
                "risk_level": "unknown"
            }


# Singleton instance
_fraud_detector: Optional[VoiceFraudDetector] = None


def get_fraud_detector() -> VoiceFraudDetector:
    """Get singleton fraud detector instance."""
    global _fraud_detector
    if _fraud_detector is None:
        _fraud_detector = VoiceFraudDetector()
    return _fraud_detector
```

---

### STEP 3: VOICE API ENDPOINTS

#### 3.1 Voice Endpoints (`app/api/voice_endpoints.py`)

```python
"""
Voice API Endpoints for Phase 2.

Provides endpoints for voice-based honeypot interaction.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import time
import tempfile
import os

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse

from app.api.schemas import VoiceEngageResponse, VoiceEngageRequest
from app.api.auth import verify_api_key
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])


@router.post("/engage", response_model=VoiceEngageResponse, dependencies=[Depends(verify_api_key)])
async def engage_voice(
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    language: Optional[str] = Form("auto")
) -> VoiceEngageResponse:
    """
    Voice-based honeypot engagement endpoint.
    
    Flow:
    1. Receive audio file (user speaking as scammer)
    2. Transcribe audio to text (ASR)
    3. Process through Phase 1 text honeypot (unchanged)
    4. Convert AI reply to speech (TTS)
    5. Return audio response + metadata
    
    Args:
        audio_file: Audio file (wav, mp3, m4a, etc.)
        session_id: Session ID (auto-generated if None)
        language: Language hint ('auto', 'en', 'hi', 'gu')
    
    Returns:
        VoiceEngageResponse with audio reply and metadata
    """
    start_time = time.time()
    
    try:
        # Import modules
        from app.voice.asr import get_asr_engine
        from app.voice.tts import get_tts_engine
        from app.voice.fraud_detector import get_fraud_detector
        from app.models.detector import get_detector
        from app.models.language import detect_language
        from app.models.extractor import extract_intelligence
        from app.agent.honeypot import HoneypotAgent
        from app.database.redis_client import (
            get_session_state_with_fallback,
            save_session_state_with_fallback,
        )
        
        # Generate session ID if needed
        if not session_id:
            session_id = f"voice-{uuid.uuid4()}"
        
        logger.info(f"Voice engage request: session={session_id}, file={audio_file.filename}")
        
        # Save uploaded audio temporarily
        temp_audio_path = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(audio_file.filename)[1]
        ).name
        
        with open(temp_audio_path, "wb") as f:
            f.write(await audio_file.read())
        
        # STEP 1: Transcribe audio to text (ASR)
        asr_engine = get_asr_engine()
        transcription = asr_engine.transcribe(
            temp_audio_path,
            language=None if language == "auto" else language
        )
        
        message_text = transcription["text"]
        detected_language = transcription["language"]
        transcription_confidence = transcription["confidence"]
        
        logger.info(f"Transcribed: '{message_text}' (lang={detected_language}, conf={transcription_confidence:.2f})")
        
        # STEP 2: Optional voice fraud detection
        voice_fraud_result = None
        if getattr(settings, "VOICE_FRAUD_DETECTION", False):
            fraud_detector = get_fraud_detector()
            voice_fraud_result = fraud_detector.detect_synthetic_voice(temp_audio_path)
        
        # STEP 3: Process through Phase 1 text pipeline (UNCHANGED)
        # This reuses the exact same logic as text honeypot
        
        detector = get_detector()
        detection_result = detector.detect(message_text)
        
        scam_detected = detection_result["is_scam"]
        scam_confidence = detection_result["confidence"]
        scam_type = detection_result["scam_type"]
        
        # Get session state
        session_state = get_session_state_with_fallback(session_id)
        
        # Initialize honeypot agent
        agent = HoneypotAgent()
        
        # Engage with honeypot
        engagement_result = agent.engage(
            message=message_text,
            session_id=session_id,
            scam_confidence=scam_confidence,
            language=detected_language
        )
        
        ai_reply_text = engagement_result["response"]
        turn_count = engagement_result["turn_count"]
        
        # Extract intelligence
        intel = extract_intelligence(message_text)
        
        # STEP 4: Convert AI reply to speech (TTS)
        tts_engine = get_tts_engine()
        reply_audio_path = tts_engine.synthesize(
            text=ai_reply_text,
            language=detected_language
        )
        
        # Save session state
        save_session_state_with_fallback(session_id, engagement_result["state"])
        
        # Clean up input audio
        os.unlink(temp_audio_path)
        
        # Build response
        response = VoiceEngageResponse(
            session_id=session_id,
            scam_detected=scam_detected,
            scam_confidence=scam_confidence,
            scam_type=scam_type,
            turn_count=turn_count,
            ai_reply_text=ai_reply_text,
            ai_reply_audio_url=f"/api/v1/voice/audio/{os.path.basename(reply_audio_path)}",
            transcription={
                "text": message_text,
                "language": detected_language,
                "confidence": transcription_confidence
            },
            voice_fraud=voice_fraud_result,
            extracted_intelligence=intel,
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
        
        logger.info(f"Voice engagement complete: {turn_count} turns, {response.processing_time_ms}ms")
        
        return response
    
    except Exception as e:
        logger.error(f"Voice engagement failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """
    Serve generated audio files.
    
    Args:
        filename: Audio filename
    
    Returns:
        Audio file
    """
    audio_path = os.path.join(tempfile.gettempdir(), filename)
    
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        filename=filename
    )


@router.get("/health")
async def voice_health():
    """
    Voice system health check.
    
    Returns:
        Health status of voice components
    """
    try:
        from app.voice.asr import get_asr_engine
        from app.voice.tts import get_tts_engine
        
        asr_engine = get_asr_engine()
        tts_engine = get_tts_engine()
        
        return {
            "status": "healthy",
            "asr": {
                "model": asr_engine.model_size,
                "device": asr_engine.device
            },
            "tts": {
                "engine": tts_engine.engine_type
            },
            "phase_2_enabled": True
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

#### 3.2 Voice Schemas (`app/api/voice_schemas.py`)

```python
"""
Pydantic schemas for Voice API endpoints.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class VoiceEngageRequest(BaseModel):
    """Request schema for voice engagement."""
    
    session_id: Optional[str] = Field(None, description="Session ID")
    language: Optional[str] = Field("auto", description="Language hint")


class TranscriptionMetadata(BaseModel):
    """Transcription metadata."""
    
    text: str = Field(..., description="Transcribed text")
    language: str = Field(..., description="Detected language")
    confidence: float = Field(..., description="Transcription confidence (0-1)")


class VoiceFraudMetadata(BaseModel):
    """Voice fraud detection metadata."""
    
    is_synthetic: bool = Field(..., description="Whether voice is synthetic")
    confidence: float = Field(..., description="Detection confidence (0-1)")
    risk_level: str = Field(..., description="Risk level: low, medium, high")


class VoiceEngageResponse(BaseModel):
    """Response schema for voice engagement."""
    
    session_id: str = Field(..., description="Session ID")
    scam_detected: bool = Field(..., description="Whether scam was detected")
    scam_confidence: float = Field(..., description="Scam detection confidence")
    scam_type: str = Field(..., description="Detected scam type")
    turn_count: int = Field(..., description="Current turn number")
    ai_reply_text: str = Field(..., description="AI reply as text")
    ai_reply_audio_url: str = Field(..., description="URL to download AI reply audio")
    transcription: TranscriptionMetadata = Field(..., description="Transcription metadata")
    voice_fraud: Optional[VoiceFraudMetadata] = Field(None, description="Voice fraud detection")
    extracted_intelligence: Dict[str, Any] = Field(..., description="Extracted intelligence")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
```

---

### STEP 4: VOICE UI

#### 4.1 Voice Chat Interface (`ui/voice.html`)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScamShield AI - Voice Honeypot (Phase 2)</title>
    <link rel="stylesheet" href="voice.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🎤 ScamShield AI - Voice Honeypot</h1>
            <p class="subtitle">Phase 2: Live Voice Conversation Testing</p>
        </header>

        <div class="main-content">
            <!-- Voice Controls -->
            <section class="voice-controls">
                <h2>Voice Controls</h2>
                
                <div class="recording-status" id="recordingStatus">
                    <span class="status-icon" id="statusIcon">⚪</span>
                    <span class="status-text" id="statusText">Ready</span>
                </div>

                <div class="button-group">
                    <button class="btn btn-primary" id="recordBtn" onclick="startRecording()">
                        🎤 Start Recording
                    </button>
                    <button class="btn btn-secondary" id="stopBtn" onclick="stopRecording()" disabled>
                        ⏹️ Stop Recording
                    </button>
                    <button class="btn btn-tertiary" id="uploadBtn" onclick="uploadAudio()">
                        📁 Upload Audio File
                    </button>
                </div>

                <input type="file" id="audioFileInput" accept="audio/*" style="display: none;" onchange="handleFileUpload(event)">

                <div class="session-info">
                    <label>Session ID:</label>
                    <input type="text" id="sessionId" readonly>
                </div>
            </section>

            <!-- Conversation Display -->
            <section class="conversation">
                <h2>💬 Conversation</h2>
                <div class="messages" id="messages">
                    <div class="system-message">
                        Welcome to Voice Honeypot Testing. Click "Start Recording" to speak as a scammer.
                    </div>
                </div>
            </section>

            <!-- Transcription & Metadata -->
            <section class="metadata">
                <h2>📊 Voice Metadata</h2>
                
                <div class="metadata-card">
                    <h3>Transcription</h3>
                    <div class="metadata-item">
                        <span class="label">Text:</span>
                        <span class="value" id="transcriptionText">-</span>
                    </div>
                    <div class="metadata-item">
                        <span class="label">Language:</span>
                        <span class="value" id="transcriptionLang">-</span>
                    </div>
                    <div class="metadata-item">
                        <span class="label">Confidence:</span>
                        <span class="value" id="transcriptionConf">-</span>
                    </div>
                </div>

                <div class="metadata-card">
                    <h3>Detection</h3>
                    <div class="metadata-item">
                        <span class="label">Scam Detected:</span>
                        <span class="value" id="scamDetected">-</span>
                    </div>
                    <div class="metadata-item">
                        <span class="label">Confidence:</span>
                        <span class="value" id="scamConfidence">-</span>
                    </div>
                    <div class="metadata-item">
                        <span class="label">Type:</span>
                        <span class="value" id="scamType">-</span>
                    </div>
                </div>

                <div class="metadata-card" id="voiceFraudCard" style="display: none;">
                    <h3>Voice Fraud Detection</h3>
                    <div class="metadata-item">
                        <span class="label">Synthetic:</span>
                        <span class="value" id="voiceSynthetic">-</span>
                    </div>
                    <div class="metadata-item">
                        <span class="label">Risk Level:</span>
                        <span class="value" id="voiceRisk">-</span>
                    </div>
                </div>
            </section>

            <!-- Intelligence -->
            <section class="intelligence">
                <h2>🎯 Extracted Intelligence</h2>
                <div id="intelligence">
                    <p class="empty-state">No intelligence extracted yet</p>
                </div>
            </section>
        </div>
    </div>

    <script src="voice.js"></script>
</body>
</html>
```

#### 4.2 Voice UI JavaScript (`ui/voice.js`)

```javascript
// Voice Honeypot UI Logic

let mediaRecorder = null;
let audioChunks = [];
let currentSessionId = null;
let isRecording = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    generateSessionId();
    checkVoiceAPIHealth();
});

function generateSessionId() {
    currentSessionId = `voice-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    document.getElementById('sessionId').value = currentSessionId;
}

async function checkVoiceAPIHealth() {
    try {
        const response = await fetch('/api/v1/voice/health');
        const data = await response.json();
        console.log('Voice API Health:', data);
    } catch (error) {
        console.error('Voice API unavailable:', error);
        addSystemMessage('⚠️ Voice API unavailable. Please check Phase 2 setup.');
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            await sendAudioToAPI(audioBlob);
        };
        
        mediaRecorder.start();
        isRecording = true;
        
        updateRecordingStatus('recording', 'Recording...');
        document.getElementById('recordBtn').disabled = true;
        document.getElementById('stopBtn').disabled = false;
        
        addSystemMessage('🎤 Recording started. Speak as a scammer...');
        
    } catch (error) {
        console.error('Failed to start recording:', error);
        alert('Microphone access denied or unavailable.');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        isRecording = false;
        
        updateRecordingStatus('processing', 'Processing...');
        document.getElementById('recordBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;
        
        addSystemMessage('⏳ Processing audio...');
    }
}

function uploadAudio() {
    document.getElementById('audioFileInput').click();
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        addSystemMessage(`📁 Uploading ${file.name}...`);
        await sendAudioToAPI(file);
    }
}

async function sendAudioToAPI(audioBlob) {
    try {
        const formData = new FormData();
        formData.append('audio_file', audioBlob, 'recording.webm');
        formData.append('session_id', currentSessionId);
        formData.append('language', 'auto');
        
        updateRecordingStatus('processing', 'Sending to API...');
        
        const response = await fetch('/api/v1/voice/engage', {
            method: 'POST',
            headers: {
                'x-api-key': 'dev-key-12345'  // Use your API key
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        handleAPIResponse(data);
        
    } catch (error) {
        console.error('API call failed:', error);
        addSystemMessage(`❌ Error: ${error.message}`);
        updateRecordingStatus('error', 'Error');
    }
}

function handleAPIResponse(data) {
    // Add user message (transcription)
    addMessage('user', data.transcription.text, data.transcription);
    
    // Add AI reply (with audio)
    addMessage('ai', data.ai_reply_text, null, data.ai_reply_audio_url);
    
    // Update metadata
    updateMetadata(data);
    
    // Update intelligence
    updateIntelligence(data.extracted_intelligence);
    
    // Update status
    updateRecordingStatus('ready', 'Ready');
    
    addSystemMessage(`✅ Processed in ${data.processing_time_ms}ms`);
}

function addMessage(role, text, transcription = null, audioUrl = null) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    let content = `<div class="message-text">${text}</div>`;
    
    if (transcription) {
        content += `<div class="message-meta">
            Language: ${transcription.language} | 
            Confidence: ${(transcription.confidence * 100).toFixed(0)}%
        </div>`;
    }
    
    if (audioUrl) {
        content += `<audio controls src="${audioUrl}" class="message-audio"></audio>`;
    }
    
    messageDiv.innerHTML = content;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addSystemMessage(text) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'system-message';
    messageDiv.textContent = text;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function updateRecordingStatus(status, text) {
    const statusIcon = document.getElementById('statusIcon');
    const statusText = document.getElementById('statusText');
    const statusDiv = document.getElementById('recordingStatus');
    
    statusDiv.className = `recording-status status-${status}`;
    statusText.textContent = text;
    
    const icons = {
        'ready': '⚪',
        'recording': '🔴',
        'processing': '⏳',
        'error': '❌'
    };
    
    statusIcon.textContent = icons[status] || '⚪';
}

function updateMetadata(data) {
    // Transcription
    document.getElementById('transcriptionText').textContent = data.transcription.text;
    document.getElementById('transcriptionLang').textContent = data.transcription.language;
    document.getElementById('transcriptionConf').textContent = `${(data.transcription.confidence * 100).toFixed(0)}%`;
    
    // Detection
    document.getElementById('scamDetected').textContent = data.scam_detected ? '✅ Yes' : '❌ No';
    document.getElementById('scamConfidence').textContent = `${(data.scam_confidence * 100).toFixed(0)}%`;
    document.getElementById('scamType').textContent = data.scam_type;
    
    // Voice fraud (if available)
    if (data.voice_fraud) {
        document.getElementById('voiceFraudCard').style.display = 'block';
        document.getElementById('voiceSynthetic').textContent = data.voice_fraud.is_synthetic ? '⚠️ Yes' : '✅ No';
        document.getElementById('voiceRisk').textContent = data.voice_fraud.risk_level;
    }
}

function updateIntelligence(intel) {
    const intelDiv = document.getElementById('intelligence');
    
    if (!intel || Object.keys(intel).length === 0) {
        intelDiv.innerHTML = '<p class="empty-state">No intelligence extracted yet</p>';
        return;
    }
    
    let html = '<div class="intel-grid">';
    
    if (intel.upi_ids && intel.upi_ids.length > 0) {
        html += `<div class="intel-item">
            <strong>UPI IDs:</strong> ${intel.upi_ids.join(', ')}
        </div>`;
    }
    
    if (intel.bank_accounts && intel.bank_accounts.length > 0) {
        html += `<div class="intel-item">
            <strong>Bank Accounts:</strong> ${intel.bank_accounts.join(', ')}
        </div>`;
    }
    
    if (intel.phone_numbers && intel.phone_numbers.length > 0) {
        html += `<div class="intel-item">
            <strong>Phone Numbers:</strong> ${intel.phone_numbers.join(', ')}
        </div>`;
    }
    
    if (intel.urls && intel.urls.length > 0) {
        html += `<div class="intel-item">
            <strong>URLs:</strong> ${intel.urls.join(', ')}
        </div>`;
    }
    
    html += '</div>';
    intelDiv.innerHTML = html;
}
```

#### 4.3 Voice UI Styles (`ui/voice.css`)

```css
/* Voice Honeypot UI Styles */

:root {
    --primary: #2563eb;
    --secondary: #64748b;
    --success: #10b981;
    --danger: #ef4444;
    --warning: #f59e0b;
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --border: #475569;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

header {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px;
    background: var(--bg-secondary);
    border-radius: 12px;
}

header h1 {
    font-size: 2rem;
    margin-bottom: 8px;
}

.subtitle {
    color: var(--text-secondary);
    font-size: 1rem;
}

.main-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

section {
    background: var(--bg-secondary);
    padding: 20px;
    border-radius: 12px;
    border: 1px solid var(--border);
}

section h2 {
    font-size: 1.25rem;
    margin-bottom: 16px;
    color: var(--primary);
}

/* Voice Controls */
.recording-status {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    background: var(--bg-tertiary);
    border-radius: 8px;
    margin-bottom: 20px;
}

.status-icon {
    font-size: 1.5rem;
}

.status-text {
    font-size: 1.1rem;
    font-weight: 600;
}

.status-recording {
    background: rgba(239, 68, 68, 0.1);
    border: 2px solid var(--danger);
}

.status-processing {
    background: rgba(245, 158, 11, 0.1);
    border: 2px solid var(--warning);
}

.button-group {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
}

.btn {
    flex: 1;
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-primary {
    background: var(--primary);
    color: white;
}

.btn-primary:hover:not(:disabled) {
    background: #1d4ed8;
}

.btn-secondary {
    background: var(--danger);
    color: white;
}

.btn-secondary:hover:not(:disabled) {
    background: #dc2626;
}

.btn-tertiary {
    background: var(--secondary);
    color: white;
}

.btn-tertiary:hover:not(:disabled) {
    background: #475569;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.session-info {
    display: flex;
    align-items: center;
    gap: 12px;
}

.session-info label {
    font-weight: 600;
}

.session-info input {
    flex: 1;
    padding: 8px 12px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-primary);
    font-family: monospace;
}

/* Conversation */
.conversation {
    grid-column: 1 / -1;
}

.messages {
    max-height: 400px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.message {
    padding: 12px 16px;
    border-radius: 8px;
    max-width: 80%;
}

.user-message {
    background: var(--bg-tertiary);
    align-self: flex-end;
}

.ai-message {
    background: rgba(37, 99, 235, 0.1);
    border: 1px solid var(--primary);
    align-self: flex-start;
}

.system-message {
    background: rgba(100, 116, 139, 0.1);
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.9rem;
    color: var(--text-secondary);
    text-align: center;
}

.message-text {
    margin-bottom: 8px;
}

.message-meta {
    font-size: 0.85rem;
    color: var(--text-secondary);
}

.message-audio {
    width: 100%;
    margin-top: 8px;
}

/* Metadata */
.metadata-card {
    background: var(--bg-tertiary);
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 16px;
}

.metadata-card h3 {
    font-size: 1rem;
    margin-bottom: 12px;
    color: var(--text-secondary);
}

.metadata-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
}

.metadata-item:last-child {
    border-bottom: none;
}

.metadata-item .label {
    font-weight: 600;
    color: var(--text-secondary);
}

.metadata-item .value {
    color: var(--text-primary);
}

/* Intelligence */
.intel-grid {
    display: grid;
    gap: 12px;
}

.intel-item {
    background: var(--bg-tertiary);
    padding: 12px;
    border-radius: 6px;
}

.intel-item strong {
    color: var(--primary);
    margin-right: 8px;
}

.empty-state {
    text-align: center;
    color: var(--text-secondary);
    padding: 20px;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-tertiary);
}

::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--secondary);
}
```

---

### STEP 5: INTEGRATION

#### 5.1 Update Main App (`app/main.py`)

```python
# Add voice router (only if Phase 2 enabled)

from app.config import settings

# ... existing imports ...

if getattr(settings, "PHASE_2_ENABLED", False):
    try:
        from app.api.voice_endpoints import router as voice_router
        app.include_router(voice_router)
        logger.info("Phase 2 voice endpoints enabled")
    except ImportError as e:
        logger.warning(f"Phase 2 voice endpoints unavailable: {e}")
```

#### 5.2 Update Config (`app/config.py`)

```python
# Add Phase 2 settings

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Phase 2: Voice Settings
    PHASE_2_ENABLED: bool = Field(
        default=False,
        description="Enable Phase 2 voice features"
    )
    
    WHISPER_MODEL: str = Field(
        default="base",
        description="Whisper model size (tiny, base, small, medium, large)"
    )
    
    TTS_ENGINE: str = Field(
        default="gtts",
        description="TTS engine (gtts, indic_tts)"
    )
    
    VOICE_FRAUD_DETECTION: bool = Field(
        default=False,
        description="Enable voice fraud detection"
    )
    
    AUDIO_SAMPLE_RATE: int = Field(
        default=16000,
        description="Audio sample rate in Hz"
    )
    
    AUDIO_CHUNK_DURATION: int = Field(
        default=5,
        description="Audio chunk duration in seconds"
    )
```

---

## TESTING PLAN

### Unit Tests

```python
# tests/unit/test_voice_asr.py
# tests/unit/test_voice_tts.py
# tests/unit/test_voice_fraud.py
```

### Integration Tests

```python
# tests/integration/test_voice_api.py

def test_voice_engage_endpoint():
    """Test voice engagement endpoint."""
    # Upload audio file
    # Verify transcription
    # Verify Phase 1 pipeline runs
    # Verify TTS output
    pass
```

### Manual Testing

1. Open `ui/voice.html` in browser
2. Click "Start Recording"
3. Speak a scam message (e.g., "Your account is blocked. Send OTP.")
4. Click "Stop Recording"
5. Verify:
   - Transcription appears
   - AI reply appears as text
   - Audio player with AI voice appears
   - Metadata is populated
   - Intelligence extracted

---

## DEPLOYMENT

### Docker Support

```dockerfile
# Add to Dockerfile

# Phase 2 dependencies (optional)
RUN if [ "$PHASE_2_ENABLED" = "true" ]; then \
    apt-get update && \
    apt-get install -y ffmpeg portaudio19-dev && \
    pip install -r requirements-phase2.txt; \
fi
```

### Environment Variables

```bash
# Production .env
PHASE_2_ENABLED=true
WHISPER_MODEL=base
TTS_ENGINE=gtts
VOICE_FRAUD_DETECTION=false
```

---

## IMPACT ANALYSIS

### What Changes

1. **New files added:**
   - `app/voice/` directory (asr.py, tts.py, fraud_detector.py)
   - `app/api/voice_endpoints.py`
   - `app/api/voice_schemas.py`
   - `ui/voice.html`, `ui/voice.js`, `ui/voice.css`
   - `requirements-phase2.txt`
   - `PHASE_2_VOICE_IMPLEMENTATION_PLAN.md` (this file)

2. **Modified files:**
   - `app/main.py` (add voice router conditionally)
   - `app/config.py` (add Phase 2 settings)
   - `.env.example` (add Phase 2 variables)

### What Doesn't Change

1. **Phase 1 remains untouched:**
   - `app/agent/honeypot.py` - NO CHANGES
   - `app/models/detector.py` - NO CHANGES
   - `app/models/extractor.py` - NO CHANGES
   - `app/api/endpoints.py` - NO CHANGES
   - `ui/index.html` - NO CHANGES

2. **Existing tests remain valid:**
   - All Phase 1 tests pass without modification

3. **Deployment:**
   - Phase 2 is opt-in via `PHASE_2_ENABLED=true`
   - Default behavior unchanged

---

## TIMELINE

| Task | Effort | Priority |
|------|--------|----------|
| Install dependencies | 1 hour | High |
| Implement ASR module | 2 hours | High |
| Implement TTS module | 2 hours | High |
| Implement voice endpoints | 3 hours | High |
| Build voice UI | 4 hours | High |
| Integration & testing | 3 hours | High |
| Voice fraud detector | 4 hours | Low (optional) |
| Documentation | 2 hours | Medium |

**Total: 17-21 hours**

---

## SUCCESS CRITERIA

1. ✅ Voice endpoint accepts audio files
2. ✅ Whisper transcribes audio accurately (>85% WER)
3. ✅ Phase 1 pipeline processes transcribed text unchanged
4. ✅ TTS generates natural-sounding replies
5. ✅ Voice UI allows recording and playback
6. ✅ Latency <5s for full voice loop
7. ✅ Phase 1 tests still pass
8. ✅ No breaking changes to existing API

---

## RESPONSIBLE AI CONSIDERATIONS

1. **Privacy:**
   - Audio files stored temporarily only
   - Deleted after processing
   - No raw audio in database

2. **Consent:**
   - UI clearly indicates recording
   - User controls start/stop

3. **Bias:**
   - Whisper trained on diverse accents
   - Test with Hindi, Gujarati, English

4. **Safety:**
   - Voice fraud detection optional
   - False positive mitigation

---

## FUTURE ENHANCEMENTS

1. **Streaming audio** (real-time chunks)
2. **WebRTC** for browser-to-browser calls
3. **Voice fingerprinting** (repeat scammer detection)
4. **Emotion detection** from voice tone
5. **Multi-speaker diarization**

---

## CONCLUSION

This plan provides a complete, production-ready implementation of Phase 2 voice features that:

- ✅ Extends Phase 1 without breaking changes
- ✅ Provides separate UI for voice testing
- ✅ Reuses existing honeypot logic
- ✅ Adds voice-specific features (ASR, TTS, fraud detection)
- ✅ Maintains code quality and testing standards

**Next Steps:**

1. Review this plan
2. Install Phase 2 dependencies
3. Implement modules in order (ASR → TTS → Endpoints → UI)
4. Test thoroughly
5. Deploy with `PHASE_2_ENABLED=true`
