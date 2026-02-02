# ScamShield AI - Hugging Face Spaces Docker Image
# Optimized for Hugging Face deployment

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

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

# Hugging Face Spaces requires port 7860
EXPOSE 7860

# Health check (using port 7860)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/api/v1/health || exit 1

# Run the application on port 7860 (required by Hugging Face Spaces)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
