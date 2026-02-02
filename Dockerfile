# ScamShield AI - Hugging Face Spaces Docker Image
# Optimized for Hugging Face deployment

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq5 \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies with increased timeout
RUN pip install --no-cache-dir --timeout 1000 -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY app/ ./app/
COPY scripts/ ./scripts/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Default configuration (non-sensitive values)
# Sensitive values (GROQ_API_KEY, API_KEY, etc.) should be set as HF Secrets
ENV DEBUG=false
ENV LOG_LEVEL=INFO
ENV GROQ_MODEL=llama-3.3-70b-versatile
ENV GROQ_MAX_TOKENS=500
ENV GROQ_TEMPERATURE=0.7
ENV CHROMADB_PATH=/app/chroma_data
ENV API_HOST=0.0.0.0
ENV API_PORT=7860
ENV MAX_MESSAGE_LENGTH=5000
ENV MAX_TURNS=20
ENV SESSION_TTL=3600
ENV SCAM_THRESHOLD=0.7
ENV RATE_LIMIT_PER_MINUTE=100
ENV RATE_LIMIT_PER_HOUR=1000
ENV INDICBERT_MODEL=ai4bharat/indic-bert
ENV SPACY_MODEL=en_core_web_sm
ENV EMBEDDING_MODEL=all-MiniLM-L6-v2
ENV GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
ENV GUVI_CALLBACK_ENABLED=true

# Hugging Face Spaces requires port 7860
EXPOSE 7860

# Run the application on port 7860 (required by Hugging Face Spaces)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
