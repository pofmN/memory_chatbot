# Memory Chatbot with Firebase Notifications & AI Agents

A comprehensive AI chatbot ecosystem featuring real-time Firebase Cloud Messaging notifications, background alert services, specialized LangGraph agents, and intelligent activity analysis. Built using LangGraph, Streamlit, PostgreSQL, Firebase FCM, and Model Context Protocol (MCP) for seamless multi-user chat experiences with proactive recommendations.

## 🚀 Features

### Core Capabilities
- **Persistent Chat Memory**: Multi-user chat sessions with PostgreSQL storage and SQLAlchemy ORM
- **Firebase Cloud Messaging (FCM)**: Real-time browser notifications with token management and Firebase Admin SDK
- **Background Alert Service**: Automated alert processing and notification delivery system
- **Specialized AI Agents**: LangGraph-powered agents for user information, event management, and activity analysis
- **Web Search Integration**: Real-time web search powered by Tavily API through MCP server
- **Activity Analysis**: Intelligent pattern recognition and habit analysis with recommendation engine

### Firebase & Notification System
- **FCM Token Management**: Automatic token collection and storage with device tracking
- **Background Alert Processing**: Continuous monitoring for due alerts and recommendations
- **Real-time Notifications**: Browser push notifications with Firebase Admin SDK integration
- **Multi-device Support**: Cross-platform notification delivery and token synchronization
- **Notification History**: Complete tracking of sent notifications and user acknowledgments

### AI-Powered Agents & Analysis
- **User Information Agent**: Automatic extraction and validation of personal information from conversations
- **Event Extraction Agent**: Natural language processing for calendar events with smart date/time parsing
- **Activity Analyzer**: Pattern recognition engine for user habits and routine analysis
- **Recommendation Engine**: AI-generated suggestions based on activity patterns and upcoming events
- **Memory Management**: Auto-summarization and intelligent conversation history retrieval

### Infrastructure & Deployment
- **Docker Containerization**: Complete multi-service deployment with Docker Compose
- **PostgreSQL Database**: Robust multi-user database schema with vector embeddings support
- **MCP Protocol Integration**: Model Context Protocol for extensible tool integration
- **FastAPI Services**: RESTful APIs for FCM token management and notification services
- **Firebase Hosting**: Dedicated notification setup site for FCM token collection

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   Firebase      │    │  Background     │
│   Frontend      │◄──►│   FCM Service   │◄──►│  Alert Service  │
│   (Chat UI)     │    │   (Push Notif.) │    │  (Monitoring)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         ▼              ┌─────────────────┐    ┌─────────────────┐
┌─────────────────┐     │   FastAPI FCM   │    │  Recommendation │
│   LangGraph     │◄───►│   Server        │    │  Engine         │
│   Agents Hub    │     │   (Token Mgmt)  │    │  (AI Analysis)  │
└─────────────────┘     └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Specialized    │    │   PostgreSQL    │    │  External APIs  │
│  AI Agents:     │◄──►│   Multi-User    │    │  • Tavily Web   │
│  • User Info    │    │   Database      │    │  • OpenAI LLM   │
│  • Events       │    │   + Vectors     │    │  • Firebase     │
│  • Activities   │    │   + FCM Tokens  │    │  • MCP Tools    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Service Architecture
- **Main App**: Streamlit frontend with LangGraph workflow orchestration
- **FCM Service**: FastAPI server for Firebase token management and notification APIs
- **Background Service**: Continuous monitoring for alerts, recommendations, and activity analysis
- **Notifier Site**: Firebase-hosted website for FCM token collection from browsers
- **Database Layer**: PostgreSQL with multi-user schema, vector embeddings, and FCM token storage
- **MCP Server**: Model Context Protocol server providing web search and tool integration

## 📋 Prerequisites

### Core Requirements
- **Python**: 3.8+ with pip package manager
- **Database**: PostgreSQL 15+ with pgvector extension for embeddings
- **AI Services**: OpenAI API key (GPT-4o-mini) with custom endpoint support
- **Web Search**: Tavily API key for real-time web search capabilities
- **Containers**: Docker & Docker Compose for deployment

