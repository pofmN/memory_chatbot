FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make sure MCP server is executable
RUN chmod +x mcp/server.py

# Create .env file with Docker-specific settings
RUN echo "DB_HOST=postgres" > .env && \
    echo "DB_PORT=5432" >> .env && \
    echo "DB_NAME=chatbot_db" >> .env && \
    echo "DB_USER=chatbot_user" >> .env && \
    echo "DB_PASSWORD=chatbot_password" >> .env

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit (which will spawn MCP server as needed)
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true"]