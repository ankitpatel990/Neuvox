# Functional Requirements Document: ScamShield AI
## Detailed Requirements & Acceptance Criteria

**Version:** 1.0  
**Date:** January 26, 2026  
**Status:** Approved for Implementation  
**Related Documents:** PRD.md, API_CONTRACT.md, THREAT_MODEL.md

---

## TABLE OF CONTENTS
1. [System Overview](#system-overview)
2. [Functional Requirements](#functional-requirements)
3. [Data Requirements](#data-requirements)
4. [Integration Requirements](#integration-requirements)
5. [Quality Requirements](#quality-requirements)
6. [Acceptance Criteria](#acceptance-criteria)

---

## SYSTEM OVERVIEW

### Architecture Layers
```
Input Layer → Detection Module → Hand-off Decision → Agentic Engagement → Intelligence Extraction → Output Layer
```

### Processing Flow
1. Receive message via API endpoint
2. Detect language (English/Hindi/Hinglish)
3. Classify scam likelihood (confidence score)
4. If scam detected (confidence >0.7), initiate engagement
5. Conduct multi-turn conversation using LangGraph agent
6. Extract intelligence using NER + regex
7. Return structured JSON response

---

## FUNCTIONAL REQUIREMENTS

### FR-1: MESSAGE DETECTION

#### FR-1.1: Language Detection
**Description:** Automatically identify the language of incoming messages

**Requirements:**
- Detect English, Hindi, and Hinglish (code-mixed)
- Return language code: 'en', 'hi', or 'hinglish'
- Confidence threshold: >0.8 for reliable detection
- Fallback: Default to 'en' if detection fails

**Implementation:**
- Library: langdetect
- Fallback: Character set analysis (Devanagari detection)

**Acceptance Criteria:**
- ✅ AC-1.1.1: Correctly identifies Hindi messages (>95% accuracy on test set)
- ✅ AC-1.1.2: Correctly identifies English messages (>98% accuracy)
- ✅ AC-1.1.3: Handles Hinglish without errors
- ✅ AC-1.1.4: Returns language code within 100ms

**Test Cases:**
```
TC-1.1.1: Input "You won 10 lakh rupees!" → Output "en"
TC-1.1.2: Input "आपने जीता 10 लाख रुपये!" → Output "hi"
TC-1.1.3: Input "Aapne jeeta 10 lakh rupees!" → Output "hinglish" or "hi"
TC-1.1.4: Input "" (empty) → Handle gracefully with error
```

---

#### FR-1.2: Scam Classification
**Description:** Classify messages as scam or legitimate using hybrid detection

**Requirements:**
- Primary Model: IndicBERT (ai4bharat/indic-bert)
- Secondary: Keyword matching for high-confidence patterns
- Return confidence score: 0.0-1.0
- Threshold for engagement trigger: 0.7

**Scam Indicators:**
- Keywords: UPI, OTP, bank, police, arrest, prize, lottery, won, urgent, verify
- Hindi keywords: यूपीआई, ओटीपी, बैंक, पुलिस, गिरफ्तार, जीत, इनाम, लॉटरी
- Patterns: Requests for money transfer, personal info, OTP sharing
- Urgency: Immediate action required, threats, time pressure

**Acceptance Criteria:**
- ✅ AC-1.2.1: Achieves >90% accuracy on labeled test dataset (minimum 1000 samples)
- ✅ AC-1.2.2: False positive rate <5%
- ✅ AC-1.2.3: Inference time <500ms per message
- ✅ AC-1.2.4: Handles messages up to 5000 characters
- ✅ AC-1.2.5: Returns calibrated confidence scores (not just 0/1)

**Test Cases:**
```
TC-1.2.1: "Congratulations! You won ₹10 lakh. Share OTP to claim."
  Expected: scam=True, confidence>0.9

TC-1.2.2: "Your account will be suspended. Send money to unblock."
  Expected: scam=True, confidence>0.85

TC-1.2.3: "Hi, how are you? Let's meet for coffee tomorrow."
  Expected: scam=False, confidence<0.2

TC-1.2.4: "Your order #12345 has been shipped."
  Expected: scam=False, confidence<0.3

TC-1.2.5: "आप गिरफ्तार हो जाएंगे। तुरंत UPI पर पैसे भेजें।"
  Expected: scam=True, confidence>0.9
```

---

### FR-2: AGENTIC ENGAGEMENT

#### FR-2.1: Persona Management
**Description:** Generate and maintain believable personas for scammer engagement

**Requirements:**
- Three persona types: Elderly (60+), Eager Victim, Confused User
- Persona selection based on scam type (lottery→eager, police→fearful)
- Consistent persona throughout conversation
- Natural language generation via Groq Llama 3.1 70B

**Persona Characteristics:**

**Elderly Persona:**
- Age: 60-75 years
- Tech literacy: Low
- Speech pattern: Polite, trusting, confused by technology
- Response time: Slower (simulated by strategic delays)
- Questions: Basic ("Which button?", "What is UPI?")

**Eager Victim Persona:**
- Age: 35-50 years
- Motivation: Financial gain
- Speech pattern: Excited, compliant, seeking instructions
- Response time: Fast, enthusiastic
- Questions: Process-oriented ("How do I claim?", "What next?")

**Confused User Persona:**
- Age: 25-40 years
- Tech literacy: Medium
- Speech pattern: Uncertain, seeks verification
- Response time: Medium
- Questions: Skeptical but interested ("Is this real?", "Show proof")

**Acceptance Criteria:**
- ✅ AC-2.1.1: Persona selection aligns with scam type (tested on 50+ scenarios)
- ✅ AC-2.1.2: Responses match persona characteristics (human evaluation >80% believability)
- ✅ AC-2.1.3: No persona switching mid-conversation
- ✅ AC-2.1.4: Responses in correct language (match input language)

**Test Cases:**
```
TC-2.1.1: Scam type="lottery" → Persona="eager_victim"
TC-2.1.2: Scam type="police_threat" → Persona="elderly_fearful"
TC-2.1.3: Scam type="bank_fraud" → Persona="confused_user"
TC-2.1.4: Verify Hindi persona response is in Hindi
TC-2.1.5: Verify persona consistency over 10+ turns
```

---

#### FR-2.2: Conversational Strategy
**Description:** Execute multi-turn engagement with adaptive stalling tactics

**Requirements:**
- Maximum turns: 20
- Minimum turns: 1 (if immediate intelligence extraction)
- Turn-based strategy progression:
  - Turns 1-5: Build rapport, show interest
  - Turns 6-12: Express confusion, request clarifications
  - Turns 13-20: Probe for specific details (bank/UPI/links)

**Stalling Tactics:**
1. Repeated clarification requests
2. Technical confusion ("My phone is old, which app?")
3. Fake delays ("Let me find my card...")
4. Partial compliance ("I tried but it didn't work")
5. Verification requests ("Send official document")

**Termination Conditions:**
1. Maximum turns reached (20)
2. High-confidence intelligence extracted (UPI ID or bank account found)
3. Scammer disconnects
4. Safety violation detected (threats, violence)

**Acceptance Criteria:**
- ✅ AC-2.2.1: Average engagement duration >10 turns on test conversations
- ✅ AC-2.2.2: Strategy progression follows defined turn brackets
- ✅ AC-2.2.3: Termination logic correctly triggers on conditions
- ✅ AC-2.2.4: No infinite loops (hard cap at 20 turns)
- ✅ AC-2.2.5: Response time per turn <2s (p95)

**Test Cases:**
```
TC-2.2.1: Simulate 15-turn conversation, verify strategy transitions
TC-2.2.2: Extract UPI at turn 5, verify early termination
TC-2.2.3: Reach 20 turns without extraction, verify graceful exit
TC-2.2.4: Scammer sends violent threat, verify safety termination
TC-2.2.5: Measure response latency across 100 turns
```

---

#### FR-2.3: State Management
**Description:** Maintain conversation context and history

**Requirements:**
- Session ID: UUID v4 generated per conversation
- State storage: Redis (active sessions, 1-hour TTL)
- History storage: PostgreSQL (permanent logs)
- Context window: Last 5 turns for LLM prompt

**State Schema:**
```python
{
  "session_id": "uuid-string",
  "language": "en|hi|hinglish",
  "persona": "elderly|eager|confused",
  "turn_count": int,
  "scam_confidence": float,
  "messages": [
    {"turn": int, "sender": "scammer|agent", "message": str, "timestamp": str}
  ],
  "extracted_intel": {
    "upi_ids": [],
    "bank_accounts": [],
    "ifsc_codes": [],
    "phone_numbers": [],
    "phishing_links": []
  },
  "strategy": "build_trust|express_confusion|probe_details",
  "created_at": "ISO-8601 timestamp",
  "updated_at": "ISO-8601 timestamp"
}
```

**Acceptance Criteria:**
- ✅ AC-2.3.1: State persists across API calls within session
- ✅ AC-2.3.2: Session expires after 1 hour of inactivity
- ✅ AC-2.3.3: Conversation history retrievable via session ID
- ✅ AC-2.3.4: Redis failure gracefully degrades to stateless mode
- ✅ AC-2.3.5: PostgreSQL stores complete conversation logs

**Test Cases:**
```
TC-2.3.1: Create session, verify state in Redis
TC-2.3.2: Make 5 calls with same session_id, verify turn_count=5
TC-2.3.3: Wait 61 minutes, verify session expired
TC-2.3.4: Retrieve conversation via GET /honeypot/session/{id}
TC-2.3.5: Simulate Redis failure, verify API still responds
```

---

### FR-3: INTELLIGENCE EXTRACTION

#### FR-3.1: Entity Extraction
**Description:** Extract financial and contact information using hybrid NER + regex

**Requirements:**
- Primary: spaCy NER (en_core_web_sm)
- Secondary: Regex patterns for structured data
- Validation: Format checking for extracted entities
- Confidence scoring: Per entity type

**Target Entities:**

**1. UPI IDs**
- Pattern: `[a-zA-Z0-9._-]+@[a-zA-Z]+`
- Examples: user@paytm, 9876543210@ybl, merchant.name@oksbi
- Validation: Must contain @ symbol, valid provider suffix
- Confidence: High if matches pattern exactly

**2. Bank Account Numbers**
- Pattern: `\b\d{9,18}\b`
- Validation: Luhn algorithm (if available), length check
- Disambiguation: Exclude phone numbers (10 digits), OTPs (4-6 digits)
- Confidence: Medium (needs context validation)

**3. IFSC Codes**
- Pattern: `\b[A-Z]{4}0[A-Z0-9]{6}\b`
- Example: SBIN0001234, HDFC0000123
- Validation: First 4 chars = bank code, 5th char = 0
- Confidence: High if matches pattern

**4. Phone Numbers**
- Pattern: `(?:\+91[\s-]?)?[6-9]\d{9}\b`
- Format: +91XXXXXXXXXX or 10-digit starting with 6-9
- Validation: Indian mobile number rules
- Confidence: High for +91 prefix, medium otherwise

**5. Phishing Links**
- Pattern: `https?://[^\s<>"{}|\\^`\[\]]+`
- Validation: Valid URL structure, reachable domain (optional)
- Risk scoring: Known scam domains (future enhancement)
- Confidence: High if valid URL structure

**Acceptance Criteria:**
- ✅ AC-3.1.1: UPI ID extraction precision >90%
- ✅ AC-3.1.2: Bank account extraction precision >85% (with context)
- ✅ AC-3.1.3: IFSC code extraction precision >95%
- ✅ AC-3.1.4: Phone number extraction precision >90%
- ✅ AC-3.1.5: Phishing link extraction precision >95%
- ✅ AC-3.1.6: No false positives for dates/orderIDs as bank accounts
- ✅ AC-3.1.7: Extraction latency <200ms per message

**Test Cases:**
```
TC-3.1.1: "Send to scammer@paytm" → Extract ["scammer@paytm"]
TC-3.1.2: "Account 1234567890123 IFSC SBIN0001234" → Extract both
TC-3.1.3: "Call +919876543210" → Extract ["+919876543210"]
TC-3.1.4: "Visit http://fake-bank.com/login" → Extract URL
TC-3.1.5: "Order #123456789" → Do NOT extract as bank account
TC-3.1.6: "OTP 654321" → Do NOT extract as bank account
TC-3.1.7: Hindi text with embedded numbers → Extract correctly
```

---

#### FR-3.2: Confidence Scoring
**Description:** Calculate confidence for each extraction and overall extraction quality

**Requirements:**
- Per-entity confidence: 0.0-1.0
- Overall extraction confidence: Weighted average
- Factors: Pattern match strength, context validation, redundancy

**Confidence Calculation:**
```
entity_confidence = 
  pattern_match_score (0.5 weight) +
  context_validation_score (0.3 weight) +
  redundancy_score (0.2 weight)

overall_confidence = 
  Σ(entity_confidence × entity_weight) / Σ(entity_weight)

Weights:
  upi_ids: 0.3
  bank_accounts: 0.3
  ifsc_codes: 0.2
  phone_numbers: 0.1
  phishing_links: 0.1
```

**Acceptance Criteria:**
- ✅ AC-3.2.1: Confidence scores calibrated (high conf → high precision)
- ✅ AC-3.2.2: Overall confidence >0.7 indicates reliable extraction
- ✅ AC-3.2.3: Low confidence entities flagged for review
- ✅ AC-3.2.4: Confidence scores returned in API response

**Test Cases:**
```
TC-3.2.1: Extract valid UPI → confidence >0.9
TC-3.2.2: Extract ambiguous 10-digit number → confidence <0.6
TC-3.2.3: Extract 2 UPIs + 1 bank account → overall conf >0.8
TC-3.2.4: No extractions → overall conf = 0.0
```

---

#### FR-3.3: Hindi Text Handling
**Description:** Extract entities from Hindi and Hinglish text

**Requirements:**
- Devanagari digit conversion (०-९ → 0-9)
- Romanized UPI/account numbers in Hindi text
- Handle code-mixed sentences

**Special Handling:**
```python
# Convert Devanagari digits
"खाता ९८७६५४३२१०" → "खाता 9876543210" → Extract "9876543210"

# Romanized patterns in Hindi
"यूपीआई scammer@paytm पर भेजें" → Extract "scammer@paytm"

# Code-mixed
"Bhejo 5000 rupees to mera@paytm" → Extract "mera@paytm"
```

**Acceptance Criteria:**
- ✅ AC-3.3.1: Devanagari digit conversion 100% accurate
- ✅ AC-3.3.2: Extract romanized entities from Hindi text
- ✅ AC-3.3.3: Handle Hinglish without errors
- ✅ AC-3.3.4: Hindi extraction precision within 5% of English

**Test Cases:**
```
TC-3.3.1: "फोन नंबर ९८७६५४३२१०" → Extract "9876543210"
TC-3.3.2: "UPI आईडी test@paytm है" → Extract "test@paytm"
TC-3.3.3: "Aapka account 1234567890 hai" → Extract "1234567890"
```

---

### FR-4: API INTERFACE

#### FR-4.1: Primary Endpoint
**Description:** POST /honeypot/engage - Main scam detection and engagement endpoint

**Request Schema:**
```json
{
  "message": "string (required, 1-5000 chars)",
  "session_id": "string (optional, UUID v4)",
  "language": "string (optional, 'auto'|'en'|'hi')",
  "mock_scammer_callback": "string (optional, URL for competition testing)"
}
```

**Response Schema (Scam Detected):**
```json
{
  "status": "success|error",
  "scam_detected": boolean,
  "confidence": float (0.0-1.0),
  "language_detected": "en|hi|hinglish",
  "session_id": "string (UUID)",
  "engagement": {
    "agent_response": "string (1-500 chars)",
    "turn_count": integer (1-20),
    "max_turns_reached": boolean,
    "strategy": "build_trust|express_confusion|probe_details",
    "persona": "elderly|eager|confused"
  },
  "extracted_intelligence": {
    "upi_ids": ["string"],
    "bank_accounts": ["string"],
    "ifsc_codes": ["string"],
    "phone_numbers": ["string"],
    "phishing_links": ["string"],
    "extraction_confidence": float (0.0-1.0)
  },
  "conversation_history": [
    {
      "turn": integer,
      "sender": "scammer|agent",
      "message": "string",
      "timestamp": "string (ISO-8601)"
    }
  ],
  "metadata": {
    "processing_time_ms": integer,
    "model_version": "string",
    "detection_model": "string",
    "engagement_model": "string"
  }
}
```

**Response Schema (Not Scam):**
```json
{
  "status": "success",
  "scam_detected": false,
  "confidence": float (0.0-1.0),
  "language_detected": "en|hi|hinglish",
  "session_id": "string (UUID)",
  "message": "No scam detected. Message appears legitimate."
}
```

**Acceptance Criteria:**
- ✅ AC-4.1.1: Returns 200 OK for valid requests
- ✅ AC-4.1.2: Returns 400 Bad Request for invalid input
- ✅ AC-4.1.3: Returns 500 Internal Server Error with details on failures
- ✅ AC-4.1.4: Response matches schema exactly (JSON validation)
- ✅ AC-4.1.5: Response time <2s (p95), <1s (p50)
- ✅ AC-4.1.6: Handles concurrent requests (50+)

**Test Cases:**
```
TC-4.1.1: Valid scam message → 200 with scam_detected=true
TC-4.1.2: Valid legitimate message → 200 with scam_detected=false
TC-4.1.3: Empty message → 400 with error details
TC-4.1.4: Message >5000 chars → 400 with error
TC-4.1.5: Invalid session_id format → 400 with error
TC-4.1.6: Load test 100 req/min → All return <2s
```

---

#### FR-4.2: Health Check Endpoint
**Description:** GET /health - Service health monitoring

**Response Schema:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "version": "string (semver)",
  "timestamp": "string (ISO-8601)",
  "dependencies": {
    "groq_api": "online|offline",
    "postgres": "online|offline",
    "redis": "online|offline",
    "models_loaded": boolean
  },
  "uptime_seconds": integer
}
```

**Acceptance Criteria:**
- ✅ AC-4.2.1: Returns 200 if all dependencies healthy
- ✅ AC-4.2.2: Returns 503 if critical dependency fails
- ✅ AC-4.2.3: Response time <100ms
- ✅ AC-4.2.4: Checks Groq API connectivity
- ✅ AC-4.2.5: Checks database connections

**Test Cases:**
```
TC-4.2.1: All systems normal → status="healthy", 200 OK
TC-4.2.2: Redis down → status="degraded", 200 OK
TC-4.2.3: Postgres down → status="unhealthy", 503
TC-4.2.4: Groq API unreachable → status="degraded"
```

---

#### FR-4.3: Session Retrieval Endpoint
**Description:** GET /honeypot/session/{session_id} - Retrieve conversation history

**Response Schema:**
```json
{
  "session_id": "string",
  "language": "en|hi|hinglish",
  "scam_confidence": float,
  "turn_count": integer,
  "conversation_history": [...],
  "extracted_intelligence": {...},
  "created_at": "string (ISO-8601)",
  "updated_at": "string (ISO-8601)"
}
```

**Acceptance Criteria:**
- ✅ AC-4.3.1: Returns 200 with data for valid session_id
- ✅ AC-4.3.2: Returns 404 for non-existent session
- ✅ AC-4.3.3: Returns complete conversation history
- ✅ AC-4.3.4: Response time <500ms

**Test Cases:**
```
TC-4.3.1: Valid session_id → 200 with history
TC-4.3.2: Invalid session_id → 404 Not Found
TC-4.3.3: Expired session → 410 Gone
```

---

### FR-5: DATA PERSISTENCE

#### FR-5.1: Conversation Logging
**Description:** Store all conversations in PostgreSQL

**Database Schema:**
```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    language VARCHAR(10) NOT NULL,
    persona VARCHAR(50),
    scam_detected BOOLEAN DEFAULT FALSE,
    confidence FLOAT,
    turn_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    sender VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE extracted_intelligence (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    upi_ids TEXT[],
    bank_accounts TEXT[],
    ifsc_codes TEXT[],
    phone_numbers TEXT[],
    phishing_links TEXT[],
    extraction_confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_session_id ON conversations(session_id);
CREATE INDEX idx_conversation_id ON messages(conversation_id);
CREATE INDEX idx_created_at ON conversations(created_at);
```

**Acceptance Criteria:**
- ✅ AC-5.1.1: Every conversation creates database record
- ✅ AC-5.1.2: Messages stored with correct turn order
- ✅ AC-5.1.3: Extracted intelligence linked to conversation
- ✅ AC-5.1.4: Database queries <100ms (indexed)
- ✅ AC-5.1.5: Data integrity maintained (foreign keys)

**Test Cases:**
```
TC-5.1.1: Create conversation → Verify in database
TC-5.1.2: Add 10 messages → Verify turn_number 1-10
TC-5.1.3: Extract intelligence → Verify in extracted_intelligence table
TC-5.1.4: Query by session_id → Return <100ms
TC-5.1.5: Delete conversation → Cascade delete messages
```

---

#### FR-5.2: Session State Caching
**Description:** Store active session state in Redis

**Cache Schema:**
```
Key: session:{session_id}
Value: JSON serialized state
TTL: 3600 seconds (1 hour)
```

**Acceptance Criteria:**
- ✅ AC-5.2.1: Session state stored on creation
- ✅ AC-5.2.2: State retrieved within 10ms
- ✅ AC-5.2.3: TTL resets on each interaction
- ✅ AC-5.2.4: Expired sessions cleaned automatically
- ✅ AC-5.2.5: Redis failure degrades gracefully (fallback to DB)

**Test Cases:**
```
TC-5.2.1: Create session → Verify in Redis
TC-5.2.2: Retrieve state → Latency <10ms
TC-5.2.3: Wait 30 mins, interact → TTL extends
TC-5.2.4: Wait 61 mins → Key expires
TC-5.2.5: Shutdown Redis → API continues with degraded performance
```

---

#### FR-5.3: Vector Embeddings Storage
**Description:** Store conversation embeddings in ChromaDB for similarity search

**Collection Schema:**
```python
collection_name: "scam_conversations"
embedding_dimension: 384 (all-MiniLM-L6-v2)
metadata: {
  "session_id": string,
  "language": string,
  "scam_type": string,
  "turn_count": integer
}
```

**Acceptance Criteria:**
- ✅ AC-5.3.1: Embeddings generated for all conversations
- ✅ AC-5.3.2: Similarity search returns relevant results
- ✅ AC-5.3.3: Query time <500ms for top-5 similar
- ✅ AC-5.3.4: Storage persists across restarts

**Test Cases:**
```
TC-5.3.1: Store conversation → Generate embedding
TC-5.3.2: Query similar UPI scams → Return relevant matches
TC-5.3.3: Query with Hindi text → Return Hindi conversations
TC-5.3.4: Restart service → Verify embeddings persist
```

---

## QUALITY REQUIREMENTS

### QR-1: Performance
- **Response Time:** <2s (p95), <1s (p50) for /honeypot/engage
- **Throughput:** 100 requests/minute sustained
- **Model Inference:** <500ms for detection, <1.5s for LLM generation
- **Database Queries:** <100ms per query

### QR-2: Reliability
- **Uptime:** 99%+ during competition testing window
- **Error Rate:** <1% of requests
- **Data Consistency:** 100% (no lost conversations)
- **Graceful Degradation:** Continue operation if Redis fails

### QR-3: Security
- **Input Validation:** All inputs sanitized (XSS, SQL injection prevention)
- **PII Protection:** Phone numbers hashed before storage
- **API Authentication:** (Optional for Phase 1, required for production)
- **Rate Limiting:** 100 req/min per IP

### QR-4: Maintainability
- **Code Coverage:** >80% unit test coverage
- **Documentation:** All functions documented with docstrings
- **Logging:** Structured logging (JSON format) for all operations
- **Monitoring:** Prometheus metrics exported

### QR-5: Usability
- **API Documentation:** OpenAPI/Swagger spec available
- **Error Messages:** Clear, actionable error descriptions
- **Response Format:** Consistent JSON structure
- **Language Support:** Transparent handling of en/hi/hinglish

---

## ACCEPTANCE CRITERIA SUMMARY

### Phase 1 Launch Checklist

**Detection Module:**
- [ ] AC-1.1.1 to AC-1.1.4: Language detection functional
- [ ] AC-1.2.1 to AC-1.2.5: Scam classification >90% accuracy

**Engagement Module:**
- [ ] AC-2.1.1 to AC-2.1.4: Persona management operational
- [ ] AC-2.2.1 to AC-2.2.5: Multi-turn engagement >10 turns avg
- [ ] AC-2.3.1 to AC-2.3.5: State persistence working

**Extraction Module:**
- [ ] AC-3.1.1 to AC-3.1.7: Entity extraction >85% precision
- [ ] AC-3.2.1 to AC-3.2.4: Confidence scoring calibrated
- [ ] AC-3.3.1 to AC-3.3.4: Hindi extraction functional

**API Interface:**
- [ ] AC-4.1.1 to AC-4.1.6: Primary endpoint operational
- [ ] AC-4.2.1 to AC-4.2.5: Health check functional
- [ ] AC-4.3.1 to AC-4.3.4: Session retrieval working

**Data Persistence:**
- [ ] AC-5.1.1 to AC-5.1.5: Conversation logging complete
- [ ] AC-5.2.1 to AC-5.2.5: Redis caching operational
- [ ] AC-5.3.1 to AC-5.3.4: Vector storage functional

**Quality Requirements:**
- [ ] QR-1: Performance targets met
- [ ] QR-2: Reliability targets met
- [ ] QR-3: Security measures implemented
- [ ] QR-4: Code quality standards met
- [ ] QR-5: Usability standards met

---

## TRACEABILITY MATRIX

| Requirement ID | PRD Section | Test Cases | API Endpoint | Database Table |
|----------------|-------------|------------|--------------|----------------|
| FR-1.1 | FR-1 (Detection) | TC-1.1.1-4 | POST /honeypot/engage | conversations.language |
| FR-1.2 | FR-1 (Detection) | TC-1.2.1-5 | POST /honeypot/engage | conversations.scam_detected |
| FR-2.1 | FR-2 (Engagement) | TC-2.1.1-5 | POST /honeypot/engage | conversations.persona |
| FR-2.2 | FR-2 (Engagement) | TC-2.2.1-5 | POST /honeypot/engage | conversations.turn_count |
| FR-2.3 | FR-2 (Engagement) | TC-2.3.1-5 | POST/GET /honeypot/* | conversations, messages |
| FR-3.1 | FR-3 (Extraction) | TC-3.1.1-7 | POST /honeypot/engage | extracted_intelligence |
| FR-3.2 | FR-3 (Extraction) | TC-3.2.1-4 | POST /honeypot/engage | extracted_intelligence.confidence |
| FR-3.3 | FR-3 (Extraction) | TC-3.3.1-3 | POST /honeypot/engage | N/A (preprocessing) |
| FR-4.1 | FR-4 (API) | TC-4.1.1-6 | POST /honeypot/engage | conversations |
| FR-4.2 | FR-4 (API) | TC-4.2.1-4 | GET /health | N/A |
| FR-4.3 | FR-4 (API) | TC-4.3.1-3 | GET /honeypot/session/{id} | conversations |
| FR-5.1 | FR-5 (Data) | TC-5.1.1-5 | N/A | conversations, messages |
| FR-5.2 | FR-5 (Data) | TC-5.2.1-5 | N/A | Redis cache |
| FR-5.3 | FR-5 (Data) | TC-5.3.1-4 | N/A | ChromaDB |

---

**Document Status:** Approved for Implementation  
**Next Steps:** Refer to API_CONTRACT.md for detailed API specifications  
**Test Implementation:** See EVAL_SPEC.md for testing framework
