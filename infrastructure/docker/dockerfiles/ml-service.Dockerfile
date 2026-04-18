FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install torch CPU-only 
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copy requirements (without torch) and install remaining dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ML service code
COPY . .

# Create non-root user
RUN useradd -m -s /bin/bash mluser && chown -R mluser:mluser /app
USER mluser

# Expose port for Flask
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run Flask
CMD ["python", "api/main.py"]