### Firebase Requirements
- **Firebase Project**: Google Firebase account with Cloud Messaging enabled
- **Service Account**: Firebase Admin SDK credentials (JSON key file)
- **VAPID Keys**: Web Push certificate for browser notifications
- **Firebase Hosting**: Optional, for hosting the FCM token collection site

### Development Tools
- **Database GUI**: pgAdmin 4 for database management (included in Docker setup)
- **Code Editor**: VS Code or similar with Python support
- **Git**: Version control for project management

## 🛠️ Installation & Setup

### Step 1: Project Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/pofmN/memory_chatbot.git
   cd memory_chat
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

### Step 2: Firebase Configuration

3. **Set up Firebase Project**
   - Visit [Firebase Console](https://console.firebase.google.com/)
   - Create a new project or use existing one
   - Enable **Cloud Messaging** in project settings
   - Generate **Web Push certificates** (VAPID keys)

4. **Generate Service Account Key**
   - Go to Project Settings > Service Accounts
   - Click "Generate new private key"
   - Save as `firebase_key.json` in project root
   - This file contains Firebase Admin SDK credentials

5. **Configure Firebase Web App**
   - Register a web app in Firebase console
   - Copy the configuration object (apiKey, projectId, etc.)
   - Update `notifier_site/public/index.html` with your config

### Step 3: Environment Configuration

6. **Update .env file**
   ```env
   # API Keys (Required)
   OPENAI_API_KEY=your_openai_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here

   # Firebase Configuration
   FIREBASE_CREDENTIALS_PATH=./firebase_key.json
   FIREBASE_API_KEY=your_firebase_api_key
   FIREBASE_PROJECT_ID=your_project_id
   FIREBASE_MESSAGING_SENDER_ID=your_sender_id
   FIREBASE_APP_ID=your_app_id
   FIREBASE_VAPID_KEY=your_vapid_key

   # Database Configuration
   DB_HOST=postgres
   DB_PORT=5432
   DB_NAME=chatbot_db
   DB_USER=chatbot_user
   DB_PASSWORD=chatbot_password

   # Service Configuration
   FCM_SERVICE_PORT=8001
   FCM_SERVICE_URL=http://localhost:8001
   MCP_SERVER_PATH=./mcp/server.py

   # Optional: Analytics & Monitoring
   LANGSMITH_API_KEY=your_langsmith_key
   LANGSMITH_TRACING=true
   LANGSMITH_PROJECT=memory_chatbot
   ```

### Step 4: Docker Deployment (Recommended)

7. **Start all services**
   ```bash
   # Build and start all containers
   docker-compose up -d --build

   # Check service status
   docker-compose ps

   # Monitor logs
   docker-compose logs -f
   ```

8. **Verify deployment**
   - **Main App**: http://localhost:8501
   - **FCM Service**: http://localhost:8001
   - **Database Admin**: http://localhost:8080 (pgAdmin)
   - **Notifier Site**: `notifier_site/public/index.html` (serve locally or deploy to Firebase)

### Step 5: Alternative Local Development

For development without Docker:

```bash
# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (local installation required)
# Update .env with local database settings

# Start FCM Service
python start_fcm_service.py

# Start main application
streamlit run app_dev.py

# Start background service (optional)
python -m agent.bg_running.background_alert_service
```
## 🚀 Usage

### Setting up Browser Notifications

1. **Enable Notifications**
   - Visit the main app: http://localhost:8501
   - Click "Enable Notifications" in the sidebar
   - Allow browser notification permissions when prompted
   - Your FCM token will be automatically registered

2. **Alternative Token Registration**
   ```bash
   # Serve the notifier site locally
   cd notifier_site/public
   python -m http.server 3000
   
   # Visit http://localhost:3000
   # Follow prompts to register FCM token
   ```

### Core Features Usage

3. **Chat Interface**
   - Natural conversation with memory retention
   - Automatic user information extraction
   - Event and activity tracking from conversation
   - Real-time web search integration

4. **Event Management**
   ```
   User: "I have a meeting with John tomorrow at 2 PM"
   → Automatically creates calendar event
   → Sets up reminder notifications
   → Stores in database with priority analysis
   ```

5. **Activity Analysis**
   ```
   User: "I usually go jogging in the morning"
   → Analyzes activity patterns
   → Generates recommendations
   → Creates intelligent alerts
   ```

6. **Background Services**
   - Automatic alert processing every 5 minutes
   - Recommendation generation based on activity patterns
   - FCM notification delivery for due alerts
   - Activity analysis and habit tracking

### Advanced Features

7. **MCP Tools Integration**
   ```bash
   # Test MCP server directly
   cd mcp
   python server.py
   
   # Available tools:
   # - Web search via Tavily
   # - User information extraction
   # - Event management
   # - Activity tracking
   ```

8. **API Endpoints**
   ```bash
   # FCM Service APIs
   curl -X POST http://localhost:8001/api/fcm/register \
     -H "Content-Type: application/json" \
     -d '{"token":"fcm_token_here","user_id":"user_123"}'
   
   # Get active tokens
   curl http://localhost:8001/api/fcm/tokens
   ```

### Customization Options

9. **AI Personality Settings**
   - Choose from predefined personality presets
   - Adjust communication style (formal, casual, technical)
   - Set response length preferences
   - Configure language settings

10. **Notification Preferences**
    - Configure alert timing and frequency
    - Set priority levels for different event types
    - Customize notification content and formatting

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

### Multi-User Database Schema

The application uses PostgreSQL 15+ with pgvector extension and comprehensive multi-user support:

#### Core User Management
- **`users`**: Multi-user support with UUID identifiers, profiles, and authentication
- **`chat_sessions`**: User-specific chat sessions with metadata and context
- **`chat_messages`**: Individual messages linked to sessions with role tracking
- **`chat_summaries`**: Auto-generated conversation summaries per session

#### Firebase & Notification System  
- **`fcm_tokens`**: Firebase Cloud Messaging tokens with device tracking
- **`alert`**: User-specific system alerts with trigger times and priorities
- **`notification_history`**: Complete tracking of sent notifications and acknowledgments
- **`user_sessions`**: Session management with expiration and device tracking

#### AI Analysis & Recommendations
- **`activities`**: User activities with tags, timestamps, and analysis status
- **`activities_analysis`**: Pattern analysis results with frequency data and preferences
- **`event`**: Calendar events with vector embeddings for similarity search
- **`recommendation`**: AI-generated suggestions with scoring and status tracking

### Specialized LangGraph Agents

#### User Information Agent (`agent/extract_user_info/`)
```python
# Workflow: extract → validate → save
- Automatic extraction of personal information from natural conversation
- Validation of phone numbers, birth years, and data consistency
- Incremental profile building with conflict resolution
- Multi-language support for information detection
```

#### Event Extraction Agent (`agent/extract_event/`)
```python
# Workflow: detect_intent → extract → validate → save/update/search
- Natural language processing for calendar events
- Smart date/time parsing with timezone support
- Intent detection: CREATE, UPDATE, SEARCH, DELETE
- Priority inference from context and keywords
```

#### Activity Analyzer (`agent/recommendation/activity_analyzer.py`)
```python
# Pattern recognition for user habits and routines
- Groups activities by similarity and tags
- Analyzes preferred times and frequency patterns
- Generates habit recommendations based on analysis
- Supports both automated and manual activity analysis
```

#### Recommendation Engine (`agent/recommendation/recommendation_engine.py`)
```python
# AI-powered suggestions based on patterns
- Combines activity analysis with upcoming events
- Generates personalized recommendations with scoring
- Creates system alerts for high-priority suggestions
- Updates recommendation status based on user interaction
```

### Firebase Cloud Messaging Integration

#### FCM Service Architecture
```bash
# FastAPI server at localhost:8001
POST /api/fcm/register    # Register FCM tokens
GET  /api/fcm/tokens      # Retrieve active tokens
```

#### Background Alert Service
```python
# Continuous monitoring service
- Processes due alerts every 5 minutes
- Sends Firebase notifications to registered devices
- Generates periodic recommendations
- Cleans up old alerts and maintains data hygiene
```

#### Token Collection Flow
```
1. User visits notifier site or main app
2. Browser requests notification permission
3. Firebase generates FCM token
4. Token registered via API with user association
5. Background service monitors for due alerts
6. Notifications sent via Firebase Admin SDK
```

### Environment Configuration

```env
# Core Application
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Database (Multi-user PostgreSQL)
DB_HOST=postgres
DB_PORT=5432
DB_NAME=chatbot_db
DB_USER=chatbot_user
DB_PASSWORD=chatbot_password

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=./firebase_key.json
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
FIREBASE_VAPID_KEY=your_vapid_key

# Service Configuration
FCM_SERVICE_PORT=8001
FCM_SERVICE_URL=http://localhost:8001
MCP_SERVER_PATH=./mcp/server.py

# Optional: Analytics & Monitoring
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=memory_chatbot
```

## 📚 API Reference

### LangGraph Agent Processing

#### User Information Extraction
```python
from agent.extract_user_info.agent import create_user_info_extraction_agent

agent = create_user_info_extraction_agent(llm)
result = agent.process("My name is John, I'm 25 years old from NYC")

if result.get("success"):
    print(f"Updated fields: {result['updated_fields']}")
    print(f"Data: {result['extracted_data']}")
```

#### Event Management
```python
from agent.extract_event.agent import EventExtractionAgent

agent = EventExtractionAgent(llm)
result = agent.process("Meeting with John tomorrow at 2 PM in conference room A")
# Supports: CREATE, UPDATE, SEARCH, DELETE operations
```

#### Activity Analysis
```python
from agent.recommendation.activity_analyzer import analyze_pending_activities

# Analyze pending activities
result = analyze_pending_activities()
print(f"Analyzed {result['analyzed_count']} activity types")

# Analyze specific activity type
from agent.recommendation.activity_analyzer import analyze_activity_type
result = analyze_activity_type("jogging")
```

#### Recommendation Generation
```python
from agent.recommendation.recommendation_engine import generate_recommendations

result = generate_recommendations()
print(f"Generated {len(result['recommendations'])} recommendations")
print(f"Created {result['alerts_created']} alerts")
```

### Firebase Cloud Messaging API

#### FCM Token Management
```bash
# Register FCM token
curl -X POST http://localhost:8001/api/fcm/register \
  -H "Content-Type: application/json" \
  -d '{
    "token": "fcm_token_here",
    "user_id": "12345678-1234-1234-1234-123456789012", 
    "device_type": "web",
    "user_agent": "Mozilla/5.0..."
  }'

# Get all active tokens
curl http://localhost:8001/api/fcm/tokens
```

#### Background Service Management
```python
from agent.bg_running.background_alert_service import (
    start_alert_service, stop_alert_service, get_service_status
)

# Start background monitoring
start_alert_service()

# Check service status
status = get_service_status()
print(f"Service running: {status['is_running']}")

# Force check for alerts
force_check_alerts()
```

### Database Operations

#### Multi-User Database Operations
```python
from core.base.storage import DatabaseManager

db = DatabaseManager()

# User management
user_id = "12345678-1234-1234-1234-123456789012"
profile = db.get_user_profile(user_id)
success = db.update_user_profile(user_id, {"user_name": "John", "age": 25})

# Session management
session_id = db.create_session(user_id)
db.save_message(session_id, "user", "Hello!")
history = db.get_chat_history(session_id)

# Activity and event management
activity_id = db.create_activity(user_id, activity_data)
event_id = db.create_event(user_id, event_data)
```

#### Recommendation & Alert Management
```python
# Create recommendations
recommendations = [
    {
        "title": "Morning Exercise Reminder",
        "content": "Based on your patterns, consider jogging at 7 AM",
        "score": 8,
        "recommendation_type": "activity"
    }
]
rec_ids = create_recommendation(recommendations)

# Create system alerts
alert_data = {
    "title": "Meeting Reminder",
    "message": "Your meeting with John starts in 30 minutes",
    "trigger_time": datetime.now() + timedelta(minutes=30),
    "priority": "high"
}
alert_id = create_system_alert(alert_data)
```

# Event management
event_id = db.create_event({
    "name": "Team Meeting",
    "start_time": datetime.now(),
    "location": "Conference Room A"
})
```

### MCP Server Tools

#### Web Search Integration
```python
# Via MCP client
await session.call_tool(
    "search_web", 
    arguments={
        "query": "Python programming best practices",
        "max_results": 5,
        "search_depth": "advanced"
    }
)
```

#### User Information Management
```python
await session.call_tool(
    "add_user_info",
    arguments={
        "user_input": "My name is Alice, I'm 28 years old and live in San Francisco"
    }
)
```

#### Event & Activity Management
```python
# Add events
await session.call_tool(
    "add_event",
    arguments={
        "user_input": "Meeting with team tomorrow at 3 PM in conference room B"
    }
)

# Add activities
await session.call_tool(
    "add_activity", 
    arguments={
        "user_input": "I usually go for a run every morning at 6 AM"
    }
)
```

#### History Management
```python
await session.call_tool(
    "get_history_summary",
    arguments={
        "session_id": "your-session-id"
    }
)
```

## 🧪 Testing

### Firebase & Notification Testing

```bash
# Test FCM service
curl -X POST http://localhost:8001/api/fcm/register \
  -H "Content-Type: application/json" \
  -d '{"token":"test_token","user_id":"test_user"}'

# Test notification delivery
python test_mcp_tools.py
```

### Agent Testing

```bash
# Test user information agent
cd agent/extract_user_info
python agent.py

# Test event extraction agent  
cd agent/extract_event
python agent.py

# Test activity analyzer
python -c "
from agent.recommendation.activity_analyzer import analyze_pending_activities
result = analyze_pending_activities()
print(result)
"

# Test recommendation engine
python -c "
from agent.recommendation.recommendation_engine import generate_recommendations
result = generate_recommendations()
print(f'Generated {len(result[\"recommendations\"])} recommendations')
"
```

### Background Service Testing

```bash
# Test background alert service
cd agent/bg_running
python background_alert_service.py

# Test alert processing
python -c "
from agent.bg_running.background_alert_service import force_check_alerts
force_check_alerts()
"
```

### Database Operations Testing

```bash
# Test database connection
python -c "from core.base.storage import DatabaseManager; db = DatabaseManager(); print('✅ Database connected!')"

# Test with Docker
docker-compose exec chatbot-app python -c "from database.storage import DatabaseManager; db = DatabaseManager(); print('✅ Database connected!')"
```

### Test MCP Server
```bash
cd mcp_server
python server.py
```

## 🔍 Features Deep Dive

### Firebase Cloud Messaging System
- **Real-time Notifications**: Browser push notifications via Firebase Admin SDK
- **Token Management**: Automatic FCM token collection and device tracking
- **Multi-device Support**: Notifications across web browsers and devices
- **Background Processing**: Continuous monitoring for due alerts and recommendations
- **Smart Delivery**: Priority-based notification scheduling and delivery
- **Notification History**: Complete tracking of sent notifications and user interactions

### Advanced AI Agent Architecture
- **LangGraph Workflow**: State-based agent processing with conditional flows
- **Intent Detection**: Multi-language intent recognition for event management
- **Structured Output**: Pydantic models for reliable data extraction
- **Error Handling**: Robust error recovery and validation at each processing step
- **Agent Orchestration**: Coordinated multi-agent processing for complex tasks

### Intelligent Activity Analysis
- **Pattern Recognition**: Analyzes user activities to identify habits and preferences
- **Time-based Analysis**: Preferred times, frequency patterns, and routine detection
- **Recommendation Generation**: AI-powered suggestions based on activity patterns
- **Habit Tracking**: Long-term behavior analysis and optimization suggestions
- **Activity Grouping**: Smart categorization of similar activities and tasks

### Real-time Alert & Monitoring System
- **Background Service**: Continuous monitoring service running every 5 minutes
- **Due Alert Processing**: Automatic detection and processing of upcoming events
- **Smart Notifications**: Context-aware notification content and timing
- **Alert Lifecycle**: Complete alert creation, processing, delivery, and cleanup
- **Status Tracking**: Real-time monitoring of service health and performance

### Multi-User Database Architecture
- **UUID-based Users**: Scalable multi-user support with unique identifiers
- **User Isolation**: Complete data separation between different users
- **Vector Embeddings**: OpenAI embeddings for event similarity and search
- **Relationship Management**: Proper foreign key relationships and data integrity
- **Performance Optimization**: Comprehensive indexing for fast query performance

### Event Management System
- **Natural Language Processing**: "Meeting tomorrow at 2 PM" → structured event
- **Smart Date Recognition**: Handles relative dates, times, and timezone conversion
- **Priority Inference**: Automatic priority detection from context and keywords
- **Location Extraction**: Physical addresses and virtual meeting platforms
- **CRUD Operations**: Complete Create, Read, Update, Delete event management
- **Conflict Detection**: Smart scheduling conflict detection and resolution

### Memory & Context Management
- **Auto-Summarization**: Intelligent conversation summarization every 5 messages
- **Context Preservation**: Maintains conversation context across sessions and restarts
- **Retrieval-Augmented**: Smart history retrieval for contextual responses
- **Profile Integration**: User information integration into conversation context
- **Session Management**: Persistent sessions with proper state management

## 🐛 Troubleshooting

### Firebase & Notification Issues

**FCM Service Not Starting**
```bash
# Check Firebase credentials
ls -la firebase_key.json

# Verify environment variables
echo $FIREBASE_CREDENTIALS_PATH

# Test FCM service manually
python start_fcm_service.py

# Check FCM service logs
docker-compose logs fcm-service
```

**Notifications Not Received**
```bash
# Check browser permissions
# Ensure notifications are allowed in browser settings

# Verify FCM token registration
curl http://localhost:8001/api/fcm/tokens

# Test notification delivery
python test_mcp_tools.py

# Check Firebase project configuration
cat notifier_site/public/index.html | grep "firebaseConfig"
```

### Database & Agent Issues

**Database Connection Problems**
```bash
# Test database connection
python -c "from core.base.storage import DatabaseManager; db = DatabaseManager(); print(db.test_connection())"

# Check PostgreSQL container
docker-compose exec postgres psql -U chatbot_user -d chatbot_db -c "SELECT 1;"

# Verify database schema
docker-compose exec postgres psql -U chatbot_user -d chatbot_db -c "\dt"
```

**Agent Processing Failures**
```bash
# Test individual agents
python -c "
from agent.extract_user_info.agent import create_user_info_extraction_agent
agent = create_user_info_extraction_agent()
result = agent.process('My name is John')
print(result)
"

# Test event extraction
python -c "
from agent.extract_event.agent import EventExtractionAgent
agent = EventExtractionAgent()
result = agent.process('Meeting tomorrow at 2 PM')
print(result)
"

# Check background service status
python -c "
from agent.bg_running.background_alert_service import get_service_status
print(get_service_status())
"
```

**MCP Server Issues**
```bash
# Test MCP server directly
cd mcp
python server.py

# Verify MCP client connection
python -c "
from core.base.mcp_client import init_mcp_client
client = init_mcp_client()
print('MCP client initialized successfully')
"

# Check available tools
python test_mcp_tools.py
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

## 🚦 Deployment

### Production Deployment Checklist

#### Security Configuration
```bash
# Generate secure passwords
DB_PASSWORD=$(openssl rand -base64 32)
ADMIN_PASSWORD=$(openssl rand -base64 16)

# Secure Firebase credentials
chmod 600 firebase_key.json
chown app:app firebase_key.json
```

#### Environment Setup
```env
# Production environment variables
NODE_ENV=production
DEBUG=false
LOG_LEVEL=info

# Secure database configuration
DB_HOST=your_postgres_host
DB_SSL_MODE=require
DB_POOL_SIZE=20

# Firebase production settings
FIREBASE_PROJECT_ID=your_production_project
FIREBASE_CREDENTIALS_PATH=/secure/path/firebase_key.json

# Rate limiting and security
RATE_LIMIT_REQUESTS_PER_MINUTE=60
MAX_CONCURRENT_SESSIONS=100
```

#### Docker Production Deployment
```bash
# Production docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Health checks
docker-compose exec chatbot-app curl http://localhost:8501/health
docker-compose exec fcm-service curl http://localhost:8001/health

# Monitor logs
docker-compose logs -f --tail=100
```

#### Monitoring & Maintenance
```bash
# Set up log rotation
logrotate /var/log/memory_chatbot/*.log

# Database maintenance
docker-compose exec postgres psql -U chatbot_user -d chatbot_db -c "VACUUM ANALYZE;"

# Monitor FCM service
curl http://localhost:8001/api/fcm/tokens | jq '.total_count'

# Check background service health
python -c "
from agent.bg_running.background_alert_service import get_service_status
import json
print(json.dumps(get_service_status(), indent=2))
"
```

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/yourusername/memory_chatbot.git
cd memory_chatbot

# Create development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up pre-commit hooks
pip install pre-commit
pre-commit install
```

### Development Guidelines

#### Code Quality Standards
- **Type Hints**: Use Python type hints for better code clarity
- **Documentation**: Write comprehensive docstrings for all functions and classes
- **Testing**: Add unit tests for new features using pytest
- **Code Formatting**: Use black and isort for consistent code formatting
- **Linting**: Ensure code passes flake8 and mypy checks

#### Agent Development
```python
# Example: Creating a new specialized agent
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class MyAgentState(TypedDict):
    input: str
    output: str
    error: Optional[str]

class MySpecializedAgent:
    def __init__(self, llm):
        self.llm = llm
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        graph = StateGraph(MyAgentState)
        graph.add_node("process", self._process_node)
        graph.add_edge(START, "process")
        graph.add_edge("process", END)
        return graph.compile()
```

#### Firebase Integration
```python
# Example: Adding new FCM functionality
from firebase_admin import messaging

def send_custom_notification(tokens: List[str], title: str, body: str):
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        tokens=tokens
    )
    return messaging.send_multicast(message)
