# Phase 2 Voice Implementation - AI Assistant Prompts

## Overview

This file contains 6 carefully crafted prompts to guide AI assistants (like Claude, ChatGPT, etc.) through implementing Phase 2 voice features step-by-step.

**How to Use:**
1. Copy each prompt one at a time
2. Paste into your AI assistant
3. Review the generated code
4. Test before moving to the next prompt
5. Track progress in `PHASE_2_CHECKLIST.md`

**Context Files to Attach:**
- `PHASE_2_VOICE_IMPLEMENTATION_PLAN.md` (master plan)
- `PHASE_2_ARCHITECTURE.md` (architecture)
- `app/agent/honeypot.py` (existing honeypot)
- `app/config.py` (existing config)

---

## 📋 PROMPT 1: ASR Module (Whisper Transcription)

**Estimated Time:** 2 hours  
**Dependencies:** `pip install openai-whisper torchaudio`  
**Output:** `app/voice/asr.py`

### Prompt

```
I'm implementing Phase 2 voice features for my ScamShield AI honeypot project. I need to create an ASR (Automatic Speech Recognition) module using Whisper.

CONTEXT:
- This is Phase 2, which wraps around an existing Phase 1 text honeypot
- Phase 1 must remain unchanged
- The ASR module will transcribe audio to text, which then feeds into Phase 1

REQUIREMENTS:

1. Create file: app/voice/asr.py

2. Implement ASREngine class with:
   - __init__(model_size: str = "base") - Initialize Whisper model
   - _load_model() - Load Whisper model (tiny/base/small/medium/large)
   - transcribe(audio_path: str, language: Optional[str] = None) -> Dict
     Returns: {"text": str, "language": str, "confidence": float}
   - _calculate_confidence(result: Dict) -> float - Calculate confidence from Whisper output

3. Features:
   - Support multiple Whisper model sizes (configurable)
   - Auto-detect language or accept language hint
   - GPU support if available (cuda), else CPU
   - Return transcription with confidence score
   - Handle errors gracefully (return empty text with 0.0 confidence)

4. Singleton pattern:
   - get_asr_engine() -> ASREngine (global instance)

5. Code quality:
   - Type hints for all functions
   - Docstrings (Google style)
   - Logging using app.utils.logger.get_logger(__name__)
   - Error handling with try/except

6. Configuration from settings:
   - settings.WHISPER_MODEL (default: "base")
   - Auto-detect device (cuda/cpu)

REFERENCE IMPLEMENTATION (from PHASE_2_VOICE_IMPLEMENTATION_PLAN.md):
[See Step 2.1 in the plan]

ACCEPTANCE CRITERIA:
- [ ] ASREngine class created
- [ ] Whisper model loads successfully
- [ ] transcribe() returns correct format
- [ ] Language detection works
- [ ] Confidence calculation implemented
- [ ] Singleton pattern works
- [ ] Error handling present
- [ ] Type hints and docstrings complete
- [ ] Logging added

Please generate the complete app/voice/asr.py file with production-ready code.
```

---

## 📋 PROMPT 2: TTS Module (Text-to-Speech)

**Estimated Time:** 2 hours  
**Dependencies:** `pip install gTTS`  
**Output:** `app/voice/tts.py`

### Prompt

