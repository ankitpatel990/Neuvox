# ScamShield AI: Agentic Honeypot System - FINAL IMPLEMENTATION SPECIFICATION
## India AI Impact Buildathon 2026 - Challenge 2
## Target: TOP 10 from 40,000 Participants

**Author/Team Lead:** Shivam Bhuva (@shivambhuva8866)  
**Date:** January 26, 2026  
**Submission Deadline:** February 5, 2026, 11:59 PM  
**Challenge:** Agentic Honey-Pot for Scam Detection & Intelligence Extraction  
**Testing Mode:** API Endpoint Submission (Mock Scammer API Integration)

---

## EXECUTIVE SUMMARY

This document provides the **production-ready implementation specification** for ScamShield AI's Agentic Honeypot System. Built exclusively for Challenge 2 of the India AI Impact Buildathon 2026, this system autonomously detects scam messages, engages scammers with believable AI personas, and extracts actionable intelligence (bank accounts, UPI IDs, phishing links).

**Key Differentiators:**
- ✅ **100% FREE TIER** - Zero paid APIs or services
- ✅ **Phased Implementation** - Text-first (Phase 1), Audio-later (Phase 2)
- ✅ **API-First Design** - Direct Mock Scammer API integration
- ✅ **Bilingual Focus** - English + Hindi only (high accuracy)
- ✅ **Structured JSON Outputs** - Competition-ready response format
- ✅ **Production-Grade** - LangGraph ReAct agents with state persistence

**AI Usage:** 90% (detection, agentic engagement, extraction)  
**Non-AI:** 10% (API wrappers, data preprocessing)

---

## PROBLEM STATEMENT (Official Challenge 2 Requirements)

**Objective:** Design an autonomous AI honeypot system that:
1. Detects scam messages accurately
2. Actively engages scammers using believable personas
3. Extracts intelligence: bank accounts, UPI IDs, phishing links
4. Integrates with Mock Scammer API for testing
5. Returns structured JSON outputs

**India's Scam Crisis Context:**
- 500,000+ scam calls/messages daily (TRAI 2025)
- ₹60+ crore daily losses
- 3+ spam messages per citizen
- Predominant scams: UPI fraud, fake loans, police/bank impersonation
- 47% Indians affected by or know victims of scam fraud

---

## IMPLEMENTATION ARCHITECTURE

### **PHASE 1: TEXT-BASED HONEYPOT (Priority for Feb 5 Submission)**

```
┌─────────────────────────────────────────────────────────────────┐
│                      INPUT LAYER                                │
│  Mock Scammer API → JSON Message → ScamShield API Endpoint     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   DETECTION MODULE                              │
│  • IndicBERT (ai4bharat/indic-bert) - Scam Classification      │
│  • Keyword Matching (UPI, OTP, bank, police, arrest)           │
│  • Language Detection (langdetect) - English/Hindi             │
│  • Confidence Scoring (>0.7 = scam trigger)                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  HAND-OFF DECISION                              │
│  IF scam_confidence > 0.7:                                      │
│     → Trigger Honeypot Engagement                              │
│  ELSE:                                                          │
│     → Return "not_scam" response                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               AGENTIC ENGAGEMENT MODULE                         │
│  Framework: LangGraph + ReAct Loop                             │
│  LLM: Groq Llama 3.1 70B (FREE API, 30 req/min)               │
│                                                                 │
│  Agent Components:                                              │
│  ├─ Persona Generator (elderly/gullible/confused)              │
│  ├─ Response Planner (stalling tactics, probing questions)     │
│  ├─ Context Tracker (conversation state in ChromaDB)           │
│  ├─ Safety Monitor (avoid escalation)                          │
│  └─ Termination Logic (max 20 turns or intel extracted)        │
│                                                                 │
│  Engagement Strategy:                                           │
│  • Turn 1-5: Show interest, ask clarifying questions           │
│  • Turn 6-12: Express confusion, request details repeatedly    │
│  • Turn 13-20: Probe for bank/UPI/links with urgency          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            INTELLIGENCE EXTRACTION MODULE                       │
│  • NER: spaCy (en_core_web_sm) for entities                    │
│  • Regex Patterns:                                              │
│    - UPI: [a-zA-Z0-9._]+@[a-zA-Z]+                            │
│    - Bank Account: \d{9,18}                                    │
│    - IFSC: [A-Z]{4}0[A-Z0-9]{6}                               │
│    - Phone: \+91[\s-]?\d{10}|\d{10}                           │
│    - URLs: https?://[^\s]+                                     │
│  • Confidence Scoring per entity (0.0-1.0)                     │
│  • Validation: Check format correctness                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  OUTPUT LAYER (JSON)                            │
│  {                                                              │
│    "scam_detected": true,                                       │
│    "confidence": 0.95,                                          │
│    "language": "hindi",                                         │
│    "conversation_transcript": [...],                            │
│    "extracted_intelligence": {                                  │
│      "upi_ids": ["scammer@paytm"],                             │
│      "bank_accounts": ["1234567890"],                          │
│      "ifsc_codes": ["SBIN0001234"],                            │
│      "phone_numbers": ["+919876543210"],                       │
│      "phishing_links": ["http://fake-bank.com"]                │
│    },                                                           │
│    "engagement_turns": 15,                                      │
│    "extraction_confidence": 0.87                                │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## TECH STACK (100% FREE TIER)

### **1. Core AI/ML Models**

| Component | Model/Library | Source | Free Tier Limits | Why Chosen |
|-----------|--------------|--------|------------------|------------|
| **LLM (Agentic Core)** | Groq Llama 3.1 70B | Groq Cloud API | 30 req/min, 6000/day | Fastest inference (280 tokens/sec), excellent Hindi support |
| **Scam Detection** | ai4bharat/indic-bert | Hugging Face | Unlimited (local) | Best for Hindi-English code-mixed text |
| **NER Extraction** | en_core_web_sm | spaCy | Unlimited (local) | Fast, accurate entity recognition |
| **Language Detection** | langdetect | PyPI | Unlimited (local) | 99%+ accuracy for Hindi/English |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 | Hugging Face | Unlimited (local) | Lightweight, 384-dim embeddings |

### **2. Agentic AI Framework**

```python
# LangGraph + LangChain (Open Source)
langgraph==0.0.20        # State graph orchestration
langchain==0.1.0         # ReAct agent framework
langchain-groq==0.0.1    # Groq LLM integration
```

**Why LangGraph:**
- Built-in state persistence (conversation memory)
- ReAct loop support (Reason → Act → Observe)
- Conditional branching for dynamic engagement
- Multi-turn conversation handling
- Free and open-source

### **3. Vector Database & Storage**

| Component | Tool | Free Tier | Purpose |
|-----------|------|-----------|---------|
| **Vector DB** | ChromaDB | Unlimited (local) | Store conversation embeddings, scam patterns |
| **Relational DB** | PostgreSQL | 1GB (Supabase free) | Conversation logs, scammer profiles |
| **Cache** | Redis | 30MB (Redis Cloud free) | Real-time state, session management |

### **4. API Framework**

```python
# FastAPI + Production Tools
fastapi==0.104.1         # High-performance API
uvicorn==0.24.0          # ASGI server
pydantic==2.5.0          # Data validation
```

### **5. Supporting Libraries**

```python
# NLP & Text Processing
spacy==3.7.2
transformers==4.35.0
torch==2.1.0
sentence-transformers==2.2.2
langdetect==1.0.9

