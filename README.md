# AI Chatbot with Memory & Event Management

A sophisticated AI chatbot application with persistent memory, event management, user information extraction, and web search capabilities. Built using LangGraph, Streamlit, SQLAlchemy, and Model Context Protocol (MCP).

## 🚀 Features

- **Persistent Chat Memory**: Stores and retrieves conversation history using PostgreSQL with SQLAlchemy ORM
- **User Information Extraction**: Automatically extracts and stores user profile information from conversations
- **Event Management**: Intelligent event extraction from natural language and calendar management
- **Web Search Integration**: Real-time web search powered by Tavily API through MCP server
- **Session Management**: Single-user persistent session with auto-summarization
- **Customizable AI Personality**: Multiple personality presets and communication styles
- **Interactive UI**: Clean Streamlit interface with sidebar customization
- **Modular Architecture**: Well-structured codebase with separate agents and tools
- **SQLAlchemy ORM**: Robust database operations with proper relationship management
- **Docker Support**: Complete containerized deployment with Docker Compose

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   LangGraph     │    │  MCP Server     │
│   Frontend      │◄──►│   Workflow      │◄──►│   (Python)      │
│   (UI Layer)    │    │   (Core Logic)  │    │   (Tools)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   OpenAI GPT    │    │   Tavily API    │
│   + SQLAlchemy  │    │   4o-mini       │    │   Web Search    │
│   (Database)    │    │   (LLM)         │    │   (External)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         │
┌─────────────────┐
│   Specialized   │
│   Agents:       │
│   • User Info   │
│   • Events      │
│   • Memory      │
└─────────────────┘
```

## 📋 Prerequisites

- **Backend:** Python 3.8+
- **AI:** OpenAI GPT-4o-mini (with custom endpoint)
- **Database:** PostgreSQL 15+ with SQLAlchemy ORM
- **UI:** Streamlit
- **Containers:** Docker & Docker Compose
- **Database Management:** pgAdmin 4
- **API Keys:** Tavily API key, OpenAI API key

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
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   GOOGLE_API_KEY=your_google_api_key
   
   # Database Configuration
   DB_HOST=postgres
   DB_PORT=5432
   DB_NAME=chatbot_db
   DB_USER=chatbot_user
   DB_PASSWORD=chatbot_password
   
   # MCP Server Configuration
   MCP_SERVER_PATH=./mcp_server/server.py
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
   psql -d chatbot_db -f database/init.sql
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
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   GOOGLE_API_KEY=your_google_api_key
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

### Customization Features
- **AI Personality**: Choose from predefined personalities or create custom ones
- **Communication Style**: Conversational, Formal, Technical, Simple, Detailed, Brief
- **Response Length**: Brief, Balanced, Detailed, Comprehensive
- **Language**: English, Vietnamese, Mixed, Auto-detect
- **Preset Management**: Save and load custom AI configurations

### MCP Server Commands
```bash
cd mcp_server
python server.py
```

## 🔧 Configuration

### Database Schema (SQLAlchemy Models)

The application uses PostgreSQL with SQLAlchemy ORM:

**Core Tables:**
- `user_profile`: Single user profile information
- `chat_sessions`: Chat session metadata
- `chat_messages`: Individual messages with relationships
- `chat_summaries`: Auto-generated conversation summaries

**Feature Tables:**
- `activities`: User activities and tasks
- `event`: Calendar events and appointments
- `alert`: System alerts and notifications
- `recommendation`: AI-generated recommendations
- `activities_analysis`: Activity frequency analysis

### Specialized Agents

**User Information Agent:**
- Extracts personal information from conversations
- Validates and stores user profile data
- Handles profile updates and corrections

**Event Extraction Agent:**
- Parses natural language for events and appointments
- Converts relative dates to absolute timestamps
- Manages event priorities and locations

**Memory Tools:**
- Auto-summarization every 5 messages
- Intelligent history retrieval
- Context-aware conversation memory

### Environment Variables

```env
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=chatbot_db
DB_USER=chatbot_user
DB_PASSWORD=chatbot_password

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# MCP Server
MCP_SERVER_PATH=./mcp_server/server.py

