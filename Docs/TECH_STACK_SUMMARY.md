# ScamShield AI - Tech Stack Summary & Changes
## Quick Reference for Implementation

**Last Updated:** January 26, 2026  
**Target:** TOP 10 from 40,000 participants

---

## KEY CHANGES FROM ORIGINAL DOCS

### ❌ **REMOVED**
1. **Gujarati Language Support** → Focus on English + Hindi only (better accuracy)
2. **Paid APIs** → All GPT-4, Claude paid tiers removed
3. **Audio (Phase 1)** → Moved to Phase 2 (after text is stable)
4. **Wav2Vec2 for features** → Redundant with Whisper (Phase 2)
5. **Sentiment Analysis** → Covered by IndicBERT
6. **Voice fingerprinting** → Phase 2 only
7. **Police reporting** → Out of scope for competition
8. **TomTom API** → Not needed for honeypot

### ✅ **ADDED**
1. **Groq Llama 3.1 70B** → Free LLM with 30 req/min (replaces unspecified LLM)
2. **ChromaDB** → Free vector database for conversation embeddings
3. **PostgreSQL** → Conversation logs and scammer profiles
4. **Redis** → Session state management
5. **Pydantic Schemas** → Structured JSON validation
6. **LangSmith** → Agent observability and debugging
7. **Mock Scammer API Integration** → Competition requirement
8. **Prometheus Metrics** → Performance monitoring
9. **Docker Deployment** → Containerization for easy hosting
10. **Testing Framework** → pytest with 80%+ coverage target

### ⚠️ **CLARIFIED**
1. **API Endpoint Design** → Detailed request/response schemas
2. **LangGraph Implementation** → Complete ReAct agent code structure
3. **Deployment Architecture** → Specific free tier services
4. **Phase 1 vs Phase 2** → Clear separation of text and audio
5. **Intelligence Extraction** → Specific regex patterns and NER approach
6. **Persona Strategy** → Turn-by-turn engagement tactics
7. **Hindi Support** → IndicBERT + Groq with Hindi prompts

---

## FINAL TECH STACK (100% FREE)

### **Phase 1: Text-Based (Feb 5 Submission)**

```
┌─────────────────────────────────────────────┐
│           DETECTION LAYER                   │
├─────────────────────────────────────────────┤
│ • IndicBERT (ai4bharat/indic-bert)         │
│ • Keyword matching (UPI, OTP, bank)        │
│ • Language detection (langdetect)          │
│ • Confidence scoring                       │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│           AGENTIC LAYER                     │
├─────────────────────────────────────────────┤
│ • LangGraph (ReAct orchestration)          │
│ • Groq Llama 3.1 70B (FREE API)            │
│ • LangChain (prompts, chains)              │
│ • Dynamic personas (elderly, eager, etc.)  │
│ • Multi-turn engagement (up to 20 turns)   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│         EXTRACTION LAYER                    │
├─────────────────────────────────────────────┤
│ • spaCy NER (en_core_web_sm)               │
│ • Regex patterns (UPI, bank, IFSC, phone)  │
│ • Confidence scoring                       │
│ • Format validation                        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│         STORAGE LAYER                       │
├─────────────────────────────────────────────┤
│ • ChromaDB (conversation embeddings)       │
│ • PostgreSQL (logs, profiles)              │
│ • Redis (session state)                    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│            API LAYER                        │
├─────────────────────────────────────────────┤
│ • FastAPI (REST endpoints)                 │
│ • Pydantic (validation)                    │
│ • Uvicorn (ASGI server)                    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│         DEPLOYMENT LAYER                    │
├─────────────────────────────────────────────┤
│ • Docker (containerization)                │
│ • Render/Railway (hosting)                 │
│ • Supabase (PostgreSQL)                    │
│ • Redis Cloud (cache)                      │
└─────────────────────────────────────────────┘
```

### **Phase 2: Audio Extension (Post-Text)**

```
Additional Components:
├─ Whisper (ASR)
├─ Librosa (audio preprocessing)
├─ PyAudio (live capture)
└─ ECAPA-TDNN (deepfake detection)
```

---

## DEPENDENCIES (requirements.txt)

