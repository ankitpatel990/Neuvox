# Phase 2 Implementation - Quick Reference Card

## 🎯 6 Prompts to Implement Phase 2

Copy these prompts one at a time to your AI assistant (Claude, ChatGPT, etc.)

---

## ✅ PROMPT 1: ASR Module (2 hours)

**What:** Create Whisper-based speech-to-text module  
**Output:** `app/voice/asr.py`  
**Dependencies:** `pip install openai-whisper torchaudio`

**Copy this:**
```
I'm implementing Phase 2 voice features for my ScamShield AI honeypot. Create app/voice/asr.py with ASREngine class using Whisper. Requirements: transcribe(audio_path, language) -> {text, language, confidence}, support multiple model sizes (tiny/base/small/medium/large), GPU if available, singleton pattern, type hints, docstrings, logging, error handling. Reference: PHASE_2_VOICE_IMPLEMENTATION_PLAN.md Step 2.1.
```

**Test:**
```bash
python -c "from app.voice.asr import get_asr_engine; print('✓ ASR OK')"
```

---

## ✅ PROMPT 2: TTS Module (2 hours)

**What:** Create gTTS-based text-to-speech module  
**Output:** `app/voice/tts.py`  
**Dependencies:** `pip install gTTS`

**Copy this:**
```
I'm implementing Phase 2 voice features for my ScamShield AI honeypot. Create app/voice/tts.py with TTSEngine class using gTTS. Requirements: synthesize(text, language, output_path) -> audio_file_path, support Indic languages (en, hi, gu, ta, te, bn, mr), auto-generate temp files, singleton pattern, type hints, docstrings, logging, error handling. Reference: PHASE_2_VOICE_IMPLEMENTATION_PLAN.md Step 2.2.
```

**Test:**
```bash
python -c "from app.voice.tts import get_tts_engine; print('✓ TTS OK')"
```

---

## ✅ PROMPT 3: Voice API (3 hours)

**What:** Create voice API endpoints  
**Output:** `app/api/voice_endpoints.py`, `app/api/voice_schemas.py`  
**Dependencies:** FastAPI (already installed)

**Copy this:**
```
I'm implementing Phase 2 voice features for my ScamShield AI honeypot. Create app/api/voice_schemas.py (VoiceEngageResponse, TranscriptionMetadata, VoiceFraudMetadata) and app/api/voice_endpoints.py with: POST /api/v1/voice/engage (audio_file upload → ASR → Phase 1 pipeline → TTS → audio response), GET /api/v1/voice/audio/{filename} (serve audio), GET /api/v1/voice/health. CRITICAL: Reuse Phase 1 code (detector, honeypot, extractor), do NOT modify Phase 1. Reference: PHASE_2_VOICE_IMPLEMENTATION_PLAN.md Step 3.
```

**Test:**
```bash
python -c "from app.api.voice_endpoints import router; print('✓ API OK')"
```

---

## ✅ PROMPT 4: Voice UI (4 hours)

**What:** Create voice chat interface  
**Output:** `ui/voice.html`, `ui/voice.js`, `ui/voice.css`  
**Dependencies:** None (vanilla JS)

**Copy this:**
```
I'm implementing Phase 2 voice features for my ScamShield AI honeypot. Create ui/voice.html (recording controls, conversation display, metadata, intelligence), ui/voice.js (MediaRecorder API, sendAudioToAPI, handleAPIResponse, updateMetadata), ui/voice.css (dark theme, recording status colors, message bubbles). Features: record audio, upload files, display transcription, play AI voice, show metadata. API: POST /api/v1/voice/engage with FormData. Reference: PHASE_2_VOICE_IMPLEMENTATION_PLAN.md Step 4.
```

**Test:**
```
Open http://localhost:8000/ui/voice.html in browser
(Server not running yet, just check UI renders)
```

---

## ✅ PROMPT 5: Integration (3 hours)

**What:** Integrate Phase 2 into main app  
**Output:** Updated `app/config.py`, `app/main.py`, `.env.example`  
**Dependencies:** None