```
I'm implementing Phase 2 voice features for my ScamShield AI honeypot. I need to create a TTS (Text-to-Speech) module using gTTS.

CONTEXT:
- This is Phase 2, which wraps around an existing Phase 1 text honeypot
- Phase 1 generates text replies, TTS converts them to speech
- The TTS module will convert AI text replies to audio files

REQUIREMENTS:

1. Create file: app/voice/tts.py

2. Implement TTSEngine class with:
   - __init__() - Initialize TTS engine
   - synthesize(text: str, language: str = "en", output_path: Optional[str] = None) -> str
     Returns: Path to generated audio file
   - Language mapping for Indic languages (en, hi, gu, ta, te, bn, mr)

3. Features:
   - Support multiple languages (English, Hindi, Gujarati, Tamil, Telugu, Bengali, Marathi)
   - Auto-generate output path if not provided (use tempfile)
   - Return path to generated .mp3 file
   - Handle errors gracefully (raise exception with clear message)

4. Singleton pattern:
   - get_tts_engine() -> TTSEngine (global instance)

5. Code quality:
   - Type hints for all functions
   - Docstrings (Google style)
   - Logging using app.utils.logger.get_logger(__name__)
   - Error handling with try/except

6. Configuration from settings:
   - settings.TTS_ENGINE (default: "gtts")

REFERENCE IMPLEMENTATION (from PHASE_2_VOICE_IMPLEMENTATION_PLAN.md):
[See Step 2.2 in the plan]

LANGUAGE MAPPING:
- "english" -> "en"
- "hindi" -> "hi"
- "gujarati" -> "gu"
- "tamil" -> "ta"
- "telugu" -> "te"
- "bengali" -> "bn"
- "marathi" -> "mr"

ACCEPTANCE CRITERIA:
- [ ] TTSEngine class created
- [ ] synthesize() generates audio files
- [ ] Language mapping works for Indic languages
- [ ] Temp file generation works
- [ ] Singleton pattern works
- [ ] Error handling present
- [ ] Type hints and docstrings complete
- [ ] Logging added

Please generate the complete app/voice/tts.py file with production-ready code.
```

---

## 📋 PROMPT 3: Voice API Endpoints

**Estimated Time:** 3 hours  
**Dependencies:** FastAPI (already installed)  
**Output:** `app/api/voice_endpoints.py`, `app/api/voice_schemas.py`

### Prompt

```
I'm implementing Phase 2 voice features for my ScamShield AI honeypot. I need to create voice API endpoints that integrate with the existing Phase 1 text honeypot.

CONTEXT:
- Phase 1 has /api/v1/honeypot/engage (text endpoint) - DO NOT MODIFY
- Phase 2 needs /api/v1/voice/engage (voice endpoint) - NEW
- Voice endpoint: Audio in → ASR → Phase 1 pipeline → TTS → Audio out
- Must reuse existing Phase 1 logic (detector, honeypot, extractor)

REQUIREMENTS:

1. Create file: app/api/voice_schemas.py

Implement Pydantic schemas:
- TranscriptionMetadata (text, language, confidence)
- VoiceFraudMetadata (is_synthetic, confidence, risk_level) - Optional
- VoiceEngageResponse (session_id, scam_detected, scam_confidence, scam_type, turn_count, ai_reply_text, ai_reply_audio_url, transcription, voice_fraud, extracted_intelligence, processing_time_ms)

2. Create file: app/api/voice_endpoints.py

Implement endpoints:

A. POST /api/v1/voice/engage
   - Accept: multipart/form-data (audio_file, session_id, language)
   - Flow:
     1. Save uploaded audio temporarily
     2. Transcribe with ASR (app.voice.asr.get_asr_engine())
     3. Process through Phase 1 (REUSE existing code):
        - app.models.detector.get_detector().detect()
        - app.agent.honeypot.HoneypotAgent().engage()
        - app.models.extractor.extract_intelligence()
     4. Convert reply to speech with TTS (app.voice.tts.get_tts_engine())
     5. Return VoiceEngageResponse with audio URL
   - Auth: x-api-key header (use existing verify_api_key)
   - Error handling: HTTPException with clear messages

B. GET /api/v1/voice/audio/{filename}
   - Serve generated audio files from temp directory
   - Return FileResponse with audio/mpeg media type
   - 404 if file not found

C. GET /api/v1/voice/health
   - Check ASR and TTS engine status
   - Return health info (model, device, engine type)

3. Router setup:
   - APIRouter with prefix="/api/v1/voice", tags=["voice"]
   - Export router for inclusion in main app

4. Code quality:
   - Type hints for all functions
   - Docstrings (Google style)
   - Logging using app.utils.logger.get_logger(__name__)
   - Error handling with try/except
   - Clean up temp files after processing

CRITICAL: DO NOT MODIFY PHASE 1 CODE
- Import and reuse: app.models.detector, app.agent.honeypot, app.models.extractor
- Import and reuse: app.database.redis_client (session state)
- Import and reuse: app.api.auth.verify_api_key

REFERENCE IMPLEMENTATION (from PHASE_2_VOICE_IMPLEMENTATION_PLAN.md):
[See Step 3.1 and 3.2 in the plan]

ACCEPTANCE CRITERIA:
- [ ] voice_schemas.py created with all schemas
- [ ] voice_endpoints.py created with all endpoints
- [ ] POST /voice/engage works end-to-end
- [ ] Audio upload handling works
- [ ] ASR integration works
- [ ] Phase 1 integration works (no modifications to Phase 1)
- [ ] TTS integration works
- [ ] GET /voice/audio/{filename} serves files
- [ ] GET /voice/health returns status
- [ ] Error handling present
- [ ] Type hints and docstrings complete
- [ ] Logging added
- [ ] Auth (x-api-key) works

Please generate both files (voice_schemas.py and voice_endpoints.py) with production-ready code.
```