# Vector & Data Storage
chromadb==0.4.18
psycopg2-binary==2.9.9
redis==5.0.1
sqlalchemy==2.0.23

# Utils
python-dotenv==1.0.0
requests==2.31.0
numpy==1.24.3
pandas==2.0.3
```

---

## API ENDPOINT SPECIFICATION

### **1. Competition Submission Endpoint**

**Base URL:** `https://your-api-domain.com/api/v1`

**Endpoint:** `POST /honeypot/engage`

**Request Format:**
```json
{
  "message": "आप जीत गए हैं 10 लाख रुपये! अपना OTP शेयर करें।",
  "session_id": "optional-session-123",
  "language": "auto"
}
```

**Response Format (Scam Detected):**
```json
{
  "status": "success",
  "scam_detected": true,
  "confidence": 0.92,
  "language_detected": "hindi",
  "session_id": "session-123",
  "engagement": {
    "agent_response": "वाह! बहुत अच्छी खबर है। मुझे OTP कहाँ भेजना है?",
    "turn_count": 1,
    "max_turns_reached": false,
    "strategy": "show_interest"
  },
  "extracted_intelligence": {
    "upi_ids": [],
    "bank_accounts": [],
    "ifsc_codes": [],
    "phone_numbers": [],
    "phishing_links": [],
    "extraction_confidence": 0.0
  },
  "conversation_history": [
    {
      "turn": 1,
      "sender": "scammer",
      "message": "आप जीत गए हैं 10 लाख रुपये! अपना OTP शेयर करें।",
      "timestamp": "2026-01-26T10:30:00Z"
    },
    {
      "turn": 1,
      "sender": "agent",
      "message": "वाह! बहुत अच्छी खबर है। मुझे OTP कहाँ भेजना है?",
      "timestamp": "2026-01-26T10:30:02Z"
    }
  ],
  "metadata": {
    "processing_time_ms": 850,
    "model_version": "v1.0.0",
    "detection_model": "indic-bert",
    "engagement_model": "groq-llama-3.1-70b"
  }
}
```

**Response Format (Not Scam):**
```json
{
  "status": "success",
  "scam_detected": false,
  "confidence": 0.15,
  "language_detected": "english",
  "session_id": "session-456",
  "message": "No scam detected. Message appears legitimate."
}
```

### **2. Mock Scammer API Integration**

**How Competition Testing Works:**
1. Competition provides Mock Scammer API endpoint
2. Your system detects scam → sends engagement response
3. Mock Scammer API replies → your system continues conversation
4. Loop continues until intelligence extracted or max turns
5. Your API returns final JSON with extracted data

**Integration Architecture:**
```python
# Your API receives initial message
POST /honeypot/engage
{
  "message": "Send money to UPI: scammer@paytm",
  "mock_scammer_callback": "https://competition-api.com/scammer/reply"
}

# Your system detects scam, engages
# For each turn, call Mock Scammer API:
POST https://competition-api.com/scammer/reply
{
  "session_id": "xyz",
  "agent_message": "Which UPI ID should I use?"
}

# Mock Scammer responds
{
  "scammer_reply": "Use scammer@paytm and send 5000 rupees"
}

# Your system extracts: upi_ids=["scammer@paytm"], continues or terminates
```

### **3. Additional Testing Endpoints**

```python
# Health Check
GET /health
Response: {"status": "healthy", "version": "1.0.0"}

# Batch Processing (if needed)
POST /honeypot/batch
{
  "messages": [
    {"id": "1", "message": "..."},
    {"id": "2", "message": "..."}
  ]
}

# Get Conversation History
GET /honeypot/session/{session_id}
Response: {conversation history JSON}
```

---

## MULTILINGUAL SUPPORT (ENGLISH + HINDI)

### **Language Detection Pipeline**