**Copy this:**
```
I'm implementing Phase 2 voice features for my ScamShield AI honeypot. Update app/config.py (add PHASE_2_ENABLED, WHISPER_MODEL, TTS_ENGINE, VOICE_FRAUD_DETECTION, AUDIO_SAMPLE_RATE, AUDIO_CHUNK_DURATION), app/main.py (conditionally include voice router if PHASE_2_ENABLED=true with try/except), .env.example (add Phase 2 config section). CRITICAL: Phase 1 must work if Phase 2 disabled or fails to load. Reference: PHASE_2_VOICE_IMPLEMENTATION_PLAN.md Step 5.
```

**Test:**
```bash
# Set in .env
PHASE_2_ENABLED=true

# Start server
python -m uvicorn app.main:app --reload

# Check logs for "Phase 2 voice endpoints enabled"
```

---

## ✅ PROMPT 6: Testing (3 hours)

**What:** Create comprehensive tests  
**Output:** `tests/unit/test_voice_asr.py`, `tests/unit/test_voice_tts.py`, `tests/integration/test_voice_api.py`  
**Dependencies:** pytest (already installed)

**Copy this:**
```
I'm implementing Phase 2 voice features for my ScamShield AI honeypot. Create tests/unit/test_voice_asr.py (test ASREngine: initialization, transcription, confidence, error handling, singleton), tests/unit/test_voice_tts.py (test TTSEngine: initialization, synthesis, language mapping, temp files, error handling, singleton), tests/integration/test_voice_api.py (test voice endpoints: full flow, audio download, health check, auth, error handling, Phase 1 unaffected). Reference: PHASE_2_VOICE_IMPLEMENTATION_PLAN.md Testing Plan.
```

**Test:**
```bash
# Run Phase 2 tests
pytest tests/unit/test_voice_*.py -v
pytest tests/integration/test_voice_api.py -v

# Run ALL tests (verify Phase 1 still works)
pytest tests/ -v
```

---

## 📋 Implementation Checklist

```
[ ] PROMPT 1: ASR Module
    [ ] Code generated
    [ ] Import test passes
    [ ] Basic transcription works

[ ] PROMPT 2: TTS Module
    [ ] Code generated
    [ ] Import test passes
    [ ] Basic synthesis works

[ ] PROMPT 3: Voice API
    [ ] Schemas generated
    [ ] Endpoints generated
    [ ] Import test passes

[ ] PROMPT 4: Voice UI
    [ ] HTML generated
    [ ] JavaScript generated
    [ ] CSS generated
    [ ] UI renders in browser

[ ] PROMPT 5: Integration
    [ ] Config updated
    [ ] Main app updated
    [ ] .env.example updated
    [ ] Server starts successfully
    [ ] Voice endpoints accessible

[ ] PROMPT 6: Testing
    [ ] Unit tests generated
    [ ] Integration tests generated
    [ ] All tests pass
    [ ] Phase 1 tests still pass

[ ] FINAL VALIDATION
    [ ] Can record voice in UI
    [ ] Can upload audio file
    [ ] AI responds with voice
    [ ] Metadata displays correctly
    [ ] Intelligence extracted
    [ ] Phase 1 text chat still works
```

---

## 🚀 Quick Start

### Before You Begin

```bash
# 1. Backup your code
git add .
git commit -m "Backup before Phase 2"

# 2. Install dependencies
pip install -r requirements-phase2.txt

# 3. Read the plan (optional but recommended)
cat PHASE_2_VOICE_IMPLEMENTATION_PLAN.md
```

### Implementation Flow

```
Start → PROMPT 1 → Test → PROMPT 2 → Test → PROMPT 3 → Test → 
PROMPT 4 → Test → PROMPT 5 → Test → PROMPT 6 → Test → Done! ✅
```

### After Each Prompt

1. **Review** the generated code
2. **Test** it works (see test commands above)
3. **Commit** your changes
4. **Move** to next prompt