### **Core (Phase 1 - Must Have)**
```python
# AI/ML Models
torch==2.1.0
transformers==4.35.0
sentence-transformers==2.2.2
spacy==3.7.2

# Agentic Framework
langchain==0.1.0
langgraph==0.0.20
langchain-groq==0.0.1
langsmith==0.0.70

# API Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0

# Databases
chromadb==0.4.18
psycopg2-binary==2.9.9
redis==5.0.1
sqlalchemy==2.0.23

# NLP Utils
langdetect==1.0.9
nltk==3.8.1

# Monitoring
prometheus-client==0.19.0

# Utils
python-dotenv==1.0.0
requests==2.31.0
numpy==1.24.3
```

### **Audio (Phase 2 - Add Later)**
```python
openai-whisper==20231117
torchaudio==2.1.0
librosa==0.10.1
soundfile==0.12.1
pyaudio==0.2.14
```

---

## FREE TIER SERVICES

| Service | Purpose | Free Limits | Signup URL |
|---------|---------|-------------|------------|
| **Groq Cloud** | LLM API | 30 req/min, 6000/day | https://console.groq.com/ |
| **Render** | API Hosting | 750 hours/month | https://render.com/ |
| **Supabase** | PostgreSQL | 500MB, 2GB transfer | https://supabase.com/ |
| **Redis Cloud** | Cache | 30MB, 30 connections | https://redis.com/try-free/ |
| **Hugging Face** | Model Storage | Unlimited downloads | https://huggingface.co/ |

---

## API ENDPOINTS (Competition Submission)

### **Primary Endpoint**
```
POST /honeypot/engage

Request:
{
  "message": "You won 10 lakh! Send OTP.",
  "session_id": "optional-123",
  "language": "auto"
}

Response:
{
  "status": "success",
  "scam_detected": true,
  "confidence": 0.92,
  "language_detected": "hindi",
  "engagement": {
    "agent_response": "वाह! कैसे claim करूं?",
    "turn_count": 1
  },
  "extracted_intelligence": {
    "upi_ids": [],
    "bank_accounts": [],
    "phishing_links": []
  },
  "conversation_history": [...]
}
```

### **Health Check**
```
GET /health
Response: {"status": "healthy"}
```

---

## IMPLEMENTATION PRIORITY

### **Week 1: Core Build**
```
Day 1-2: Setup (repo, dependencies, databases)
Day 3-4: Detection (IndicBERT, keywords)
Day 5-6: Agent (LangGraph, Groq integration)
Day 7: Extraction (spaCy, regex)
```

### **Week 2: Deploy & Test**
```
Day 8: Integration (FastAPI, end-to-end)
Day 9: Testing (unit, integration, load)
Day 10: Deployment (Docker, Render)
Day 11: Submit & Monitor
```

---

## COMPETITION WINNING FACTORS

### **Why This Solution Wins**

1. **Technical Sophistication**
   - ✅ Multi-turn agentic AI (not just detection)
   - ✅ State persistence (remembers context)
   - ✅ Dynamic personas (adaptive behavior)
   - ✅ Production architecture

2. **India-Specific**
   - ✅ Hindi + English bilingual
   - ✅ UPI/IFSC/Indian patterns
   - ✅ Local scam tactics knowledge

3. **Execution Quality**
   - ✅ Clean API design
   - ✅ Comprehensive testing
   - ✅ Free tier deployment
   - ✅ Monitoring & metrics

4. **Innovation**
   - ✅ ReAct loop engagement
   - ✅ Intelligent stalling
   - ✅ Real-time extraction
   - ✅ Multi-factor validation

### **Competitive Edge**

Most competitors will build:
- ❌ Simple keyword detection
- ❌ Single response (no engagement)
- ❌ Basic regex extraction
- ❌ No state management

You will build:
- ✅ Hybrid ML detection (IndicBERT + rules)
- ✅ 20-turn conversations
- ✅ NER + regex + validation
- ✅ Full state persistence

**Expected Advantage:** 3-5x more sophisticated

---

## QUICK START

