# Dockerfile — minimal, reproducible, expands $PORT via entrypoint.sh
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps required for some Python packages (psycopg2, build tools)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure entrypoint script is executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Use entrypoint that expands $PORT
ENTRYPOINT ["/entrypoint.sh"]
