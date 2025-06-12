# Memory Chat with MCP Integration

A sophisticated chatbot application with persistent memory and web search capabilities, built using LangGraph, Streamlit, and Model Context Protocol (MCP).

## 🚀 Features

- **Persistent Chat Memory**: Stores and retrieves conversation history using PostgreSQL
- **Web Search Integration**: Real-time web search powered by Tavily API through MCP server
- **Session Management**: Create, manage, and switch between multiple chat sessions
- **Interactive UI**: Clean Streamlit interface for seamless user experience
- **MCP Architecture**: Modular design using Model Context Protocol for tool integration
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

<<<<<<< HEAD
- Python 3.8+
- PostgreSQL database
- Tavily API key
=======
- **Backend:** Python 3.13+
- **AI:** Google Gemini 2.0 Flash, GPT4.1-mini
- **Database:** PostgreSQL 15
- **UI:** Streamlit
- **Containers:** Docker & Docker Compose
- **Database Management:** pgAdmin 4

## 📦 Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.8 or higher
>>>>>>> df71f86 (modify: rm unecessary file)
- Google Gemini API key

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/memory_chat.git
   cd memory_chat
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your credentials:
   ```env
   # Database Configuration
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=chatbot_db
   DB_USER=chatbot_user
   DB_PASSWORD=your_password
   
   # API Keys
   TAVILY_API_KEY=your_tavily_api_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

5. **Set up PostgreSQL database**
   ```bash
   # Create database and user
   createdb chatbot_db
   createuser chatbot_user
   ```

## 🚀 Usage

### Running the Main Application

```bash
streamlit run app_draft.py
```

### Running the MCP Server (Standalone)

```bash
cd mcp_server
python mcp_server.py
```

### Using the CLI Client

```bash
cd mcp_server
python chatbot_client.py
```

## 📁 Project Structure

```
memory_chat/
├── app_draft.py              # Main Streamlit application
├── storage.py                # Database manager and operations
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── README.md                # This file
│
├── mcp_server/              # MCP Server implementation
│   ├── mcp_server.py        # FastMCP server with tools
│   ├── chatbot_client.py    # CLI client for testing
│   └── storage.py           # Database operations (symlink)
│
└── docs/                    # Documentation
    └── api.md              # API documentation
```

## 🔧 Configuration

### Database Setup

The application uses PostgreSQL with the following tables:
- `sessions`: Chat session metadata
- `messages`: Individual chat messages
- `search_history`: Web search history

### MCP Tools

The MCP server provides these tools:
- `search_web`: Web search using Tavily API
- `get_history_summary`: Retrieve chat session summaries
- `test_mcp_server`: Health check endpoint

## 📚 API Reference

### MCP Server Endpoints

#### Search Web
```python
await session.call_tool(
    "search_web",
    arguments={
        "query": "Python programming",
        "max_results": 5,
        "search_depth": "basic"
    }
)
```

#### Get History Summary
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

# Create session
db.create_session("session-id")

# Save message
db.save_message("session-id", "user", "Hello!")

# Get chat history
history = db.get_chat_history("session-id")
```

## 🧪 Testing

### Test MCP Server Connection
```bash
cd mcp_server
python chatbot_client.py
# Type 'test' to check connection
```

### Test Database Connection
```bash
python -c "from storage import DatabaseManager; db = DatabaseManager(); print('Database connected!')"
```

## 🔍 CLI Commands

When using the CLI client (`chatbot_client.py`):

- `help` - Show available commands
- `settings` - Configure search parameters
- `test` - Test MCP server connection
- `get_history_summary` - Fetch chat history
- `exit/quit/bye` - Exit the application

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastMCP](https://github.com/fastmcp/fastmcp) for MCP protocol implementation
- [Tavily](https://tavily.com/) for web search API
- [LangGraph](https://langchain-ai.github.io/langgraph/) for workflow orchestration
- [Streamlit](https://streamlit.io/) for the web interface

## 🐛 Troubleshooting

### Common Issues

**MCP Server Connection Failed**
```bash
# Check if MCP server is running
python mcp_server/mcp_server.py

# Verify environment variables
cat .env
```

**Database Connection Error**
```bash
# Check PostgreSQL service
sudo service postgresql status

# Verify database exists
psql -l | grep chatbot_db
```

**Import Errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## 📞 Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/yourusername/memory_chat/issues) page
2. Create a new issue with detailed description
3. Include error logs and environment details

---

**Built with ❤️ using Python, FastMCP, and LangGraph**
