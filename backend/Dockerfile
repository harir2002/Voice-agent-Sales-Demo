# ==============================================================================
# VOICE AGENT BACKEND - Dockerfile
# ==============================================================================

# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8000

# Install system dependencies (needed for audioop and other packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir httpx  # For TestClient

# Copy project files
COPY . .

# Initialize knowledge base (Optional: can also be done via a separate job)
# RUN python init_knowledge_base.py

# Expose the API port
EXPOSE 8000

# Start the application using uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}"]