```python
# Step 1: Detect language
import langdetect
detected_lang = langdetect.detect(message)  # 'en' or 'hi'

# Step 2: Route to appropriate processing
if detected_lang == 'hi':
    # Use IndicBERT for detection
    # Use Hindi persona prompts for engagement
    # Apply Hindi regex patterns
elif detected_lang == 'en':
    # Use IndicBERT (supports English too)
    # Use English persona prompts
    # Apply English regex patterns
```

### **Hindi Support Specifications**

**Models:**
- **Detection:** `ai4bharat/indic-bert` (pre-trained on 12 Indic languages)
- **LLM:** Groq Llama 3.1 70B (strong Hindi capabilities)
- **Alternative:** Gemma-2-9B-it (good Hindi, can run locally)

**Hindi Regex Patterns:**
```python
# Hindi text patterns
HINDI_UPI_KEYWORDS = ['भेजें', 'ट्रांसफर', 'पैसे', 'यूपीआई', 'खाता']
HINDI_SCAM_KEYWORDS = ['जीत', 'ईनाम', 'लॉटरी', 'ओटीपी', 'पुलिस', 'गिरफ्तार']

# Numeric patterns work same (0-9 digits in Hindi text)
UPI_PATTERN = r'[a-zA-Z0-9._]+@[a-zA-Z]+'
ACCOUNT_PATTERN = r'\d{9,18}'
```

**Hindi Persona Examples:**
```
Persona 1 (Elderly):
"अरे वाह! बहुत अच्छा है। लेकिन मुझे समझ नहीं आ रहा, कैसे करूँ?"

Persona 2 (Confused):
"जी हाँ, मैं पैसे भेज दूंगा। पर कौन सा बटन दबाऊं?"

Persona 3 (Eager):
"हाँ हाँ, मुझे पैसे चाहिए। आप कहाँ भेजूं?"
```

### **English Support Specifications**

**Models:**
- Same as Hindi (IndicBERT is multilingual)
- Groq Llama 3.1 70B (native English)

**English Persona Examples:**
```
Persona 1 (Elderly):
"Oh wonderful! But I'm not very good with technology. Can you help me?"

Persona 2 (Confused):
"I want to claim my prize. Where do I send the money again?"

Persona 3 (Eager):
"Yes, I'm ready to transfer. What's your account number?"
```

### **Code-Mixed (Hinglish) Support**

Many Indian scams use code-mixed Hindi-English. IndicBERT handles this well:

```
Input: "Aapne jeeta 10 lakh rupees! Send OTP to claim prize"
Language: hinglish (auto-detected as 'hi' or 'en')
Processing: IndicBERT detects scam patterns in mixed text
Engagement: Respond in same mixing pattern
```

---

## AGENTIC ENGAGEMENT STRATEGY

### **LangGraph ReAct Agent Architecture**

```python
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

# State Definition
class HoneypotState(TypedDict):
    messages: List[dict]
    scam_confidence: float
    turn_count: int
    extracted_intel: dict
    strategy: str
    language: str

# Agent Nodes
def detect_scam(state):
    """Classify if message is scam"""
    # IndicBERT classification
    # Return updated state with confidence

def plan_response(state):
    """Decide engagement strategy"""
    if state['turn_count'] < 5:
        strategy = "show_interest"
    elif state['turn_count'] < 12:
        strategy = "express_confusion"
    else:
        strategy = "probe_details"
    return {"strategy": strategy}

def generate_response(state):
    """LLM generates believable reply"""
    # Groq Llama 3.1 with persona prompt
    # Returns agent message

def extract_intelligence(state):
    """Extract financial details"""
    # spaCy NER + Regex
    # Update extracted_intel

def should_continue(state):
    """Termination logic"""
    if state['turn_count'] >= 20:
        return "end"
    if len(state['extracted_intel']['upi_ids']) > 0:
        return "end"
    return "continue"

# Build Graph
workflow = StateGraph(HoneypotState)
workflow.add_node("detect", detect_scam)
workflow.add_node("plan", plan_response)
workflow.add_node("generate", generate_response)
workflow.add_node("extract", extract_intelligence)

workflow.add_edge("detect", "plan")
workflow.add_edge("plan", "generate")
workflow.add_edge("generate", "extract")
workflow.add_conditional_edges(
    "extract",
    should_continue,
    {
        "continue": "plan",
        "end": END
    }
)

workflow.set_entry_point("detect")
agent = workflow.compile()
```

### **Persona Management**

**Persona Types:**
1. **Elderly Person (60+ years)**
   - Slow to understand technology
   - Trusting and polite
   - Asks basic questions
   - Expresses confusion often

2. **Middle-Aged Eager Victim**
   - Excited about prizes/offers
   - Willing to comply
   - Asks for step-by-step instructions
   - Shows urgency

3. **Young Confused User**
   - Familiar with tech but cautious
   - Asks verification questions
   - Requests proof/links
   - Seeks reassurance

**Persona Selection Logic:**
```python
def select_persona(language, scam_type):
    if "prize" in scam_type or "lottery" in scam_type:
        return "eager_victim"
    elif "police" in scam_type or "arrest" in scam_type:
        return "elderly_fearful"
    else:
        return "confused_user"
```

### **Stalling Tactics**

**Goal:** Keep scammer engaged to extract more information

**Tactics:**
1. **Repeated Clarification:** "I didn't understand, can you repeat?"
2. **Technical Confusion:** "Which button do I press? My phone is old."
3. **Fake Delays:** "Let me find my card. Hold on..."
4. **Partial Compliance:** "I sent something, did you receive?"
5. **Request Verification:** "Can you send me official proof?"