```

### Testing Guidelines
```bash
# Run full test suite
pytest tests/ -v

# Test specific components
pytest tests/test_agents.py::TestUserInfoAgent
pytest tests/test_fcm_service.py::TestTokenManagement

# Integration tests
pytest tests/integration/ -v --slow
```

## 🙏 Acknowledgments

### Core Technologies
- **[LangGraph](https://langchain-ai.github.io/langgraph/)** - State-based workflow orchestration and agent management
- **[Firebase](https://firebase.google.com/)** - Real-time notifications and cloud messaging infrastructure
- **[PostgreSQL](https://www.postgresql.org/)** with **[pgvector](https://github.com/pgvector/pgvector)** - Vector database for embeddings and multi-user data
- **[FastAPI](https://fastapi.tiangolo.com/)** - High-performance API framework for FCM services
- **[Streamlit](https://streamlit.io/)** - Interactive web interface and user experience

### AI & Search Services  
- **[OpenAI](https://openai.com/)** - GPT-4o-mini language model for intelligent conversations
- **[Tavily](https://tavily.com/)** - Real-time web search API integration
- **[Model Context Protocol](https://github.com/modelcontextprotocol/servers)** - Extensible tool integration framework

### Development Tools
- **[Docker](https://docker.com/)** - Containerization and deployment orchestration
- **[SQLAlchemy](https://sqlalchemy.org/)** - Robust ORM and database relationship management
- **[Pydantic](https://pydantic.dev/)** - Data validation and structured output parsing

**Built with ❤️ Python, SQLAlchemy, LangGraph, and Streamlit**

[![GitHub](https://img.shields.io/badge/GitHub-pofmN/memory_chatbot-blue?logo=github)](https://github.com/pofmN/memory_chatbot)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red?logo=sqlalchemy)](https://sqlalchemy.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://docker.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit)](https://streamlit.io)
