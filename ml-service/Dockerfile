FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY api/ ./api/
COPY core/ ./core/
COPY config/ ./config/

EXPOSE 9000

# Run server
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "9000"]
