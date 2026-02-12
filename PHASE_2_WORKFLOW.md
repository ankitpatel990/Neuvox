# Phase 2 Implementation Workflow

## 📋 Visual Step-by-Step Guide

This document provides a visual workflow for implementing Phase 2 using the 6 prompts.

---

## 🎯 Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    PHASE 2 IMPLEMENTATION                     │
│                         (17-21 hours)                         │
│                                                               │
│  6 Prompts → 6 Components → 1 Complete Voice System          │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Workflow

```
START
  │
  ├─ Read PHASE_2_IMPLEMENTATION_PROMPTS.md
  ├─ Backup code: git commit -m "Before Phase 2"
  ├─ Install: pip install -r requirements-phase2.txt
  │
  ▼
┌────────────────────────────────────────────────────────────┐
│ PROMPT 1: ASR Module (2 hours)                             │
│                                                             │
│ Input:  PROMPT 1 → AI Assistant                            │
│ Output: app/voice/asr.py                                   │
│                                                             │
│ Actions:                                                    │
│  1. Copy PROMPT 1 to AI assistant                          │
│  2. Review generated code                                  │
│  3. Save to app/voice/asr.py                               │
│  4. Test: python -c "from app.voice.asr import ..."        │
│  5. Commit: git commit -m "Add ASR module"                 │
│                                                             │
│ Success Criteria:                                          │
│  ✓ File created                                            │
│  ✓ Import works                                            │
│  ✓ No errors                                               │
└────────────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────────────┐
│ PROMPT 2: TTS Module (2 hours)                             │
│                                                             │
│ Input:  PROMPT 2 → AI Assistant                            │
│ Output: app/voice/tts.py                                   │
│                                                             │
│ Actions:                                                    │
│  1. Copy PROMPT 2 to AI assistant                          │
│  2. Review generated code                                  │
│  3. Save to app/voice/tts.py                               │
│  4. Test: python -c "from app.voice.tts import ..."        │
│  5. Commit: git commit -m "Add TTS module"                 │
│                                                             │
│ Success Criteria:                                          │
│  ✓ File created                                            │
│  ✓ Import works                                            │
│  ✓ No errors                                               │
└────────────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────────────┐
│ PROMPT 3: Voice API (3 hours)                              │
│                                                             │
│ Input:  PROMPT 3 → AI Assistant                            │
│ Output: app/api/voice_endpoints.py                         │
│         app/api/voice_schemas.py                           │
│                                                             │
│ Actions:                                                    │
│  1. Copy PROMPT 3 to AI assistant                          │
│  2. Review generated code (2 files)                        │
│  3. Save both files                                        │
│  4. Test: python -c "from app.api.voice_endpoints ..."     │
│  5. Commit: git commit -m "Add voice API endpoints"        │
│                                                             │
│ Success Criteria:                                          │
│  ✓ Both files created                                      │
│  ✓ Imports work                                            │
│  ✓ No errors                                               │
└────────────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────────────┐
│ PROMPT 4: Voice UI (4 hours)                               │
│                                                             │
│ Input:  PROMPT 4 → AI Assistant                            │
│ Output: ui/voice.html                                      │
│         ui/voice.js                                        │
│         ui/voice.css                                       │
│                                                             │
│ Actions:                                                    │
│  1. Copy PROMPT 4 to AI assistant                          │
│  2. Review generated code (3 files)                        │
│  3. Save all three files                                   │
│  4. Test: Open voice.html in browser                       │
│  5. Commit: git commit -m "Add voice UI"                   │
│                                                             │
│ Success Criteria:                                          │
│  ✓ All 3 files created                                     │
│  ✓ UI renders in browser                                   │
│  ✓ No console errors                                       │
└────────────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────────────┐
│ PROMPT 5: Integration (3 hours)                            │
│                                                             │
│ Input:  PROMPT 5 → AI Assistant                            │
│ Output: Updated app/config.py                              │
│         Updated app/main.py                                │
│         Updated .env.example                               │
│                                                             │
│ Actions:                                                    │
│  1. Copy PROMPT 5 to AI assistant                          │
│  2. Review changes to 3 files                              │
│  3. Apply changes carefully                                │
│  4. Add to .env: PHASE_2_ENABLED=true                      │
│  5. Test: python -m uvicorn app.main:app --reload          │
│  6. Check logs for "Phase 2 voice endpoints enabled"       │
│  7. Test Phase 1: curl http://localhost:8000/api/v1/health │
│  8. Commit: git commit -m "Integrate Phase 2"              │
│                                                             │
│ Success Criteria:                                          │
│  ✓ Server starts                                           │
│  ✓ Phase 2 endpoints available                             │
│  ✓ Phase 1 still works                                     │
│  ✓ No errors in logs                                       │
└────────────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────────────┐
│ PROMPT 6: Testing (3 hours)                                │
│                                                             │
│ Input:  PROMPT 6 → AI Assistant                            │
│ Output: tests/unit/test_voice_asr.py                       │
│         tests/unit/test_voice_tts.py                       │
│         tests/integration/test_voice_api.py                │
│                                                             │
│ Actions:                                                    │
│  1. Copy PROMPT 6 to AI assistant                          │
│  2. Review generated tests (3 files)                       │
│  3. Save all test files                                    │
│  4. Run: pytest tests/unit/test_voice_*.py -v              │
│  5. Run: pytest tests/integration/test_voice_api.py -v     │
│  6. Run: pytest tests/ -v (ALL tests)                      │
│  7. Fix any failures                                       │
│  8. Commit: git commit -m "Add Phase 2 tests"              │
│                                                             │
│ Success Criteria:                                          │
│  ✓ All test files created                                  │
│  ✓ All Phase 2 tests pass                                  │
│  ✓ All Phase 1 tests pass                                  │
│  ✓ No breaking changes                                     │
└────────────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────────────┐
│ FINAL VALIDATION                                           │
│                                                             │
│ Manual Testing:                                            │
│  1. Open http://localhost:8000/ui/voice.html               │
│  2. Click "Start Recording"                                │
│  3. Speak: "Your account is blocked. Send OTP now!"        │
│  4. Click "Stop Recording"                                 │
│  5. Wait for processing                                    │
│  6. Verify:                                                │
│     ✓ Transcription appears                                │
│     ✓ AI reply text appears                                │
│     ✓ Audio player appears                                 │
│     ✓ AI voice plays                                       │
│     ✓ Metadata displays                                    │
│     ✓ Intelligence extracted (if any)                      │
│                                                             │
│  7. Test Phase 1:                                          │
│     Open http://localhost:8000/ui/index.html               │
│     ✓ Text chat still works                                │
│                                                             │
│  8. Final commit: git commit -m "Phase 2 complete"         │
└────────────────────────────────────────────────────────────┘
  │
  ▼
✅ PHASE 2 COMPLETE!
```

