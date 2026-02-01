# Product Requirements Document: ScamShield AI
## Agentic Honeypot System for Scam Detection & Intelligence Extraction

**Version:** 1.0  
**Date:** January 26, 2026  
**Owner:** Product & Architecture Team  
**Target Competition:** India AI Impact Buildathon 2026 - Challenge 2  
**Submission Deadline:** February 5, 2026

---

## EXECUTIVE SUMMARY

ScamShield AI is an autonomous AI-powered honeypot system designed to detect scam messages, actively engage scammers using believable personas, and extract actionable intelligence including bank accounts, UPI IDs, and phishing links. Built exclusively with free-tier technologies, the system targets 90%+ detection accuracy and multi-turn conversational engagement in English and Hindi.

**Target Outcome:** TOP 10 ranking from 40,000 participants through technical superiority and production-grade implementation.

---

## PROBLEM STATEMENT

### Market Context
- 500,000+ scam calls/messages daily in India (TRAI 2025)
- ₹60+ crore daily losses to fraud
- 47% of Indians affected by or know victims of scam fraud
- Predominant scams: UPI fraud, fake loans, police/bank impersonation

### Solution Gap
Existing solutions focus on passive detection. ScamShield AI introduces active engagement to extract intelligence while scammers remain unaware they're interacting with an AI system.

---

## PRODUCT VISION

**Mission:** Proactively combat digital fraud through autonomous AI agents that gather actionable intelligence from scammers.

**Core Differentiators:**
1. **Active Engagement:** Multi-turn conversations (up to 20 turns) vs. single-response detection
2. **Intelligence Extraction:** Structured extraction of UPI IDs, bank accounts, IFSC codes, phone numbers, phishing links
3. **Persona Simulation:** Dynamic, believable personas (elderly, eager victim, confused user)
4. **Bilingual:** Native English + Hindi support with Hinglish handling
5. **Cost-Effective:** 100% free-tier implementation

---

## TARGET USERS

**Primary:** Competition judges evaluating via Mock Scammer API integration

**Secondary (Future):**
- Financial institutions (banks, payment providers)
- Law enforcement agencies
- Consumer protection organizations
- Telecom operators

---

## PRODUCT REQUIREMENTS

### Phase 1: Text-Based Honeypot (Feb 5, 2026)

#### FR-1: Scam Detection
- **Requirement:** Classify incoming messages as scam/not-scam with confidence scores
- **Accuracy Target:** ≥90% on test dataset
- **Languages:** English, Hindi, Hinglish (code-mixed)
- **Confidence Threshold:** 0.7 (trigger engagement)

#### FR-2: Agentic Engagement
- **Requirement:** Conduct multi-turn conversations to extract intelligence
- **Turn Range:** 1-20 turns per conversation
- **Persona Types:** Elderly (60+), Eager Victim (middle-aged), Confused User (young)
- **Strategy:** Progressive engagement (interest → confusion → probing)

#### FR-3: Intelligence Extraction
- **Requirement:** Extract and validate financial/contact information
- **Target Types:**
  - UPI IDs (e.g., user@paytm)
  - Bank Account Numbers (9-18 digits)
  - IFSC Codes (11 characters, format: XXXX0XXXXXX)
  - Phone Numbers (Indian mobile: +91XXXXXXXXXX or 10-digit)
  - Phishing Links (http/https URLs)
- **Precision Target:** ≥85%
- **Recall Target:** ≥80%

#### FR-4: API Integration
- **Requirement:** REST API endpoint for competition testing
- **Response Time:** <2 seconds per request
- **Format:** Structured JSON output
- **Session Management:** Stateful conversation tracking

#### FR-5: State Persistence
- **Requirement:** Maintain conversation context across turns
- **Storage:** PostgreSQL (logs), Redis (active sessions), ChromaDB (embeddings)
- **Session Expiry:** 1 hour for active sessions

### Phase 2: Audio Extension (Post-Competition)
- Whisper-based audio transcription
- Voice deepfake detection
- Phone call integration

---

## NON-FUNCTIONAL REQUIREMENTS

### Performance
- API Latency: <2s (p95), <1s (p50)
- Throughput: 100 requests/minute
- Concurrent Sessions: 50+

### Reliability
- Uptime: 99%+ during competition testing window
- Error Rate: <1%
- Graceful degradation on LLM rate limits

