# GUVI Submission Compliance Plan

## Overview

This document outlines all the changes required to make our ScamShield AI project fully compliant with the GUVI Hackathon submission requirements for the **Agentic Honey-Pot for Scam Detection & Intelligence Extraction** challenge.

**Date Created**: February 2, 2026  
**Status**: ✅ IMPLEMENTED  
**Priority**: CRITICAL - Must complete before submission deadline

---

## ✅ IMPLEMENTATION COMPLETED

All critical items have been implemented:

1. ✅ `app/api/auth.py` - API Key Authentication with x-api-key header
2. ✅ `app/utils/guvi_callback.py` - GUVI callback with suspiciousKeywords & agentNotes
3. ✅ `app/config.py` - Added API_KEY, GUVI_CALLBACK_URL, GUVI_CALLBACK_ENABLED
4. ✅ `app/api/schemas.py` - Added GUVI format schemas, reply field, suspicious_keywords
5. ✅ `app/api/endpoints.py` - Full GUVI format support with auth and callback
6. ✅ `env.example` - Updated with new environment variables

---

## 🔴 CRITICAL MISSING ITEMS

### 1. GUVI Final Result Callback Endpoint

**Priority**: 🔴 CRITICAL (Without this, submission CANNOT be evaluated)

**Requirement**: After engagement completes, send results to GUVI's evaluation endpoint.

**Endpoint**: `POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult`

**Required Payload**:
```json
{
  "sessionId": "abc123-session-id",
  "scamDetected": true,
  "totalMessagesExchanged": 18,
  "extractedIntelligence": {
    "bankAccounts": ["XXXX-XXXX-XXXX"],
    "upiIds": ["scammer@upi"],
    "phishingLinks": ["http://malicious-link.example"],
    "phoneNumbers": ["+91XXXXXXXXXX"],
    "suspiciousKeywords": ["urgent", "verify now", "account blocked"]
  },
  "agentNotes": "Scammer used urgency tactics and payment redirection"
}
```

**Implementation Tasks**:
- [ ] Create `app/utils/guvi_callback.py` with callback function
- [ ] Add `suspiciousKeywords` extraction to extractor module
- [ ] Add `agentNotes` generation (summary of scammer behavior)
- [ ] Integrate callback into endpoint when engagement completes
- [ ] Add configuration for callback URL (allow testing with mock endpoint)
- [ ] Add error handling and retry logic for callback failures

**When to Send Callback**:
- When `max_turns_reached` is True (20 turns completed)
- When `extraction_confidence` >= 0.85 (high confidence extraction)
- When session is explicitly terminated

---

### 2. API Key Authentication (x-api-key Header)

**Priority**: 🔴 CRITICAL

**Requirement**: "Participants must deploy a public API endpoint secured with a user-provided API key"

**Expected Header**: `x-api-key: YOUR_SECRET_API_KEY`

**Implementation Tasks**:
- [ ] Add `API_KEY` to `app/config.py` settings
- [ ] Add `API_KEY` to `env.example`
- [ ] Create `app/api/auth.py` with API key verification middleware
- [ ] Apply middleware to `/honeypot/engage` endpoint
- [ ] Apply middleware to `/honeypot/session/{session_id}` endpoint
- [ ] Keep `/health` endpoint public (no auth required)
- [ ] Add proper 401 Unauthorized error response

---

## 🟡 INPUT/OUTPUT FORMAT ADJUSTMENTS

### 3. Support GUVI's Exact Input Format

**Priority**: 🟡 HIGH

**Current Input Format** (our implementation):
```json
{
  "message": "string",
  "session_id": "uuid",
  "language": "auto"
}
```