---

## 📊 Detailed Prompt Flow

### PROMPT 1: ASR Module

```
┌─────────────────────────────────────────────────────────┐
│ YOU                                                      │
│  │                                                       │
│  │ Copy PROMPT 1                                        │
│  │ "Create ASR module with Whisper..."                 │
│  ▼                                                       │
│ AI ASSISTANT                                            │
│  │                                                       │
│  │ Generates app/voice/asr.py                           │
│  │ - ASREngine class                                    │
│  │ - transcribe() method                                │
│  │ - Whisper integration                                │
│  │ - Error handling                                     │
│  ▼                                                       │
│ YOU                                                      │
│  │                                                       │
│  │ Review code                                          │
│  │ Save to app/voice/asr.py                             │
│  │ Test: python -c "from app.voice.asr import ..."      │
│  │ Commit: git commit -m "Add ASR module"               │
│  ▼                                                       │
│ ✅ CHECKPOINT: ASR module works                         │
└─────────────────────────────────────────────────────────┘
```

### PROMPT 2: TTS Module

```
┌─────────────────────────────────────────────────────────┐
│ YOU                                                      │
│  │                                                       │
│  │ Copy PROMPT 2                                        │
│  │ "Create TTS module with gTTS..."                    │
│  ▼                                                       │
│ AI ASSISTANT                                            │
│  │                                                       │
│  │ Generates app/voice/tts.py                           │
│  │ - TTSEngine class                                    │
│  │ - synthesize() method                                │
│  │ - gTTS integration                                   │
│  │ - Language mapping                                   │
│  ▼                                                       │
│ YOU                                                      │
│  │                                                       │
│  │ Review code                                          │
│  │ Save to app/voice/tts.py                             │
│  │ Test: python -c "from app.voice.tts import ..."      │
│  │ Commit: git commit -m "Add TTS module"               │
│  ▼                                                       │
│ ✅ CHECKPOINT: TTS module works                         │
└─────────────────────────────────────────────────────────┘
```

### PROMPT 3: Voice API

```
┌─────────────────────────────────────────────────────────┐
│ YOU                                                      │
│  │                                                       │
│  │ Copy PROMPT 3                                        │
│  │ "Create voice API endpoints..."                     │
│  ▼                                                       │
│ AI ASSISTANT                                            │
│  │                                                       │
│  │ Generates:                                           │
│  │ 1. app/api/voice_schemas.py                          │
│  │    - VoiceEngageResponse                             │
│  │    - TranscriptionMetadata                           │
│  │    - VoiceFraudMetadata                              │
│  │                                                       │
│  │ 2. app/api/voice_endpoints.py                        │
│  │    - POST /api/v1/voice/engage                       │
│  │    - GET /api/v1/voice/audio/{filename}              │
│  │    - GET /api/v1/voice/health                        │
│  ▼                                                       │
│ YOU                                                      │
│  │                                                       │
│  │ Review both files                                    │
│  │ Save both files                                      │
│  │ Test imports                                         │
│  │ Commit: git commit -m "Add voice API"                │
│  ▼                                                       │
│ ✅ CHECKPOINT: API code ready                           │
└─────────────────────────────────────────────────────────┘
```

