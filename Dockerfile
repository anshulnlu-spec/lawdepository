# Use official slim Python runtime
FROM python:3.11-slim

# Prevents Python from writing .pyc files to disk and buffers output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

# Install system deps required by psycopg2 and similar packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Copy dependency definitions first for better caching
COPY requirements.txt .

# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy app sources
COPY . .

# Optional: expose the default port (Cloud Run ignores this, but it helps locally)
EXPOSE 8080

# Start command: use shell form so ${PORT} expands at runtime
CMD ["bash", "-lc", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