---

## 📋 PROMPT 4: Voice UI (HTML + JavaScript + CSS)

**Estimated Time:** 4 hours  
**Dependencies:** None (vanilla JS)  
**Output:** `ui/voice.html`, `ui/voice.js`, `ui/voice.css`

### Prompt

```
I'm implementing Phase 2 voice features for my ScamShield AI honeypot. I need to create a voice UI that allows users to record audio, send it to the API, and hear AI voice replies.

CONTEXT:
- Phase 1 has ui/index.html (text chat) - DO NOT MODIFY
- Phase 2 needs ui/voice.html (voice chat) - NEW, SEPARATE
- Voice UI: Record → Send to /api/v1/voice/engage → Display transcription + Play AI audio

REQUIREMENTS:

1. Create file: ui/voice.html

Features:
- Header: "🎤 ScamShield AI - Voice Honeypot (Phase 2)"
- Recording controls:
  - Status indicator (Ready/Recording/Processing)
  - "Start Recording" button
  - "Stop Recording" button
  - "Upload Audio File" button
  - Session ID display (read-only)
- Conversation area:
  - Display user messages (transcription)
  - Display AI messages (text + audio player)
  - System messages (status updates)
- Metadata section:
  - Transcription (text, language, confidence)
  - Detection (scam_detected, confidence, type)
  - Voice fraud (optional, if enabled)
- Intelligence section:
  - Display extracted UPI, bank accounts, phone numbers, URLs

2. Create file: ui/voice.js

Features:
- startRecording(): Use MediaRecorder API to capture audio
- stopRecording(): Stop recording and send to API
- uploadAudio(): Allow file upload
- sendAudioToAPI(): POST to /api/v1/voice/engage with FormData
- handleAPIResponse(): Update UI with response
- addMessage(): Add user/ai/system messages
- updateMetadata(): Update transcription, detection, fraud info
- updateIntelligence(): Display extracted intelligence
- Audio playback: <audio controls> for AI replies

3. Create file: ui/voice.css

Features:
- Dark theme (consistent with Phase 1)
- Recording status indicator (colors: ready=white, recording=red, processing=yellow)
- Button styles (primary, secondary, tertiary)
- Message bubbles (user=right, ai=left, system=center)
- Metadata cards with labels and values
- Responsive design

4. Code quality:
- Vanilla JavaScript (no frameworks)
- Clean, readable code
- Error handling (microphone access, API errors)
- Console logging for debugging

API INTEGRATION:
- Endpoint: POST /api/v1/voice/engage
- Headers: x-api-key: "dev-key-12345"
- FormData: audio_file (blob), session_id (string), language (string)
- Response: VoiceEngageResponse (see voice_schemas.py)

REFERENCE IMPLEMENTATION (from PHASE_2_VOICE_IMPLEMENTATION_PLAN.md):
[See Step 4.1, 4.2, 4.3 in the plan]

ACCEPTANCE CRITERIA:
- [ ] voice.html created with all sections
- [ ] voice.js created with all functions
- [ ] voice.css created with all styles
- [ ] Recording works (MediaRecorder API)
- [ ] File upload works
- [ ] API integration works
- [ ] Transcription displays correctly
- [ ] AI audio plays correctly
- [ ] Metadata updates correctly
- [ ] Intelligence displays correctly
- [ ] Error handling present
- [ ] UI looks professional (dark theme)
- [ ] Responsive design works

Please generate all three files (voice.html, voice.js, voice.css) with production-ready code.
```