**Turn-by-Turn Strategy:**
```python
ENGAGEMENT_STRATEGY = {
    "turns_1_5": {
        "goal": "Build trust, show interest",
        "tactics": ["express_excitement", "ask_basic_questions"],
        "example": "Really? I won? How do I claim it?"
    },
    "turns_6_12": {
        "goal": "Extract contact/payment info",
        "tactics": ["request_details", "express_confusion"],
        "example": "Should I send money to your account? What's the number?"
    },
    "turns_13_20": {
        "goal": "Force reveal of bank/UPI/links",
        "tactics": ["fake_compliance", "probe_urgently"],
        "example": "I'm ready to transfer. Send me your UPI ID again?"
    }
}
```

---

## INTELLIGENCE EXTRACTION

### **Extraction Targets (Competition Requirements)**

1. **UPI IDs:** `user@paytm`, `9876543210@ybl`, etc.
2. **Bank Account Numbers:** 9-18 digit sequences
3. **IFSC Codes:** 11-character bank codes
4. **Phone Numbers:** +91 or 10-digit Indian numbers
5. **Phishing Links:** URLs to fake websites

### **Extraction Pipeline**

```python
import spacy
import re

nlp = spacy.load("en_core_web_sm")

def extract_intelligence(text):
    intel = {
        "upi_ids": [],
        "bank_accounts": [],
        "ifsc_codes": [],
        "phone_numbers": [],
        "phishing_links": []
    }
    
    # UPI IDs
    upi_pattern = r'\b[a-zA-Z0-9._-]+@[a-zA-Z]+\b'
    intel['upi_ids'] = re.findall(upi_pattern, text)
    
    # Bank Accounts (9-18 digits, with validation)
    account_pattern = r'\b\d{9,18}\b'
    accounts = re.findall(account_pattern, text)
    intel['bank_accounts'] = [acc for acc in accounts if validate_account(acc)]
    
    # IFSC Codes
    ifsc_pattern = r'\b[A-Z]{4}0[A-Z0-9]{6}\b'
    intel['ifsc_codes'] = re.findall(ifsc_pattern, text)
    
    # Phone Numbers
    phone_pattern = r'(?:\+91[\s-]?)?[6-9]\d{9}\b'
    intel['phone_numbers'] = re.findall(phone_pattern, text)
    
    # Phishing Links
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    intel['phishing_links'] = re.findall(url_pattern, text)
    
    # SpaCy NER for additional entities
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "CARDINAL" and len(ent.text) >= 9:
            # Possible account number
            if ent.text not in intel['bank_accounts']:
                intel['bank_accounts'].append(ent.text)
    
    # Calculate confidence
    confidence = calculate_extraction_confidence(intel)
    
    return intel, confidence

def validate_account(account_number):
    """Basic validation for bank account"""
    if len(account_number) < 9 or len(account_number) > 18:
        return False
    # Add checksum validation if needed
    return True

def calculate_extraction_confidence(intel):
    """Score based on number and quality of extractions"""
    score = 0
    weights = {
        'upi_ids': 0.3,
        'bank_accounts': 0.3,
        'ifsc_codes': 0.2,
        'phone_numbers': 0.1,
        'phishing_links': 0.1
    }
    
    for key, weight in weights.items():
        if len(intel[key]) > 0:
            score += weight
    
    return min(score, 1.0)
```

### **Hindi Text Extraction Challenges**

**Challenge:** Numbers in Hindi text (Devanagari script: ०१२३...)
**Solution:** Devanagari digits to ASCII conversion

```python
def convert_devanagari_to_ascii(text):
    """Convert Devanagari digits to ASCII"""
    devanagari_to_ascii = {
        '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
        '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
    }
    for dev, asc in devanagari_to_ascii.items():
        text = text.replace(dev, asc)
    return text

# Apply before extraction
text = convert_devanagari_to_ascii(hindi_text)
intel = extract_intelligence(text)
```

---

## DATABASE & STATE MANAGEMENT

### **PostgreSQL Schema**

```sql
-- Conversations Table
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    language VARCHAR(10) NOT NULL,
    scam_detected BOOLEAN DEFAULT FALSE,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages Table
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    turn_number INTEGER NOT NULL,
    sender VARCHAR(50) NOT NULL, -- 'scammer' or 'agent'
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Extracted Intelligence Table
CREATE TABLE extracted_intelligence (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    upi_ids TEXT[], -- PostgreSQL array
    bank_accounts TEXT[],
    ifsc_codes TEXT[],
    phone_numbers TEXT[],
    phishing_links TEXT[],
    extraction_confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scammer Profiles (for analytics)
CREATE TABLE scammer_profiles (
    id SERIAL PRIMARY KEY,
    phone_hash VARCHAR(64), -- Hashed for privacy
    scam_tactics TEXT[],
    languages_used TEXT[],
    total_conversations INTEGER DEFAULT 1,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **ChromaDB for Vector Storage**

```python
import chromadb
from sentence_transformers import SentenceTransformer

# Initialize
client = chromadb.Client()
collection = client.create_collection("scam_conversations")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Store conversation embeddings
def store_conversation(session_id, messages):
    # Combine messages into single text
    full_text = " ".join([msg['message'] for msg in messages])
    
    # Generate embedding
    embedding = embedder.encode(full_text)
    
    # Store in ChromaDB
    collection.add(
        embeddings=[embedding.tolist()],
        documents=[full_text],
        ids=[session_id],
        metadatas=[{
            "session_id": session_id,
            "turn_count": len(messages),
            "language": messages[0].get('language', 'unknown')
        }]
    )

# Query similar conversations (for learning)
def find_similar_scams(query_text, n_results=5):
    query_embedding = embedder.encode(query_text)
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=n_results
    )
    return results
```

### **Redis for Session State**

```python
import redis
import json

# Initialize Redis
redis_client = redis.Redis(
    host='redis-free-tier.cloud.redislabs.com',
    port=12345,
    password='your-password',
    decode_responses=True
)

