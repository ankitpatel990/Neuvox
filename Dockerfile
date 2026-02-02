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

# Hugging Face Spaces requires port 7860
EXPOSE 7860

# Run the application on port 7860 (required by Hugging Face Spaces)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