---

## 🎯 Expected Results

### After PROMPT 1 + 2 (Modules)
```
✓ app/voice/asr.py exists
✓ app/voice/tts.py exists
✓ Can import both modules
✓ Basic transcription/synthesis works
```

### After PROMPT 3 (API)
```
✓ app/api/voice_endpoints.py exists
✓ app/api/voice_schemas.py exists
✓ Can import endpoints
✓ Ready for integration
```

### After PROMPT 4 (UI)
```
✓ ui/voice.html exists
✓ ui/voice.js exists
✓ ui/voice.css exists
✓ UI renders in browser
```

### After PROMPT 5 (Integration)
```
✓ Server starts with Phase 2 enabled
✓ Voice endpoints accessible
✓ Phase 1 still works
✓ Logs show "Phase 2 voice endpoints enabled"
```

### After PROMPT 6 (Testing)
```
✓ All Phase 2 tests pass
✓ All Phase 1 tests pass
✓ No breaking changes
✓ Ready for production
```

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ImportError: whisper` | Run `pip install openai-whisper` |
| `ImportError: gTTS` | Run `pip install gTTS` |
| PyAudio install fails | See `PHASE_2_README.md` → Troubleshooting |
| Server won't start | Check logs: `tail -f logs/app.log` |
| Voice endpoint 404 | Verify `PHASE_2_ENABLED=true` in `.env` |
| Phase 1 tests fail | Phase 2 broke something - review changes |
| Audio not playing | Check audio URL in response |
| Microphone not working | Browser needs HTTPS or localhost |

### Quick Fixes

```bash
# Reset if something breaks
git reset --hard HEAD

# Reinstall dependencies
pip install -r requirements-phase2.txt --force-reinstall

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +

# Restart server
pkill -f uvicorn
python -m uvicorn app.main:app --reload
```

---

## 📊 Time Estimates

| Prompt | Component | Time |
|--------|-----------|------|
| 1 | ASR Module | 2h |
| 2 | TTS Module | 2h |
| 3 | Voice API | 3h |
| 4 | Voice UI | 4h |
| 5 | Integration | 3h |
| 6 | Testing | 3h |
| **Total** | | **17h** |

Add 20% buffer: **~21 hours total**

---

## 🎓 Pro Tips

1. **Test after each prompt** - Don't skip testing!
2. **Commit frequently** - Easy to rollback if needed
3. **Read error messages** - They usually tell you what's wrong
4. **Check logs** - `tail -f logs/app.log` is your friend
5. **Ask for help** - Provide error messages to AI assistant
6. **Take breaks** - 17 hours is a lot, spread over 2-3 days

---

## 📞 Need Help?

### Full Documentation

- **Complete Plan:** `PHASE_2_VOICE_IMPLEMENTATION_PLAN.md`
- **Architecture:** `PHASE_2_ARCHITECTURE.md`
- **Quick Start:** `PHASE_2_README.md`
- **Checklist:** `PHASE_2_CHECKLIST.md`
- **Prompts:** `PHASE_2_IMPLEMENTATION_PROMPTS.md` (detailed versions)

### Ask AI for Help

**Template:**
```
I'm implementing Phase 2 (PROMPT [number]) for ScamShield AI.

Error: [paste error]

Current code: [paste relevant code]

How do I fix this? Reference PHASE_2_VOICE_IMPLEMENTATION_PLAN.md if needed.
```

---

## ✅ Success!

When all 6 prompts are complete:

1. ✓ Voice recording works
2. ✓ AI responds with voice
3. ✓ Transcription displays
4. ✓ Metadata shows
5. ✓ Intelligence extracted
6. ✓ Phase 1 still works
7. ✓ All tests pass

**You've successfully implemented Phase 2!** 🎉

---

*Quick Reference for: PHASE_2_IMPLEMENTATION_PROMPTS.md*

*Start with: PROMPT 1 (ASR Module)*

*Estimated Time: 17-21 hours*