# Store session state
def save_session_state(session_id, state):
    redis_client.setex(
        f"session:{session_id}",
        3600,  # 1 hour expiry
        json.dumps(state)
    )

# Retrieve session state
def get_session_state(session_id):
    data = redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else None

# Update turn count
def increment_turn(session_id):
    redis_client.incr(f"session:{session_id}:turns")
```

---

## DEPLOYMENT ARCHITECTURE

### **Free Tier Hosting Options**

| Service | Free Tier | Best For | Limits |
|---------|-----------|----------|--------|
| **Render** | 750 hours/month | FastAPI deployment | Sleep after 15min inactivity |
| **Railway** | $5 credit/month | PostgreSQL + API | 500 hours |
| **Fly.io** | 3 shared VMs | Low-latency API | 160GB transfer/month |
| **Supabase** | 500MB PostgreSQL | Database | 2GB transfer/month |
| **Redis Cloud** | 30MB Redis | Cache/sessions | 30 connections |

### **Recommended Stack for Competition**

```
API Server: Render (or Railway)
├─ FastAPI application
├─ Uvicorn ASGI server
├─ 512MB RAM, 0.1 CPU
└─ Environment: Python 3.11

Database: Supabase PostgreSQL
├─ 500MB storage
├─ 2GB transfer/month
└─ Connection pooling

Cache: Redis Cloud
├─ 30MB storage
├─ Session state management
└─ 30 concurrent connections

Vector DB: ChromaDB (Local)
├─ Embedded in API server
├─ Persistent storage in Docker volume
└─ No external service needed

Model Hosting: Hugging Face (Local)
├─ IndicBERT loaded at startup
├─ spaCy models bundled
└─ 2GB disk space for models

LLM API: Groq Cloud
├─ 30 requests/minute
├─ 6000 requests/day
└─ Zero cost
```

### **Docker Configuration**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download models at build time
RUN python -c "from transformers import AutoModel, AutoTokenizer; \
    AutoModel.from_pretrained('ai4bharat/indic-bert'); \
    AutoTokenizer.from_pretrained('ai4bharat/indic-bert')"
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml (for local testing)
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - POSTGRES_URL=${POSTGRES_URL}
      - REDIS_URL=${REDIS_URL}
    volumes:
      - chromadb_data:/app/chromadb
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=scamshield
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=securepass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  chromadb_data:
  postgres_data:
  redis_data:
```

---

## GROQ API INTEGRATION

### **Setup & Configuration**

```python
# .env file
GROQ_API_KEY=gsk_your_free_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile

# config.py
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
GROQ_TEMPERATURE = 0.7
GROQ_MAX_TOKENS = 500
GROQ_TIMEOUT = 30
```

### **LangChain Integration**

```python
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

# Initialize Groq LLM
llm = ChatGroq(
    model=GROQ_MODEL,
    api_key=GROQ_API_KEY,
    temperature=GROQ_TEMPERATURE,
    max_tokens=GROQ_MAX_TOKENS
)

# Persona Prompts
ELDERLY_HINDI_PROMPT = """
आप एक 65 वर्षीय व्यक्ति हैं जो टेक्नोलॉजी में बहुत अच्छे नहीं हैं।
आप विनम्र और भरोसेमंद हैं। आप अक्सर सवाल पूछते हैं और भ्रमित होते हैं।

आपका लक्ष्य: घोटालेबाज से बैंक डिटेल्स, UPI ID, या लिंक निकालना, लेकिन 
असली व्यक्ति की तरह व्यवहार करना।

बातचीत का इतिहास:
{conversation_history}

घोटालेबाज का संदेश: {scammer_message}

आपका जवाब (केवल एक संदेश, 1-2 वाक्य):
"""

ELDERLY_ENGLISH_PROMPT = """
You are a 65-year-old person who is not tech-savvy.
You are polite, trusting, and often confused about technology.

Your goal: Extract bank details, UPI IDs, or phishing links from the scammer
while acting like a real elderly person.

Conversation history:
{conversation_history}

Scammer's message: {scammer_message}

Your response (only one message, 1-2 sentences):
"""

# Generate response
def generate_agent_response(language, persona, conversation_history, scammer_message):
    if language == "hindi":
        prompt_template = ELDERLY_HINDI_PROMPT
    else:
        prompt_template = ELDERLY_ENGLISH_PROMPT
    
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | llm
    
    response = chain.invoke({
        "conversation_history": format_conversation(conversation_history),
        "scammer_message": scammer_message
    })
    
    return response.content

def format_conversation(history):
    """Format conversation for prompt"""
    formatted = []
    for msg in history[-5:]:  # Last 5 turns for context
        sender = "Scammer" if msg['sender'] == 'scammer' else "You"
        formatted.append(f"{sender}: {msg['message']}")
    return "\n".join(formatted)
```

### **Rate Limiting & Retry Logic**

```python
import time
from functools import wraps

def rate_limited_groq_call(max_retries=3, backoff=2):
    """Decorator for handling Groq rate limits"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "rate_limit" in str(e).lower():
                        wait_time = backoff ** attempt
                        print(f"Rate limited. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise e
            raise Exception("Max retries exceeded")
        return wrapper
    return decorator

@rate_limited_groq_call(max_retries=3)
def call_groq_api(messages):
    """Safe Groq API call with retry"""
    return llm.invoke(messages)
```

---

## EVALUATION METRICS

### **Competition Judging Criteria (Predicted)**

Based on Challenge 2 requirements, judges will likely evaluate:

1. **Scam Detection Accuracy (25%)**
   - True Positive Rate (detecting actual scams)
   - False Positive Rate (avoiding false alarms)
   - Target: >90% accuracy

