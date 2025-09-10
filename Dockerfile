# Use official lightweight Python base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for psycopg2/Postgres)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Environment variables (overridable in docker-compose.yml)
ENV PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:///shame.db

# Run the bot
CMD ["python", "bot.py"]