---

## 📋 PROMPT 5: Integration & Configuration

**Estimated Time:** 3 hours  
**Dependencies:** None  
**Output:** Updated `app/main.py`, `app/config.py`, `.env.example`

### Prompt

```
I'm implementing Phase 2 voice features for my ScamShield AI honeypot. I need to integrate the voice module into the main app without breaking Phase 1.

CONTEXT:
- Phase 1 is working perfectly - MUST NOT BREAK
- Phase 2 voice module is ready (ASR, TTS, endpoints, UI)
- Need to conditionally load Phase 2 only if PHASE_2_ENABLED=true
- If Phase 2 fails to load, Phase 1 should still work

REQUIREMENTS:

1. Update file: app/config.py

Add Phase 2 settings to Settings class:
- PHASE_2_ENABLED: bool = Field(default=False, description="Enable Phase 2 voice features")
- WHISPER_MODEL: str = Field(default="base", description="Whisper model size (tiny, base, small, medium, large)")
- TTS_ENGINE: str = Field(default="gtts", description="TTS engine (gtts, indic_tts)")
- VOICE_FRAUD_DETECTION: bool = Field(default=False, description="Enable voice fraud detection")
- AUDIO_SAMPLE_RATE: int = Field(default=16000, description="Audio sample rate in Hz")
- AUDIO_CHUNK_DURATION: int = Field(default=5, description="Audio chunk duration in seconds")

2. Update file: app/main.py

Add conditional Phase 2 router inclusion:
```python
# After existing router inclusions
if getattr(settings, "PHASE_2_ENABLED", False):
    try:
        from app.api.voice_endpoints import router as voice_router
        app.include_router(voice_router)
        logger.info("Phase 2 voice endpoints enabled")
    except ImportError as e:
        logger.warning(f"Phase 2 voice endpoints unavailable: {e}")
    except Exception as e:
        logger.error(f"Failed to load Phase 2: {e}")
```

3. Update file: .env.example

Add Phase 2 configuration section:
```bash
# ========================================
# PHASE 2: VOICE FEATURES (OPTIONAL)
# ========================================
# Enable Phase 2 voice features (default: false)
PHASE_2_ENABLED=false

# Whisper ASR Configuration
WHISPER_MODEL=base
# Options: tiny, base, small, medium, large
# Larger models = better accuracy but slower

# TTS Configuration
TTS_ENGINE=gtts
# Options: gtts (Google TTS - free)

# Voice Fraud Detection (Optional)
VOICE_FRAUD_DETECTION=false
# Set to true to enable synthetic voice detection