### PROMPT 4: Voice UI

```
┌─────────────────────────────────────────────────────────┐
│ YOU                                                      │
│  │                                                       │
│  │ Copy PROMPT 4                                        │
│  │ "Create voice UI with recording..."                 │
│  ▼                                                       │
│ AI ASSISTANT                                            │
│  │                                                       │
│  │ Generates:                                           │
│  │ 1. ui/voice.html                                     │
│  │    - Recording controls                              │
│  │    - Conversation display                            │
│  │    - Metadata section                                │
│  │                                                       │
│  │ 2. ui/voice.js                                       │
│  │    - MediaRecorder API                               │
│  │    - API integration                                 │
│  │    - UI updates                                      │
│  │                                                       │
│  │ 3. ui/voice.css                                      │
│  │    - Dark theme                                      │
│  │    - Recording status                                │
│  │    - Message bubbles                                 │
│  ▼                                                       │
│ YOU                                                      │
│  │                                                       │
│  │ Review all 3 files                                   │
│  │ Save all files                                       │
│  │ Open voice.html in browser                           │
│  │ Commit: git commit -m "Add voice UI"                 │
│  ▼                                                       │
│ ✅ CHECKPOINT: UI renders                               │
└─────────────────────────────────────────────────────────┘
```

### PROMPT 5: Integration

```
┌─────────────────────────────────────────────────────────┐
│ YOU                                                      │
│  │                                                       │
│  │ Copy PROMPT 5                                        │
│  │ "Integrate Phase 2 into main app..."                │
│  ▼                                                       │
│ AI ASSISTANT                                            │
│  │                                                       │
│  │ Provides updates for:                                │
│  │ 1. app/config.py                                     │
│  │    + PHASE_2_ENABLED                                 │
│  │    + WHISPER_MODEL                                   │
│  │    + TTS_ENGINE                                      │
│  │    + Other Phase 2 settings                          │
│  │                                                       │
│  │ 2. app/main.py                                       │
│  │    + Conditional voice router inclusion              │
│  │                                                       │
│  │ 3. .env.example                                      │
│  │    + Phase 2 config section                          │
│  ▼                                                       │
│ YOU                                                      │
│  │                                                       │
│  │ Review changes carefully                             │
│  │ Apply updates to all 3 files                         │
│  │ Add PHASE_2_ENABLED=true to .env                     │
│  │ Start server: uvicorn app.main:app --reload          │
│  │ Check logs                                           │
│  │ Test Phase 1 still works                             │
│  │ Commit: git commit -m "Integrate Phase 2"            │
│  ▼                                                       │
│ ✅ CHECKPOINT: Phase 2 integrated                       │
└─────────────────────────────────────────────────────────┘
```

### PROMPT 6: Testing

```
┌─────────────────────────────────────────────────────────┐
│ YOU                                                      │
│  │                                                       │
│  │ Copy PROMPT 6                                        │
│  │ "Create tests for Phase 2..."                       │
│  ▼                                                       │
│ AI ASSISTANT                                            │
│  │                                                       │
│  │ Generates:                                           │
│  │ 1. tests/unit/test_voice_asr.py                      │
│  │    - Test ASREngine                                  │
│  │    - Test transcription                              │
│  │    - Test error handling                             │
│  │                                                       │
│  │ 2. tests/unit/test_voice_tts.py                      │
│  │    - Test TTSEngine                                  │
│  │    - Test synthesis                                  │
│  │    - Test language mapping                           │
│  │                                                       │
│  │ 3. tests/integration/test_voice_api.py               │
│  │    - Test voice endpoints                            │
│  │    - Test full flow                                  │
│  │    - Test Phase 1 unaffected                         │
│  ▼                                                       │
│ YOU                                                      │
│  │                                                       │
│  │ Review all test files                                │
│  │ Save all files                                       │
│  │ Run: pytest tests/unit/test_voice_*.py               │
│  │ Run: pytest tests/integration/test_voice_api.py      │
│  │ Run: pytest tests/ (all tests)                       │
│  │ Fix any failures                                     │
│  │ Commit: git commit -m "Add Phase 2 tests"            │
│  ▼                                                       │
│ ✅ CHECKPOINT: All tests pass                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Progress Tracking

### Visual Progress Bar

```
PROMPT 1: [████████████████████] 100% ✅
PROMPT 2: [████████████████████] 100% ✅
PROMPT 3: [████████████████████] 100% ✅
PROMPT 4: [████████████████████] 100% ✅
PROMPT 5: [████████████████████] 100% ✅
PROMPT 6: [████████████████████] 100% ✅

