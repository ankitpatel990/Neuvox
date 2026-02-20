---
title: ScamShield AI
emoji: 🛡️
colorFrom: blue
colorTo: red
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# ScamShield AI

**Agentic Honeypot System for Scam Detection & Intelligence Extraction**

Version: 1.0.0

## Overview

ScamShield AI is an intelligent honeypot system that detects scam messages, engages scammers through AI-driven personas, and extracts financial intelligence from conversations. The system supports English, Hindi, and Hinglish (code-mixed) messages.

## Features

- **Multi-language Scam Detection**: Detects scams in English, Hindi, and Hinglish using IndicBERT
- **Agentic Engagement**: Uses LangGraph and Groq LLM for multi-turn conversations with scammers
- **Intelligence Extraction**: Extracts UPI IDs, bank accounts, IFSC codes, phone numbers, and phishing links
- **Dynamic Personas**: Deploys believable personas (elderly, eager, confused) to prolong engagement
- **Session Management**: Persists conversation state using Redis with automatic TTL
- **Production Ready**: Full REST API with FastAPI, Docker deployment, and comprehensive testing

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/yourorg/scamshield-ai.git
cd scamshield-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration:
# - GROQ_API_KEY (required for LLM)
# - POSTGRES_URL (optional, for persistence)
# - REDIS_URL (optional, for session state)
```

### 3. Run the API

```bash
# Development mode
uvicorn app.main:app --reload

# Or run directly
python -m app.main
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Test scam detection
curl -X POST http://localhost:8000/api/v1/honeypot/engage \
  -H "Content-Type: application/json" \
  -d '{"message": "You won 10 lakh rupees! Send OTP now!"}'
```

## Project Structure

```
scamshield-ai/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── api/
│   │   ├── endpoints.py     # API routes
│   │   └── schemas.py       # Pydantic schemas
│   ├── models/
│   │   ├── detector.py      # Scam detection (IndicBERT)
│   │   ├── extractor.py     # Intelligence extraction
│   │   └── language.py      # Language detection
│   ├── agent/
│   │   ├── honeypot.py      # LangGraph agent
│   │   ├── personas.py      # Persona definitions
│   │   ├── prompts.py       # Prompt templates
│   │   └── strategies.py    # Engagement strategies
│   ├── database/
│   │   ├── postgres.py      # PostgreSQL client
│   │   ├── redis_client.py  # Redis client
│   │   ├── chromadb_client.py
│   │   └── models.py        # ORM models
│   └── utils/
│       ├── preprocessing.py  # Text preprocessing
│       ├── validation.py     # Input validation
│       ├── metrics.py        # Prometheus metrics
│       └── logger.py         # Logging configuration
├── tests/
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   ├── performance/          # Load tests
│   └── conftest.py           # Pytest fixtures
├── scripts/
│   ├── setup_models.py       # Download ML models
│   ├── init_database.py      # Initialize database
│   └── test_deployment.py    # Deployment tests
├── data/                     # Datasets (gitignored)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── pyproject.toml
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/honeypot/engage` | Primary scam detection and engagement |
| GET | `/api/v1/honeypot/session/{id}` | Retrieve conversation history |
| GET | `/api/v1/health` | Service health check |
| POST | `/api/v1/honeypot/batch` | Batch message processing |

See [API_CONTRACT.md](API_CONTRACT.md) for full API documentation.

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build standalone
docker build -t scamshield-ai .
docker run -p 8000:8000 scamshield-ai
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
```

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq LLM API key | Required |
| `GROQ_MODEL` | Groq model name | llama-3.1-70b-versatile |
| `POSTGRES_URL` | PostgreSQL connection URL | Optional |
| `REDIS_URL` | Redis connection URL | Optional |
| `SCAM_THRESHOLD` | Scam detection threshold | 0.7 |
| `MAX_TURNS` | Maximum conversation turns | 20 |
| `SESSION_TTL` | Session expiry (seconds) | 3600 |

## Tech Stack

- **API Framework**: FastAPI + Uvicorn
- **ML Models**: IndicBERT, spaCy, Sentence Transformers
- **Agentic Framework**: LangChain + LangGraph + Groq
- **Databases**: PostgreSQL, Redis, ChromaDB
- **Deployment**: Docker, Render/Railway

## Approach

### How We Detect Scams

Our system uses a **hybrid detection approach** combining multiple techniques:

1. **IndicBERT Transformer Model**: A fine-tuned BERT model optimized for Indian languages (English, Hindi, Hinglish) provides semantic classification of messages. When fine-tuned, it contributes 60% to the final confidence score.

2. **Keyword Pattern Matching**: A comprehensive rule-based system matches against 100+ scam indicators across English, Hindi, and romanized Hindi (Hinglish). Categories include:
   - Prize/lottery scams
   - Authority impersonation (police, bank officials)
   - Financial urgency (blocked accounts, KYC updates)
   - OTP/credential harvesting

3. **Regex Pattern Detection**: Complex patterns identify specific scam structures like money amounts, OTP requests, arrest threats, and suspicious phone number formats.

The final detection score is a weighted combination, with calibrated confidence thresholds ensuring >90% accuracy with <5% false positive rate.

### How We Extract Intelligence

Intelligence extraction uses **regex patterns with validation** to achieve high precision:

| Entity Type | Precision Target | Technique |
|-------------|------------------|-----------|
| UPI IDs | >90% | Pattern matching with known provider validation |
| Bank Accounts | >85% | 9-18 digit detection with sequential/repeating filter |
| IFSC Codes | >95% | Strict XXXX0XXXXXX format validation |
| Phone Numbers | >90% | Indian mobile format with multiple normalization |
| Phishing Links | >95% | URL parsing with suspicious domain/pattern detection |
| Email Addresses | >90% | Standard email regex with UPI deduplication |
| Case/Order/Policy IDs | >85% | Context-aware reference number extraction |

Additional NER via spaCy enhances extraction for CARDINAL and MONEY entities.

### How We Maintain Engagement

The honeypot uses a **LangGraph-based agentic workflow** with three stages:

1. **Plan**: Select engagement strategy based on turn count:
   - Turns 1-5: `build_trust` (establish rapport, appear cooperative)
   - Turns 6-12: `express_confusion` (stall, request clarification)
   - Turns 13-20: `probe_details` (actively extract intelligence)

2. **Generate**: Use Groq LLM (Llama 3.1) with persona-specific prompts:
   - **Elderly persona**: Slower to understand, asks for help
   - **Eager persona**: Willing but confused about process
   - **Confused persona**: Requests repeated clarification

3. **Extract**: Continuously extract intelligence from conversation, avoiding redundant questions by tracking what's already obtained.

The system targets **10+ conversation turns** to maximize scammer time waste and intelligence extraction while maintaining believable human responses.

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Support

For issues and questions, please open a GitHub issue.