# UI Configuration
PAGE_TITLE=AI Chatbot with Memory
PAGE_ICON=🤖
LAYOUT=wide
```

## 📚 API Reference

### Agent Processing

#### User Information Extraction
```python
from agents.extract_user_info_agent import create_user_info_extraction_agent

agent = create_user_info_extraction_agent(llm)
result = agent.process("My name is John, I'm 25 years old from NYC")

if result.get("success"):
    print(f"Updated fields: {result['updated_fields']}")
    print(f"Data: {result['extracted_data']}")
```

#### Event Extraction
```python
from agents.extract_event_agent import create_event_extraction_agent

agent = create_event_extraction_agent(llm)
result = agent.process("Meeting with John tomorrow at 2 PM in conference room A")
```

### Database Operations (SQLAlchemy)

```python
from database.storage import DatabaseManager

db = DatabaseManager()

# User profile management
profile = db.get_user_profile()
success = db.update_user_profile({"user_name": "John", "age": 25})

# Session management
session_id = db.create_session()
db.save_message(session_id, "user", "Hello!")
history = db.get_chat_history(session_id)

# Event management
event_id = db.create_event({
    "name": "Team Meeting",
    "start_time": datetime.now(),
    "location": "Conference Room A"
})
```

### MCP Server Tools

#### Web Search
```python
await session.call_tool(
    "search_web",
    arguments={
        "query": "Python programming best practices",
        "max_results": 3
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

## 🧪 Testing

### Test User Information Agent
```bash
cd agents/extract_user_info_agent
python extract_user_info.py
```

### Test Event Extraction Agent
```bash
cd agents/extract_event_agent
python extract_event.py
```

### Test Database Operations
```bash
# Test SQLAlchemy models
python -c "from database.storage import DatabaseManager; db = DatabaseManager(); print('✅ Database connected!')"

# Test with Docker
docker-compose exec chatbot-app python -c "from database.storage import DatabaseManager; db = DatabaseManager(); print('✅ Database connected!')"
```

### Test MCP Server
```bash
cd mcp_server
python server.py
```

## 🔍 Features Deep Dive

### AI Personality Customization
- **Personality Presets**: Friendly Assistant, Professional Advisor, Creative Companion, Study Buddy, Casual Friend
- **Custom Personalities**: Write your own AI personality descriptions
- **Communication Styles**: Conversational, Formal, Technical, Simple, Detailed, Brief
- **Response Lengths**: Brief, Balanced, Detailed, Comprehensive
- **Language Support**: English, Vietnamese, Mixed, Auto-detect
- **Preset Management**: Save and load custom configurations

### Intelligent Memory System
- **Auto-Summarization**: Automatically summarizes every 5 messages
- **Context Awareness**: Maintains conversation context across sessions
- **User Profile Integration**: Remembers user information and preferences
- **Smart Retrieval**: Contextual history retrieval for relevant responses

### Event Management
- **Natural Language Parsing**: "Meeting tomorrow at 2 PM" → structured event
- **Smart Date Recognition**: Handles relative dates and times
- **Priority Detection**: Infers event importance from language cues
- **Location Extraction**: Physical and virtual meeting locations
- **Validation**: Ensures event data consistency

### User Information Extraction
- **Automatic Detection**: Extracts personal info from natural conversation
- **Profile Building**: Incrementally builds user profile
- **Data Validation**: Validates phone numbers, dates, and other fields
- **Update Handling**: Manages profile corrections and updates

## 🐛 Troubleshooting

### Common Issues

**SQLAlchemy Import Errors**
```bash
# Ensure all dependencies are installed
pip install sqlalchemy>=2.0.0 psycopg2-binary>=2.9.0

# Check Python path
python -c "import sqlalchemy; print(sqlalchemy.__version__)"
```

**Database Connection Issues**
```bash
# Test connection
python -c "from database.storage import DatabaseManager; db = DatabaseManager(); print(db.test_connection())"

# Check database status
docker-compose exec postgres psql -U chatbot_user -d chatbot_db -c "SELECT 1;"
```

**Agent Processing Errors**
```bash
# Test user info agent
python agents/extract_user_info_agent/extract_user_info.py

# Test event agent
python agents/extract_event_agent/extract_event.py
```

**MCP Server Issues**
```bash
# Check MCP server path
python mcp_server/server.py

# Verify environment variables
cat .env | grep MCP_SERVER_PATH
```

### Docker Issues

**Container Build Failures**
```bash
# Clean rebuild
docker-compose down --volumes
docker-compose build --no-cache
docker-compose up -d
```

**Database Initialization**
```bash
# Force database recreation
docker-compose down --volumes
docker-compose up -d postgres
docker-compose exec postgres psql -U chatbot_user -d chatbot_db -f /docker-entrypoint-initdb.d/init.sql
```

## 🚦 Deployment

### Production Deployment

1. **Environment Configuration**
   ```bash
   # Production environment
   cp .env.example .env.production
   
   # Edit with production values
   nano .env.production
   ```

2. **Database Backup & Migration**
   ```bash
   # Backup database
   docker-compose exec postgres pg_dump -U chatbot_user chatbot_db > backup_$(date +%Y%m%d_%H%M%S).sql
   
   # Restore database
   docker-compose exec -T postgres psql -U chatbot_user chatbot_db < backup.sql
   ```

3. **Production Deployment**
   ```bash
   # Deploy with production settings
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
   
   # Monitor logs
   docker-compose logs -f --tail=100
   ```

4. **Health Checks**
   ```bash
   # Check all services
   docker-compose ps
   
   # Test database connection
   docker-compose exec chatbot-app python -c "from database.storage import DatabaseManager; print('✅' if DatabaseManager().test_connection() else '❌')"
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- **Code Style**: Follow PEP 8 for Python code
- **Type Hints**: Add type hints for better code clarity
- **Documentation**: Write comprehensive docstrings
- **Testing**: Add tests for new features
- **Modular Design**: Keep components separate and focused
- **Error Handling**: Implement proper exception handling
- **Logging**: Add appropriate logging for debugging

### Project Structure Guidelines

- **Agents**: Place specialized agents in `agents/` directory
- **Tools**: Implement tools in `tools/` directory
- **UI Components**: Keep UI logic in `ui/` directory
- **Configuration**: Centralize config in `config/` directory
- **Database**: All database operations in `database/` directory
- **Utils**: Helper functions in `utils/` directory

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangGraph](https://langchain-ai.github.io/langgraph/) for workflow orchestration
- [SQLAlchemy](https://sqlalchemy.org/) for robust ORM capabilities
- [Streamlit](https://streamlit.io/) for the interactive web interface
- [PostgreSQL](https://www.postgresql.org/) for reliable database management
- [Tavily](https://tavily.com/) for web search API capabilities
- [OpenAI](https://openai.com/) for GPT-4o-mini language model
- [Model Context Protocol](https://github.com/modelcontextprotocol/servers) for tool integration

## 📞 Support

For support and questions:

1. **Check Documentation**: Review this README and inline documentation
2. **GitHub Issues**: [Create an issue](https://github.com/pofmN/memory_chatbot/issues) with detailed information
3. **Discussions**: Use GitHub Discussions for general questions

### When Reporting Issues

Include the following information:
- **Environment**: OS, Python version, Docker version
- **Error Logs**: Complete error messages and stack traces
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Configuration**: Relevant environment variables (without API keys)
- **Expected vs Actual**: What you expected vs what happened

---

**Built with ❤️ using Python, SQLAlchemy, LangGraph, and Streamlit**

[![GitHub](https://img.shields.io/badge/GitHub-pofmN/memory_chatbot-blue?logo=github)](https://github.com/pofmN/memory_chatbot)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red?logo=sqlalchemy)](https://sqlalchemy.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://docker.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit)](https://streamlit.io)