Overall:   [████████████████████] 100% ✅ COMPLETE!
```

### Time Tracking

```
Start Time: ___________

PROMPT 1: Start _______ End _______ Duration _______
PROMPT 2: Start _______ End _______ Duration _______
PROMPT 3: Start _______ End _______ Duration _______
PROMPT 4: Start _______ End _______ Duration _______
PROMPT 5: Start _______ End _______ Duration _______
PROMPT 6: Start _______ End _______ Duration _______

Total Duration: _______
```

---

## 🚦 Decision Points

### After Each Prompt

```
┌─────────────────────────────────────────┐
│ Did the code generate successfully?     │
└─────────────┬───────────────────────────┘
              │
         ┌────┴────┐
         │   YES   │   NO
         │         │   │
         ▼         │   ▼
    Continue       │   ┌──────────────────────┐
    to next        │   │ Debug:               │
    prompt         │   │ - Check error msg    │
                   │   │ - Review prompt      │
                   │   │ - Ask AI for help    │
                   │   │ - Try again          │
                   │   └──────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │ Did tests pass?      │
         └─────────┬────────────┘
                   │
              ┌────┴────┐
              │   YES   │   NO
              │         │   │
              ▼         │   ▼
         Continue       │   ┌──────────────────────┐
         to next        │   │ Debug:               │
         prompt         │   │ - Read error output  │
                        │   │ - Fix code           │
                        │   │ - Run tests again    │
                        │   └──────────────────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │ Commit and continue  │
              └─────────────────────┘
```

---

## 📋 Checklist Format

Print this and check off as you go:

```
□ SETUP
  □ Read PHASE_2_IMPLEMENTATION_PROMPTS.md
  □ Backup: git commit -m "Before Phase 2"
  □ Install: pip install -r requirements-phase2.txt

□ PROMPT 1: ASR Module (_____ hours)
  □ Copy prompt to AI
  □ Review generated code
  □ Save app/voice/asr.py
  □ Test import
  □ Commit changes

□ PROMPT 2: TTS Module (_____ hours)
  □ Copy prompt to AI
  □ Review generated code
  □ Save app/voice/tts.py
  □ Test import
  □ Commit changes

□ PROMPT 3: Voice API (_____ hours)
  □ Copy prompt to AI
  □ Review generated code (2 files)
  □ Save voice_schemas.py
  □ Save voice_endpoints.py
  □ Test imports
  □ Commit changes

□ PROMPT 4: Voice UI (_____ hours)
  □ Copy prompt to AI
  □ Review generated code (3 files)
  □ Save voice.html
  □ Save voice.js
  □ Save voice.css
  □ Test UI renders
  □ Commit changes

□ PROMPT 5: Integration (_____ hours)
  □ Copy prompt to AI
  □ Review changes (3 files)
  □ Update app/config.py
  □ Update app/main.py
  □ Update .env.example
  □ Set PHASE_2_ENABLED=true
  □ Start server
  □ Check logs
  □ Test Phase 1
  □ Commit changes

□ PROMPT 6: Testing (_____ hours)
  □ Copy prompt to AI
  □ Review tests (3 files)
  □ Save test_voice_asr.py
  □ Save test_voice_tts.py
  □ Save test_voice_api.py
  □ Run Phase 2 tests
  □ Run all tests
  □ Fix failures
  □ Commit changes

□ FINAL VALIDATION
  □ Manual voice test
  □ Phase 1 still works
  □ All tests pass
  □ Documentation updated
  □ Final commit

✅ DONE!
```

---

## 🎉 Completion

When you reach this point:

```
┌────────────────────────────────────────────────────────┐
│                                                         │
│              🎉 PHASE 2 COMPLETE! 🎉                    │
│                                                         │
│  ✓ ASR Module working                                  │
│  ✓ TTS Module working                                  │
│  ✓ Voice API working                                   │
│  ✓ Voice UI working                                    │
│  ✓ Integration complete                                │
│  ✓ All tests passing                                   │
│  ✓ Phase 1 still working                               │
│                                                         │
│  You can now:                                          │
│  - Record voice messages                               │
│  - Get AI voice replies                                │
│  - See transcriptions                                  │
│  - Extract intelligence from voice                     │
│                                                         │
│  Next: Deploy and demo! 🚀                             │
│                                                         │
└────────────────────────────────────────────────────────┘
```

---

*Visual workflow for: PHASE_2_IMPLEMENTATION_PROMPTS.md*

*Start with: PROMPT 1 (ASR Module)*

*Track progress with this document!*