# Audio Settings
AUDIO_SAMPLE_RATE=16000
AUDIO_CHUNK_DURATION=5
```

4. Code quality:
- Minimal changes to existing code
- Graceful degradation (Phase 1 works if Phase 2 fails)
- Clear logging messages
- No breaking changes

CRITICAL REQUIREMENTS:
- DO NOT modify any Phase 1 code beyond adding the router
- Phase 2 must be opt-in (default: disabled)
- If Phase 2 fails to load, log warning but continue
- Phase 1 must work even if Phase 2 dependencies are missing

REFERENCE IMPLEMENTATION (from PHASE_2_VOICE_IMPLEMENTATION_PLAN.md):
[See Step 5.1 and 5.2 in the plan]

ACCEPTANCE CRITERIA:
- [ ] app/config.py updated with Phase 2 settings
- [ ] app/main.py updated with conditional router inclusion
- [ ] .env.example updated with Phase 2 config
- [ ] Phase 1 still works with PHASE_2_ENABLED=false
- [ ] Phase 2 loads with PHASE_2_ENABLED=true
- [ ] Graceful degradation if Phase 2 fails
- [ ] Logging messages clear
- [ ] No breaking changes to Phase 1

Please provide the exact changes needed for each file (show before/after or provide complete updated sections).
```

---

## 📋 PROMPT 6: Testing & Validation

**Estimated Time:** 3 hours  
**Dependencies:** pytest (already installed)  
**Output:** `tests/unit/test_voice_asr.py`, `tests/unit/test_voice_tts.py`, `tests/integration/test_voice_api.py`

### Prompt

```
I'm implementing Phase 2 voice features for my ScamShield AI honeypot. I need to create comprehensive tests to ensure everything works correctly.

CONTEXT:
- Phase 2 is implemented (ASR, TTS, endpoints, UI, integration)
- Need unit tests for ASR and TTS modules
- Need integration tests for voice API endpoints
- Need to verify Phase 1 is not affected

REQUIREMENTS:

1. Create file: tests/unit/test_voice_asr.py

Test ASREngine:
- test_asr_engine_initialization() - Verify model loads
- test_asr_transcribe_english() - Test English transcription
- test_asr_transcribe_hindi() - Test Hindi transcription (if sample available)
- test_asr_confidence_calculation() - Test confidence scoring
- test_asr_error_handling() - Test with invalid audio
- test_asr_singleton() - Verify singleton pattern

2. Create file: tests/unit/test_voice_tts.py

Test TTSEngine:
- test_tts_engine_initialization() - Verify engine initializes
- test_tts_synthesize_english() - Test English synthesis
- test_tts_synthesize_hindi() - Test Hindi synthesis
- test_tts_language_mapping() - Test language code mapping
- test_tts_temp_file_generation() - Test auto file path
- test_tts_error_handling() - Test with invalid input
- test_tts_singleton() - Verify singleton pattern

3. Create file: tests/integration/test_voice_api.py

Test Voice API:
- test_voice_engage_endpoint() - Test full voice flow
  - Upload sample audio
  - Verify transcription in response
  - Verify AI reply text in response
  - Verify audio URL in response
  - Verify metadata (scam_detected, confidence, etc.)
- test_voice_audio_download() - Test audio file serving
- test_voice_health_endpoint() - Test health check
- test_voice_auth_required() - Test x-api-key authentication
- test_voice_invalid_audio() - Test error handling
- test_phase_1_unaffected() - Verify Phase 1 endpoints still work

4. Test fixtures:
- Create sample audio files (tests/fixtures/audio/):
  - sample_scam_en.wav (English scam message)
  - sample_scam_hi.wav (Hindi scam message, if available)
  - invalid_audio.txt (non-audio file for error testing)

5. Code quality:
- Use pytest fixtures
- Mock external dependencies where appropriate
- Clear test names and docstrings
- Assertions with descriptive messages
- Test both success and failure cases

CRITICAL: Test Phase 1 Isolation
- Run all existing Phase 1 tests
- Verify they still pass
- Verify Phase 1 endpoints work with PHASE_2_ENABLED=false

REFERENCE IMPLEMENTATION (from PHASE_2_VOICE_IMPLEMENTATION_PLAN.md):
[See Testing Plan section]

ACCEPTANCE CRITERIA:
- [ ] test_voice_asr.py created with all tests
- [ ] test_voice_tts.py created with all tests
- [ ] test_voice_api.py created with all tests
- [ ] All ASR tests pass
- [ ] All TTS tests pass
- [ ] All voice API tests pass
- [ ] Phase 1 tests still pass
- [ ] Test fixtures created
- [ ] Code coverage >80%
- [ ] Clear test documentation

Please generate all three test files with production-ready test code. Include instructions for creating sample audio fixtures.
```