### **1. Clone & Setup**
```bash
git clone https://github.com/your-repo/scamshield-ai
cd scamshield-ai
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### **2. Configure Environment**
```bash
cp .env.example .env
# Edit .env:
# GROQ_API_KEY=gsk_your_key_here
# POSTGRES_URL=postgresql://...
# REDIS_URL=redis://...
```

### **3. Run Locally**
```bash
python scripts/init_database.py
uvicorn app.main:app --reload
```

### **4. Test**
```bash
curl -X POST http://localhost:8000/honeypot/engage \
  -H "Content-Type: application/json" \
  -d '{"message": "You won 10 lakh rupees!"}'
```

### **5. Deploy**
```bash
docker build -t scamshield-ai .
# Push to Render/Railway
```

---

## METRICS TO TRACK

### **Competition Judging (Predicted)**
1. **Detection Accuracy:** >90% target
2. **Engagement Quality:** >10 turns average
3. **Extraction Precision:** >85% correct
4. **Response Time:** <2s per request
5. **System Robustness:** 99%+ uptime

### **Monitor During Testing**
```python
# Key metrics
- scam_detection_total (by language, result)
- intelligence_extracted_total (by type)
- response_time_seconds (histogram)
- active_honeypot_sessions (gauge)
- error_rate (counter)
```

---

## RISK MANAGEMENT

| Risk | Mitigation |
|------|------------|
| **Groq rate limits** | Retry logic, backoff, caching |
| **Model load time** | Load at startup, not per request |
| **DB connection loss** | Connection pooling, auto-reconnect |
| **API changes** | Flexible schema, comprehensive tests |
| **Deployment downtime** | Multiple hosting options, health checks |

---

## SUCCESS CHECKLIST

### **Pre-Submission (Feb 4)**
- [ ] API deployed and public
- [ ] Tested with 100+ scam messages
- [ ] Response time <2s average
- [ ] Detection accuracy >85%
- [ ] Extraction working for all 5 types
- [ ] Hindi and English both working
- [ ] Monitoring active
- [ ] Documentation complete

### **Submission Day (Feb 5)**
- [ ] Submit API endpoint URL
- [ ] Verify external accessibility
- [ ] Monitor logs for test requests
- [ ] Team on standby
- [ ] Backup deployment ready

---

## LANGUAGES SUPPORTED

### **Phase 1**
- ✅ **English:** Full support (IndicBERT, Groq, spaCy)
- ✅ **Hindi:** Full support (IndicBERT, Groq, custom patterns)
- ⚠️ **Hinglish (Code-mixed):** Automatic handling by IndicBERT

### **Phase 2 (Audio)**
- ✅ **English Audio:** Whisper transcription → text pipeline
- ✅ **Hindi Audio:** Whisper transcription → text pipeline

### **NOT Supported (Removed for Focus)**
- ❌ Gujarati
- ❌ Tamil, Telugu, Malayalam (not required for this competition)

---

## CONTACT & SUPPORT

**Team Lead:** Shivam Bhuva (@shivambhuva8866)  
**Email:** shivambhuva8866@gmail.com  
**Submission Deadline:** Feb 5, 2026, 11:59 PM

**Documentation:**
- Full Spec: `Docs/FINAL_IMPLEMENTATION_SPEC.md`
- This Summary: `Docs/TECH_STACK_SUMMARY.md`
- Original Docs: `Docs/Doc.md`, `Docs/final_api_endpoint_build.md`

---

## FINAL NOTES

### **Priority Focus**
1. **Get text-based working first** (Phase 1)
2. **Test extensively** (100+ test cases)
3. **Deploy early** (by Feb 3)
4. **Monitor continuously** (competition day)

### **Key Differentiators**
- 🏆 Multi-turn agentic engagement (not single response)
- 🏆 State-aware conversations (not stateless)
- 🏆 Production architecture (not proof-of-concept)
- 🏆 Free tier deployment (cost-effective innovation)

### **Expected Outcome**
**Ranking:** TOP 10 from 40,000 participants  
**Success Rate:** 85-95% based on technical superiority

---

**Ready to implement? Start with:** `Docs/FINAL_IMPLEMENTATION_SPEC.md`

**Questions?** Review full spec or contact team lead.

---

**END OF SUMMARY**
