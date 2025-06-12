# Memory Chat with MCP Integration

A sophisticated chatbot application with persistent memory and web search capabilities, built using LangGraph, Streamlit, and Model Context Protocol (MCP).

## 🚀 Features

- **Persistent Chat Memory**: Stores and retrieves conversation history using PostgreSQL
- **Web Search Integration**: Real-time web search powered by Tavily API through MCP server
- **Session Management**: Create, manage, and switch between multiple chat sessions
- **Interactive UI**: Clean Streamlit interface for seamless user experience
- **MCP Architecture**: Modular design using Model Context Protocol for tool integration
- **Docker Support**: Complete containerized deployment with Docker Compose
- **Async Support**: Efficient handling of concurrent operations

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   LangGraph     │    │  MCP Server     │
│   Frontend      │◄──►│   Workflow      │◄──►│   (FastMCP)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   LLM Provider  │    │   Tavily API    │
│   Database      │    │   (Gemini)      │    │   Web Search    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- **Backend:** Python 3.8+
- **AI:** Google Gemini 2.0 Flash, GPT4.1-mini
- **Database:** PostgreSQL 15
- **UI:** Streamlit
- **Containers:** Docker & Docker Compose
- **Database Management:** pgAdmin 4
- **API Keys:** Tavily API key, Google Gemini API key

## 🛠️ Installation

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/pofmN/memory_chatbot.git
   cd memory_chat
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your API keys:
   ```env
   # API Keys (Required)
   TAVILY_API_KEY=your_tavily_api_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

3. **Start with Docker Compose**
   ```bash
   # Start all services
   docker-compose up -d --build
   
   # Check status
   docker-compose ps
   
   # View logs
   docker-compose logs -f
   ```

4. **Access the application**
   - **Chatbot UI**: http://localhost:8501
   - **PgAdmin**: http://localhost:8080 (admin@chatbot.com / admin123)

### Option 2: Local Development

1. **Clone and setup environment**
   ```bash
   git clone https://github.com/pofmN/memory_chatbot.git
   cd memory_chat
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database**
   ```bash
   # Install PostgreSQL and create database
   createdb chatbot_db
   createuser chatbot_user
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your local database settings:
   ```env
   # Local Database Configuration
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=chatbot_db
   DB_USER=chatbot_user
   DB_PASSWORD=your_password
   
   # API Keys
   TAVILY_API_KEY=your_tavily_api_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 🚀 Usage

### Main Application
```bash
# With Docker
docker-compose up -d
# Access: http://localhost:8501

# Local development
streamlit run app.py
```

### MCP Server (Standalone)
```bash
cd mcp_server
python mcp_server.py
```

### CLI Client for Testing
```bash
cd mcp_server
python chatbot_client.py
```

## 📁 Project Structure

```
memory_chat/
├── app.py                   # Main Streamlit application
├── storage.py               # Database manager and operations
├── requirements.txt         # Python dependencies
├── docker-compose.yaml      # Docker orchestration
├── Dockerfile              # Container configuration
├── .env.example            # Environment variables template
├── .gitignore             # Git ignore rules
├── README.md              # This file
│
├── mcp_server/            # MCP Server implementation
│   ├── mcp_server.py      # FastMCP server with tools
│   ├── chatbot_client.py  # CLI client for testing
│   └── storage.py         # Database operations
│
└── init.sql               # Database initialization script
```

## 🔧 Configuration

### Database Schema

The application uses PostgreSQL with these tables:
- `sessions`: Chat session metadata and summaries
- `messages`: Individual chat messages with timestamps
- `search_history`: Web search queries and results

### MCP Tools

The MCP server provides these tools:
- `search_web`: Web search using Tavily API
- `get_history_summary`: Retrieve chat session summaries
- `test_mcp_server`: Health check endpoint

### Environment Variables