---

## 🎯 Implementation Workflow

### Step-by-Step Process

```
┌─────────────────────────────────────────────────────────────┐
│  PROMPT 1: ASR Module                                       │
│  ├─ Generate app/voice/asr.py                               │
│  ├─ Test: python -c "from app.voice.asr import get_asr_engine; print('OK')"
│  └─ ✓ Checkpoint: ASR module works                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PROMPT 2: TTS Module                                       │
│  ├─ Generate app/voice/tts.py                               │
│  ├─ Test: python -c "from app.voice.tts import get_tts_engine; print('OK')"
│  └─ ✓ Checkpoint: TTS module works                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PROMPT 3: Voice API                                        │
│  ├─ Generate app/api/voice_schemas.py                       │
│  ├─ Generate app/api/voice_endpoints.py                     │
│  ├─ Test: Check imports work                                │
│  └─ ✓ Checkpoint: API code ready (not integrated yet)       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PROMPT 4: Voice UI                                         │
│  ├─ Generate ui/voice.html                                  │
│  ├─ Generate ui/voice.js                                    │
│  ├─ Generate ui/voice.css                                   │
│  ├─ Test: Open voice.html in browser                        │
│  └─ ✓ Checkpoint: UI renders (API not connected yet)        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PROMPT 5: Integration                                      │
│  ├─ Update app/config.py                                    │
│  ├─ Update app/main.py                                      │
│  ├─ Update .env.example                                     │
│  ├─ Set PHASE_2_ENABLED=true in .env                        │
│  ├─ Test: Start server, check logs                          │
│  └─ ✓ Checkpoint: Phase 2 integrated, server starts         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PROMPT 6: Testing                                          │
│  ├─ Generate tests/unit/test_voice_asr.py                   │
│  ├─ Generate tests/unit/test_voice_tts.py                   │
│  ├─ Generate tests/integration/test_voice_api.py            │
│  ├─ Run: pytest tests/unit/test_voice_*.py                  │
│  ├─ Run: pytest tests/integration/test_voice_api.py         │
│  ├─ Run: pytest tests/ (all tests, including Phase 1)       │
│  └─ ✓ Checkpoint: All tests pass                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ✅ PHASE 2 COMPLETE!
```

---

## 📊 Progress Tracking

### Checklist

Use this to track your progress:

- [ ] **PROMPT 1 COMPLETE** - ASR Module
  - [ ] app/voice/asr.py created
  - [ ] ASR module imports successfully
  - [ ] Basic transcription test works

- [ ] **PROMPT 2 COMPLETE** - TTS Module
  - [ ] app/voice/tts.py created
  - [ ] TTS module imports successfully
  - [ ] Basic synthesis test works

- [ ] **PROMPT 3 COMPLETE** - Voice API
  - [ ] app/api/voice_schemas.py created
  - [ ] app/api/voice_endpoints.py created
  - [ ] Imports work (no integration yet)

- [ ] **PROMPT 4 COMPLETE** - Voice UI
  - [ ] ui/voice.html created
  - [ ] ui/voice.js created
  - [ ] ui/voice.css created
  - [ ] UI renders in browser

- [ ] **PROMPT 5 COMPLETE** - Integration
  - [ ] app/config.py updated
  - [ ] app/main.py updated
  - [ ] .env.example updated
  - [ ] Server starts with Phase 2 enabled
  - [ ] Voice endpoints accessible

- [ ] **PROMPT 6 COMPLETE** - Testing
  - [ ] Unit tests created
  - [ ] Integration tests created
  - [ ] All tests pass
  - [ ] Phase 1 tests still pass

---

## 🚨 Important Notes

### Before Starting

1. **Backup your code:**
   ```bash
   git add .
   git commit -m "Backup before Phase 2 implementation"
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements-phase2.txt
   ```