### Scalability
- Horizontal scaling via containerization
- Stateless API design (state in external stores)
- Database connection pooling

### Security
- No storage of real user PII
- Anonymization of extracted phone numbers
- Safe engagement (no provocation/threats)
- Data retention: 30 days max

### Compliance
- DPDP Act 2023 adherence
- Ethical AI guidelines (no harm principle)
- Transparent data handling

---

## SUCCESS METRICS

### Competition Metrics
1. **Detection Accuracy:** >90% (true positive rate)
2. **False Positive Rate:** <5%
3. **Engagement Quality:** >10 turns average
4. **Extraction Precision:** >85%
5. **Response Time:** <2s per request
6. **System Uptime:** 99%+ during testing

### Technical Metrics
- Code Coverage: >80%
- Documentation Completeness: 100%
- API Compliance: 100% (all endpoints functional)
- Error Handling: All edge cases covered

---

## CONSTRAINTS & ASSUMPTIONS

### Constraints
- **Cost:** $0 operational cost (free tier only)
- **Time:** 10 days to production deployment
- **Languages:** English + Hindi only (no Gujarati/Tamil/etc.)
- **Modality:** Text only in Phase 1

### Assumptions
- Competition provides functional Mock Scammer API
- Groq API maintains 30 req/min free tier
- Test dataset representative of real scam messages
- Judges evaluate on detection accuracy, engagement quality, extraction precision

---

## DEPENDENCIES

### External Services
- Groq Cloud API (LLM)
- Supabase (PostgreSQL)
- Redis Cloud (cache)
- Hugging Face (model downloads)

### Critical Risks
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Groq rate limits | High | Retry logic, exponential backoff, request queueing |
| Model loading time | Medium | Load at startup, cache in memory |
| Database connectivity | High | Connection pooling, auto-reconnect, local fallback |
| Competition API changes | Medium | Flexible schema design, extensive pre-testing |

---

## OUT OF SCOPE (Phase 1)

- Audio/voice call handling (Phase 2)
- Real-time phone system integration
- Automated police reporting
- Gujarati or other regional languages
- Web scraping of phishing sites
- Blockchain/cryptocurrency scam detection (unless text-based)

---

## ACCEPTANCE CRITERIA

**Phase 1 Launch Readiness:**
1. ✅ API endpoint deployed and publicly accessible
2. ✅ Health check endpoint returns 200 OK
3. ✅ Detection accuracy ≥85% on 100+ test cases
4. ✅ Extraction precision ≥80% on validation dataset
5. ✅ Response time <2s for 95% of requests
6. ✅ Multi-turn engagement averages >8 turns
7. ✅ Hindi and English both functional
8. ✅ JSON output matches specified schema
9. ✅ Monitoring dashboard active
10. ✅ Documentation complete (API docs, deployment guide)

---

## ROADMAP

### Week 1 (Jan 26 - Feb 1): Core Development
- Days 1-2: Project setup, dependencies, database initialization
- Days 3-4: Detection module (IndicBERT, language detection)
- Days 5-6: Agentic module (LangGraph, Groq integration, personas)
- Day 7: Extraction module (spaCy NER, regex patterns)

### Week 2 (Feb 2 - Feb 5): Testing & Deployment
- Day 8: Integration and end-to-end testing
- Day 9: Unit/integration/load testing
- Day 10: Production deployment to Render/Railway
- Day 11: Final testing and competition submission

---

## APPENDIX

### Technology Stack
- **Detection:** IndicBERT (ai4bharat/indic-bert), langdetect
- **LLM:** Groq Llama 3.1 70B (free tier)
- **Orchestration:** LangGraph + LangChain
- **Extraction:** spaCy (en_core_web_sm), regex patterns
- **API:** FastAPI + Uvicorn + Pydantic
- **Storage:** PostgreSQL, Redis, ChromaDB (all local/free)
- **Deployment:** Docker, Render/Railway

### Key Performance Indicators
- Scam detection calls: target 1000+ during competition testing
- Average engagement turns: target 12
- Intelligence pieces extracted per conversation: target 2.5
- System uptime during judging window: 99.9%

---

**Document Status:** Approved for Implementation  
**Next Steps:** Proceed to FRD.md for detailed functional specifications