2. **Engagement Quality (25%)**
   - Naturalness of conversation (believable persona)
   - Number of turns sustained
   - Avoidance of detection by scammer
   - Target: >10 turns average

3. **Intelligence Extraction (30%)**
   - UPI IDs extracted correctly
   - Bank accounts extracted correctly
   - Phishing links identified
   - Extraction accuracy (no false positives)
   - Target: >85% precision, >80% recall

4. **Response Time (10%)**
   - API latency
   - Time to extract intelligence
   - Target: <2s per response

5. **System Robustness (10%)**
   - Handle edge cases (empty messages, very long texts)
   - Error handling
   - API availability

### **Testing Framework**

```python
# test_metrics.py
import pytest
from app.honeypot import HoneypotAgent

def test_scam_detection_accuracy():
    """Test detection accuracy on known scam messages"""
    test_cases = [
        {
            "message": "You won 10 lakh! Send OTP to claim.",
            "expected_scam": True,
            "expected_confidence": 0.9
        },
        {
            "message": "Hi, how are you doing today?",
            "expected_scam": False,
            "expected_confidence": 0.1
        },
        # Add 100+ test cases
    ]
    
    agent = HoneypotAgent()
    correct = 0
    
    for case in test_cases:
        result = agent.detect_scam(case["message"])
        if result["scam_detected"] == case["expected_scam"]:
            correct += 1
    
    accuracy = correct / len(test_cases)
    assert accuracy >= 0.90, f"Accuracy {accuracy} below 90% threshold"

def test_intelligence_extraction():
    """Test extraction accuracy"""
    test_text = """
    Please send 5000 rupees to my UPI: scammer@paytm
    My bank account is 1234567890123 with IFSC SBIN0001234
    Call me at +919876543210 or visit http://fake-bank.com
    """
    
    agent = HoneypotAgent()
    result = agent.extract_intelligence(test_text)
    
    assert "scammer@paytm" in result["upi_ids"]
    assert "1234567890123" in result["bank_accounts"]
    assert "SBIN0001234" in result["ifsc_codes"]
    assert "+919876543210" in result["phone_numbers"]
    assert "http://fake-bank.com" in result["phishing_links"]

def test_response_latency():
    """Test API response time"""
    import time
    agent = HoneypotAgent()
    
    start = time.time()
    result = agent.engage("Send money to win prize!")
    latency = time.time() - start
    
    assert latency < 2.0, f"Latency {latency}s exceeds 2s threshold"
```

### **Monitoring Dashboard**

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
scam_detection_total = Counter(
    'scam_detection_total',
    'Total number of scam detections',
    ['language', 'result']
)

intelligence_extracted = Counter(
    'intelligence_extracted_total',
    'Total pieces of intelligence extracted',
    ['type']  # upi, bank_account, etc.
)