3. **Read the plan:**
   - Review `PHASE_2_VOICE_IMPLEMENTATION_PLAN.md`
   - Understand the architecture in `PHASE_2_ARCHITECTURE.md`

### During Implementation

1. **Test after each prompt:**
   - Don't move to the next prompt until the current one works
   - Run basic tests to verify functionality
   - Check logs for errors

2. **Track progress:**
   - Update `PHASE_2_CHECKLIST.md` as you complete tasks
   - Mark prompts complete in this file

3. **Ask for help:**
   - If a prompt doesn't work, ask the AI to debug
   - Provide error messages and logs
   - Reference the implementation plan

### After Completion

1. **Full testing:**
   ```bash
   # Test Phase 2
   pytest tests/unit/test_voice_*.py
   pytest tests/integration/test_voice_api.py
   
   # Test Phase 1 (verify no breaking changes)
   pytest tests/
   ```

2. **Manual testing:**
   - Open `http://localhost:8000/ui/voice.html`
   - Record a voice message
   - Verify AI responds with voice

3. **Documentation:**
   - Update main README.md with Phase 2 info
   - Document any issues or deviations from plan

---

## 🎓 Tips for Success

### Working with AI Assistants

1. **Provide context:**
   - Attach relevant files (config, existing code)
   - Mention you're following a specific plan
   - Reference the implementation plan sections

2. **Be specific:**
   - If code doesn't work, provide exact error messages
   - Ask for specific fixes, not rewrites
   - Request explanations for unclear parts

3. **Iterate:**
   - Review generated code before using it
   - Test incrementally
   - Ask for improvements if needed

### Common Issues

| Issue | Solution | Prompt to Use |
|-------|----------|---------------|
| Import errors | Check dependencies installed | "I'm getting ImportError: [error]. How do I fix this?" |
| Whisper slow | Use smaller model | "Change WHISPER_MODEL to 'tiny' in the code" |
| Audio not playing | Check file path | "Debug audio file serving in voice_endpoints.py" |
| Phase 1 broken | Revert changes | "Show me how to make Phase 2 truly optional" |

---

## 📞 Support

### If You Get Stuck

1. **Check the plan:**
   - `PHASE_2_VOICE_IMPLEMENTATION_PLAN.md` has detailed explanations
   - `PHASE_2_ARCHITECTURE.md` shows how components fit together

2. **Check logs:**
   ```bash
   tail -f logs/app.log
   ```

3. **Ask the AI:**
   - "I'm stuck on [step]. Here's my error: [error]. How do I fix it?"
   - Provide context from the implementation plan

### Getting Help from AI

**Good prompt:**
```
I'm implementing PROMPT 3 (Voice API) from PHASE_2_IMPLEMENTATION_PROMPTS.md.

I'm getting this error:
[paste error]

Here's my current code:
[paste relevant code]

How do I fix this? Reference the implementation plan if needed.
```

**Bad prompt:**
```
It doesn't work. Fix it.
```

---

## ✅ Success Criteria

Phase 2 is complete when:

- [x] All 6 prompts executed successfully
- [ ] All generated code works
- [ ] Server starts with PHASE_2_ENABLED=true
- [ ] Voice UI accessible at /ui/voice.html
- [ ] Can record voice and get AI voice reply
- [ ] All tests pass (Phase 1 + Phase 2)
- [ ] No breaking changes to Phase 1
- [ ] Documentation updated

---

## 🎉 You're Ready!

**Next Steps:**

1. **Start with PROMPT 1** (ASR Module)
2. **Copy the prompt** to your AI assistant
3. **Review the generated code**
4. **Test it works**
5. **Move to PROMPT 2**

**Estimated Total Time:** 17-21 hours

**You've got this!** 🚀

---

*Created: 2026-02-10*

*For: ScamShield AI - Phase 2 Voice Implementation*

*Start with: PROMPT 1 (ASR Module)*