**Required Input Format** (GUVI specification):
```json
{
  "sessionId": "wertyu-dfghj-ertyui",
  "message": {
    "sender": "scammer",
    "text": "Your bank account will be blocked today.",
    "timestamp": "2026-01-21T10:15:30Z"
  },
  "conversationHistory": [
    {
      "sender": "scammer",
      "text": "Previous message",
      "timestamp": "2026-01-21T10:15:30Z"
    },
    {
      "sender": "user",
      "text": "Previous response",
      "timestamp": "2026-01-21T10:16:00Z"
    }
  ],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

**Implementation Tasks**:
- [ ] Create new Pydantic schema `GUVIEngageRequest` in `app/api/schemas.py`
- [ ] Create adapter function to convert GUVI format to our internal format
- [ ] Update `/honeypot/engage` endpoint to accept GUVI format
- [ ] Handle `conversationHistory` to restore session state
- [ ] Map `metadata.language` to our language detection
- [ ] Handle `sessionId` (camelCase) in addition to `session_id` (snake_case)

**Key Field Mappings**:
| GUVI Format | Our Format | Action |
|-------------|------------|--------|
| `sessionId` | `session_id` | Accept both, normalize internally |
| `message.text` | `message` | Extract text from object |
| `message.sender` | N/A | Validate is "scammer" |
| `conversationHistory` | Redis session | Rebuild session from history |
| `metadata.language` | `language` | Map "English"→"en", "Hindi"→"hi" |

---

### 4. Simple Agent Reply Format

**Priority**: 🟡 MEDIUM

**Required Simple Output** (per GUVI spec):
```json
{
  "status": "success",
  "reply": "Why is my account being suspended?"
}
```

**Implementation Tasks**:
- [ ] Add `reply` field to `EngageResponse` schema (alias for `engagement.agent_response`)
- [ ] Ensure response always includes the `reply` field at top level
- [ ] Keep existing detailed response structure (backwards compatible)

---

### 5. Add `suspiciousKeywords` to Extracted Intelligence

**Priority**: 🟡 MEDIUM

**Requirement**: Return keywords like `["urgent", "verify now", "account blocked"]`

**Implementation Tasks**:
- [ ] Add `suspiciousKeywords` field to `ExtractedIntelligence` schema
- [ ] Update `IntelligenceExtractor.extract()` to return detected scam keywords
- [ ] Use existing `ScamDetector.indicators` list for keywords
- [ ] Include in GUVI callback payload

---

### 6. Add `agentNotes` Field

**Priority**: 🟡 MEDIUM

**Requirement**: Summary of scammer behavior like "Scammer used urgency tactics"

**Implementation Tasks**:
- [ ] Create function to generate agent notes from conversation
- [ ] Analyze patterns: urgency tactics, payment requests, impersonation, etc.
- [ ] Store in session state
- [ ] Include in GUVI callback payload
- [ ] Add to API response

---

## 📋 IMPLEMENTATION ORDER

### Phase 1: Critical Security & Callback (Must Do First)
1. API Key Authentication middleware
2. GUVI Callback utility function
3. Integrate callback into endpoint

### Phase 2: Input Format Compatibility
4. New GUVI-format request schema
5. Adapter function for format conversion
6. Update endpoint to accept both formats

### Phase 3: Output Enhancements
7. Add `reply` field to response
8. Add `suspiciousKeywords` extraction
9. Add `agentNotes` generation

### Phase 4: Testing & Validation
10. Test with GUVI's exact input format
11. Test callback with mock endpoint
12. Verify API key authentication
13. End-to-end testing

---

## 📁 FILES TO CREATE/MODIFY

### New Files:
- `app/utils/guvi_callback.py` - GUVI result callback
- `app/api/auth.py` - API key authentication

### Modified Files:
- `app/config.py` - Add API_KEY, GUVI_CALLBACK_URL settings
- `app/api/schemas.py` - Add GUVI request format, reply field, suspiciousKeywords
- `app/api/endpoints.py` - Apply auth, handle GUVI format, trigger callback
- `app/models/extractor.py` - Add suspicious keywords extraction
- `app/agent/honeypot.py` - Add agent notes generation
- `env.example` - Add new environment variables

---

## 🔧 CONFIGURATION ADDITIONS

Add to `env.example`:
```bash
# API Authentication
API_KEY=your-secure-api-key-here

# GUVI Hackathon Integration
GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
GUVI_CALLBACK_ENABLED=true
```

---

## ✅ ACCEPTANCE CRITERIA

Before submission, verify:

- [ ] API returns 401 when `x-api-key` header is missing or invalid
- [ ] API accepts GUVI's exact input format with nested message object
- [ ] API returns `reply` field in response
- [ ] `extractedIntelligence` includes `suspiciousKeywords`
- [ ] Response includes `agentNotes` summary
- [ ] GUVI callback is sent when engagement completes
- [ ] Callback includes all required fields in correct format (camelCase)
- [ ] Callback handles network errors gracefully
- [ ] All existing functionality still works

---

## 🧪 TEST CASES

### Test 1: API Key Authentication
```bash
# Should return 401
curl -X POST http://localhost:8000/api/v1/honeypot/engage \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# Should return 200
curl -X POST http://localhost:8000/api/v1/honeypot/engage \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{"message": "test"}'
```

### Test 2: GUVI Input Format
```bash
curl -X POST http://localhost:8000/api/v1/honeypot/engage \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "sessionId": "test-session-123",
    "message": {
      "sender": "scammer",
      "text": "You won 10 lakh! Send OTP now!",
      "timestamp": "2026-02-02T10:00:00Z"
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'
```

### Test 3: Response Format
Verify response contains:
- `status`: "success"
- `reply`: Agent's response text
- `extracted_intelligence.suspiciousKeywords`: Array of keywords

### Test 4: GUVI Callback
Use mock endpoint to verify callback payload structure matches GUVI spec.

---

## 📝 NOTES

1. **Backwards Compatibility**: Keep existing API format working alongside GUVI format
2. **Graceful Degradation**: If GUVI callback fails, don't fail the main request
3. **Logging**: Log all GUVI callbacks for debugging
4. **Testing**: Use mock callback URL for local testing

---

## 🚀 READY TO IMPLEMENT

Once this plan is reviewed, we will proceed with implementation in the order specified above.

**Estimated Time**: 2-3 hours for full implementation

---

*Document Version: 1.0*  
*Last Updated: February 2, 2026*
