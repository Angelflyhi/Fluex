FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create model directory
RUN mkdir -p model

EXPOSE 8000

# Railway injects $PORT — use it
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