```env
# Database (Auto-configured in Docker)
DB_HOST=postgres
DB_PORT=5432
DB_NAME=chatbot_db
DB_USER=chatbot_user
DB_PASSWORD=chatbot_password

# Required API Keys
TAVILY_API_KEY=your_tavily_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

## 📚 API Reference

### MCP Server Tools

#### Web Search
```python
await session.call_tool(
    "search_web",
    arguments={
        "query": "Python programming",
        "max_results": 5,
        "search_depth": "basic"  # or "advanced"
    }
)
```

#### History Summary
```python
await session.call_tool(
    "get_history_summary",
    arguments={
        "session_id": "your-session-id"
    }
)
```

### Database Operations

```python
from storage import DatabaseManager

db = DatabaseManager()

# Session management
session_id = db.create_session()
db.save_message(session_id, "user", "Hello!")
history = db.get_chat_history(session_id)
summary = db.get_session_summary(session_id)
```

## 🧪 Testing

### Test MCP Server
```bash
cd mcp_server
python chatbot_client.py
# Commands: test, help, settings, exit
```

### Test Database Connection
```bash
# Local testing
python -c "from storage import DatabaseManager; db = DatabaseManager(); print('Database connected!')"

# Docker testing
docker-compose exec chatbot-app python -c "from storage import DatabaseManager; db = DatabaseManager(); print('Database connected!')"
```

### Docker Health Checks
```bash
# Check container health
docker-compose ps

# View container logs
docker-compose logs chatbot-app
docker-compose logs postgres
```

## 🔍 CLI Commands

When using `chatbot_client.py`:

- `help` - Show available commands
- `settings` - Configure search parameters (max results, depth)
- `test` - Test MCP server connection
- `history` - Fetch chat history summary
- `exit/quit/bye` - Exit the application

## 🐛 Troubleshooting

### Docker Issues

**Build Failures**
```bash
# Clean build
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Container Connection Issues**
```bash
# Check container network
docker network ls
docker-compose logs -f
```

### Local Development Issues

**MCP Server Connection Failed**
```bash
# Verify MCP server path
python mcp_server/mcp_server.py

# Check environment variables
cat .env | grep -v "^#"
```

**Database Connection Error**
```bash
# Check PostgreSQL service
sudo service postgresql status  # Linux
brew services list | grep postgres  # macOS

# Test connection
psql -h localhost -U chatbot_user -d chatbot_db
```

**Import Errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 🚦 Deployment

### Production Deployment

1. **Set up production environment**
   ```bash
   # Use production environment file
   cp .env.example .env.production
   # Edit with production values
   ```

2. **Deploy with Docker**
   ```bash
   # Production deployment
   docker-compose up -d --build
   
   # Monitor logs
   docker-compose logs -f
   ```

3. **Database backup**
   ```bash
   # Backup database
   docker-compose exec postgres pg_dump -U chatbot_user chatbot_db > backup.sql
   
   # Restore database
   docker-compose exec -T postgres psql -U chatbot_user chatbot_db < backup.sql
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Add type hints where appropriate
- Write docstrings for functions and classes
- Update tests for new features
- Update documentation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastMCP](https://github.com/fastmcp/fastmcp) for MCP protocol implementation
- [Tavily](https://tavily.com/) for web search API
- [LangGraph](https://langchain-ai.github.io/langgraph/) for workflow orchestration
- [Streamlit](https://streamlit.io/) for the web interface
- [PostgreSQL](https://www.postgresql.org/) for robust database management

## 📞 Support

If you encounter any issues or have questions:

1. **Check existing issues**: [GitHub Issues](https://github.com/pofmN/memory_chatbot/issues)
2. **Create new issue**: Include error logs, environment details, and steps to reproduce
3. **Discussion**: Use GitHub Discussions for general questions and ideas

### Getting Help

- Include your environment details (OS, Python version, Docker version)
- Share relevant error logs
- Describe steps to reproduce the issue
- Mention if you're using Docker or local development

---

**Built with ❤️ using Python, FastMCP, LangGraph, and Streamlit**

[![GitHub](https://img.shields.io/badge/GitHub-pofmN/memory_chatbot-blue?logo=github)](https://github.com/pofmN/memory_chatbot)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://docker.com)