response_time = Histogram(
    'response_time_seconds',
    'Response time in seconds',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

active_sessions = Gauge(
    'active_honeypot_sessions',
    'Number of active honeypot sessions'
)

# Use in code
scam_detection_total.labels(language='hindi', result='scam').inc()
intelligence_extracted.labels(type='upi_id').inc()
response_time.observe(1.2)
```

---

## PHASE 2: AUDIO INTEGRATION (POST-TEXT IMPLEMENTATION)

**Note:** Only proceed with Phase 2 after Phase 1 is fully tested and working.

### **Phase 2 Additions**

```python
# Additional requirements for Phase 2
openai-whisper==20231117   # ASR for audio transcription
torchaudio==2.1.0          # Audio processing
librosa==0.10.1            # Audio features
soundfile==0.12.1          # Audio I/O
pydub==0.25.1              # Audio format conversion
```

### **Audio Endpoint**

```python
# POST /honeypot/engage-audio
# Accept: multipart/form-data or JSON with base64 audio

@app.post("/honeypot/engage-audio")
async def engage_audio(audio_file: UploadFile):
    # Step 1: Save audio temporarily
    temp_path = f"/tmp/{audio_file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await audio_file.read())
    
    # Step 2: Transcribe with Whisper
    import whisper
    model = whisper.load_model("base")
    result = model.transcribe(temp_path, language="hi")  # or "en"
    transcribed_text = result["text"]
    detected_language = result["language"]
    
    # Step 3: Process as text (reuse Phase 1 pipeline)
    response = await engage_text({
        "message": transcribed_text,
        "language": detected_language,
        "source": "audio"
    })
    
    # Step 4: Add audio-specific metadata
    response["audio_metadata"] = {
        "original_filename": audio_file.filename,
        "transcription": transcribed_text,
        "detected_language": detected_language,
        "transcription_confidence": result.get("confidence", 1.0)
    }
    
    return response
```

### **Audio-Specific Scam Detection**

```python
# Voice deepfake detection (Phase 2 only)
from resemblyzer import preprocess_wav, VoiceEncoder

encoder = VoiceEncoder()

def detect_synthetic_voice(audio_path):
    """Detect if voice is AI-generated"""
    wav = preprocess_wav(audio_path)
    embed = encoder.embed_utterance(wav)
    
    # Compare against known synthetic voice embeddings
    # Return confidence score
    
    return {
        "is_synthetic": False,  # Placeholder
        "confidence": 0.95
    }
```

---

## RESPONSIBLE AI & COMPLIANCE

### **Privacy & Data Protection**

**DPDP Act 2023 Compliance:**
1. **Consent:** User must opt-in to honeypot engagement
2. **Data Minimization:** Store only essential data
3. **Anonymization:** Hash PII (phone numbers, etc.)
4. **Retention:** Delete logs after 30 days
5. **Right to Erasure:** Provide deletion API

```python
import hashlib

def anonymize_phone(phone_number):
    """Hash phone numbers for privacy"""
    return hashlib.sha256(phone_number.encode()).hexdigest()

def schedule_data_deletion(session_id, days=30):
    """Schedule automatic data deletion"""
    deletion_date = datetime.now() + timedelta(days=days)
    # Store in deletion_queue table
    db.execute("""
        INSERT INTO deletion_queue (session_id, deletion_date)
        VALUES (%s, %s)
    """, (session_id, deletion_date))
```

### **Safety Guidelines**

**Agent Behavior Rules:**
1. **No Escalation:** Never threaten or provoke scammer
2. **No Personal Info:** Never share real personal details
3. **No Financial Transactions:** Never actually transfer money
4. **Termination:** End conversation if scammer becomes violent
5. **Legal Compliance:** Ensure honeynet operations are legal

```python
def safety_check(agent_message):
    """Ensure agent response is safe"""
    unsafe_patterns = [
        r'I will kill',
        r'real address',
        r'my actual bank',
        # Add more unsafe patterns
    ]
    
    for pattern in unsafe_patterns:
        if re.search(pattern, agent_message, re.IGNORECASE):
            return False, "Unsafe content detected"
    
    return True, "Safe"
```

### **Bias Mitigation**

**Addressing Potential Biases:**
1. **Language Bias:** Equal performance for Hindi and English
2. **Dialect Bias:** Test on multiple Indian accents
3. **Age Bias:** Personas represent diverse age groups
4. **Regional Bias:** Test on North and South Indian scam patterns

```python
def test_language_fairness():
    """Ensure equal accuracy across languages"""
    hindi_accuracy = evaluate_on_dataset("hindi_test_set")
    english_accuracy = evaluate_on_dataset("english_test_set")
    
    difference = abs(hindi_accuracy - english_accuracy)
    assert difference < 0.05, "Language bias detected"
```

---

## WINNING STRATEGY

### **What Makes This Solution Top 10 Material**

1. **Technical Excellence (40%)**
   - ✅ Production-grade LangGraph architecture
   - ✅ State-of-the-art models (IndicBERT, Llama 3.1)
   - ✅ Robust state management (PostgreSQL + Redis + ChromaDB)
   - ✅ Free tier deployment (cost-effective)

2. **Innovation (30%)**
   - ✅ Multi-turn agentic engagement (beyond simple detection)
   - ✅ Dynamic persona adaptation
   - ✅ Intelligent stalling tactics
   - ✅ Real-time intelligence extraction

3. **India-Specific (20%)**
   - ✅ Hindi + English bilingual support
   - ✅ UPI/IFSC/Indian bank patterns
   - ✅ Local scam tactics knowledge
   - ✅ Cultural context in personas

4. **Execution Quality (10%)**
   - ✅ Clean API design
   - ✅ Comprehensive documentation
   - ✅ Testing framework
   - ✅ Production deployment

### **Competition Day Checklist**

**Before Submission (Feb 4):**
- [ ] API deployed and publicly accessible
- [ ] Health check endpoint working
- [ ] Test with 100+ sample scam messages
- [ ] Verify JSON response format matches requirements
- [ ] Check response latency (<2s average)
- [ ] Ensure Groq API key has remaining credits
- [ ] Database backups configured
- [ ] Monitoring dashboard active
- [ ] Documentation complete
- [ ] Demo video recorded (if required)

**Submission Day (Feb 5):**
- [ ] Submit API endpoint URL
- [ ] Verify endpoint is reachable from external networks
- [ ] Monitor logs for incoming test requests
- [ ] Have fallback plan (backup deployment)
- [ ] Team available for support
- [ ] Response to any judge queries within 2 hours

### **Differentiation from Competitors**

Most participants will likely build:
- Simple rule-based detection (keyword matching only)
- Single-turn response (no multi-turn engagement)
- Basic regex extraction (no NER)
- No state management (stateless API)

**Your Edge:**
- ✅ **Agentic AI** with LangGraph (complex, adaptive)
- ✅ **Multi-turn engagement** (up to 20 turns)
- ✅ **State persistence** (remembers conversation)
- ✅ **Dynamic personas** (believable, adaptive)
- ✅ **Hybrid extraction** (NER + regex + validation)
- ✅ **Production architecture** (scalable, monitored)

---

## PROJECT STRUCTURE

```
scamshield-ai/
├── README.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app
│   ├── config.py                  # Configuration
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints.py           # API routes
│   │   └── schemas.py             # Pydantic models
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── detector.py            # IndicBERT scam detection
│   │   ├── extractor.py           # Intelligence extraction
│   │   └── language.py            # Language detection
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── honeypot.py            # LangGraph agent
│   │   ├── personas.py            # Persona definitions
│   │   ├── prompts.py             # LLM prompts
│   │   └── strategies.py          # Engagement strategies
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── postgres.py            # PostgreSQL connection
│   │   ├── redis_client.py        # Redis connection
│   │   ├── chromadb_client.py     # ChromaDB connection
│   │   └── models.py              # SQLAlchemy models
│   │
│   └── utils/
│       ├── __init__.py
│       ├── preprocessing.py       # Text preprocessing
│       ├── validation.py          # Input validation
│       ├── metrics.py             # Prometheus metrics
│       └── logger.py              # Logging configuration
│
├── tests/
│   ├── __init__.py
│   ├── test_detection.py
│   ├── test_extraction.py
│   ├── test_engagement.py
│   └── test_api.py
│
├── scripts/
│   ├── setup_models.py            # Download ML models
│   ├── init_database.py           # Initialize DB schema
│   └── test_deployment.py         # Deployment smoke tests
│
├── data/
│   ├── test_scam_messages.json    # Test dataset
│   ├── personas.json              # Persona definitions
│   └── scam_patterns.json         # Known scam patterns
│
└── docs/
    ├── API_DOCUMENTATION.md
    ├── DEPLOYMENT_GUIDE.md
    └── TESTING_GUIDE.md
```

---

## IMPLEMENTATION TIMELINE

### **Week 1 (Jan 26 - Feb 1): Core Development**

**Day 1-2: Project Setup**
- Initialize repository
- Setup virtual environment
- Install dependencies
- Configure PostgreSQL, Redis, ChromaDB
- Obtain Groq API key

**Day 3-4: Detection Module**
- Implement IndicBERT integration
- Build language detection
- Create keyword matching
- Test on sample messages

**Day 5-6: Agentic Module**
- Build LangGraph workflow
- Integrate Groq Llama 3.1
- Implement persona system
- Test engagement loop

**Day 7: Extraction Module**
- Implement spaCy NER
- Build regex patterns
- Create validation logic
- Test on sample extractions

### **Week 2 (Feb 2 - Feb 5): Testing & Deployment**

**Day 8: Integration**
- Connect all modules
- Build FastAPI endpoints
- Implement database operations
- End-to-end testing

**Day 9: Testing**
- Unit tests (80%+ coverage)
- Integration tests
- Load testing (100 req/min)
- Fix bugs

**Day 10: Deployment**
- Deploy to Render/Railway
- Configure environment variables
- Setup monitoring
- Test production endpoint

**Day 11: Buffer & Submission**
- Final testing
- Documentation review
- Submit API endpoint
- Monitor for test requests

---

## SUCCESS METRICS

### **Minimum Viable Product (MVP) Criteria**

**Must Have:**
- [x] Scam detection with >85% accuracy
- [x] Multi-turn engagement (at least 10 turns)
- [x] Extract at least 1 UPI ID or bank account
- [x] API response time <3s
- [x] Handle Hindi and English
- [x] Structured JSON output

**Should Have:**
- [x] >90% detection accuracy
- [x] 15+ turn average engagement
- [x] Extract 2+ intelligence types per conversation
- [x] API response time <2s
- [x] State persistence across sessions
- [x] Monitoring and metrics

**Nice to Have:**
- [ ] >95% detection accuracy
- [ ] 20 turn max engagement
- [ ] Extract all 5 intelligence types
- [ ] API response time <1s
- [ ] Advanced persona adaptation
- [ ] Voice deepfake detection (Phase 2)

---

## RISK MITIGATION

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Groq API rate limits** | High | High | Implement retry logic, use backoff, cache responses |
| **Model loading time** | Medium | Medium | Load models at startup, not per request |
| **Database connection loss** | Low | High | Connection pooling, auto-reconnect, fallback to local storage |
| **Competition API changes** | Medium | High | Flexible schema design, comprehensive testing |
| **Deployment downtime** | Low | Critical | Multiple hosting options, health checks, auto-restart |
| **Hindi detection accuracy** | Medium | Medium | Extensive testing, fallback to English, hybrid approach |

---

## CONCLUSION

This specification provides a **complete, production-ready blueprint** for building a winning Agentic Honeypot System for the India AI Impact Buildathon 2026.

**Key Strengths:**
1. ✅ **100% Free Tier** - No cost barriers
2. ✅ **Phased Approach** - Text first, audio later
3. ✅ **Production Architecture** - Scalable, monitored, robust
4. ✅ **India-Specific** - Hindi support, local scam patterns
5. ✅ **Competition-Ready** - API-first, JSON outputs
6. ✅ **Technically Superior** - LangGraph, state management, multi-turn
7. ✅ **Well-Documented** - Clear implementation path

**Expected Ranking:** TOP 10 from 40,000 participants

**Next Steps:**
1. Begin implementation following project structure
2. Test continuously against test dataset
3. Deploy early to identify issues
4. Iterate based on testing feedback
5. Submit before deadline with confidence

**Team Focus:**
- Speed of execution (10 days remaining)
- Quality over features (MVP first)
- Testing, testing, testing
- Documentation for judges
- Monitoring for competition day

---

## APPENDIX

### **A. Sample API Requests/Responses**

See API ENDPOINT SPECIFICATION section above.

### **B. Groq API Key Setup**

1. Visit: https://console.groq.com/
2. Sign up with email
3. Navigate to API Keys section
4. Generate new API key
5. Free tier: 30 requests/minute, 6000/day

### **C. Supabase PostgreSQL Setup**

1. Visit: https://supabase.com/
2. Create account
3. New project → Select free tier
4. Copy connection string
5. Use in DATABASE_URL environment variable

### **D. Redis Cloud Setup**

1. Visit: https://redis.com/try-free/
2. Create account
3. New database → Free 30MB
4. Copy connection details
5. Use in REDIS_URL environment variable

### **E. Testing Commands**

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_detection.py::test_hindi_scam_detection

# Test API locally
curl -X POST http://localhost:8000/honeypot/engage \
  -H "Content-Type: application/json" \
  -d '{"message": "You won 10 lakh rupees!"}'

# Load test
locust -f tests/load_test.py --host http://localhost:8000
```

### **F. Deployment Commands**

```bash
# Build Docker image
docker build -t scamshield-ai .

# Run locally
docker-compose up

# Deploy to Render
git push render main

# Check logs
render logs --tail 100
```

---

**Document Version:** 1.0  
**Last Updated:** January 26, 2026  
**Status:** Ready for Implementation  
**Approved By:** Shivam Bhuva (Team Lead)

**For Questions/Support:**
- GitHub Issues: [Your Repo]
- Email: shivambhuva8866@gmail.com
- Team Channel: [Your Communication Channel]

---

**END OF DOCUMENT**
