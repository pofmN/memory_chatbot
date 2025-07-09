FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    curl \
    libdbus-1-dev \
    libglib2.0-dev \
    libnotify-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make sure MCP server is executable (only if it exists)
RUN if [ -f mcp/server.py ]; then chmod +x mcp/server.py; fi

# Create Docker-specific .env file (don't overwrite existing one)
RUN if [ ! -f .env ]; then \
    echo "DB_HOST=postgres" > .env && \
    echo "DB_PORT=5432" >> .env && \
    echo "DB_NAME=chatbot_db" >> .env && \
    echo "DB_USER=chatbot_user" >> .env && \
    echo "DB_PASSWORD=chatbot_password" >> .env; \
fi

# Create logs directory
RUN mkdir -p logs

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the correct app file
CMD ["streamlit", "run", "app_dev.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true"]