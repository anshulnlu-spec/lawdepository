# Use an official slim Python base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Install system deps required for some Python packages (psycopg2, lxml)
# and keep minimal footprint
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc \
      libpq-dev \
      curl \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt .

# Upgrade pip and install python deps; --no-cache-dir to save space
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy rest of the application
COPY . .

# Create a non-root user and set ownership of files
RUN useradd --create-home appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the port (informational)
EXPOSE 8080

# Use exec form and expand $PORT at runtime so Cloud Run's PORT is respected.
# The `exec` ensures signals are properly forwarded to uvicorn.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
