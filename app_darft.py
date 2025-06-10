import streamlit as st
from dotenv import load_dotenv
from storage import DatabaseManager
from retrieve_history import retrieval_tool
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_tavily import TavilySearch
from typing import Annotated
from typing_extensions import TypedDict
from memory.chat_llms import GeminiChatbot
import os
from langchain_openai import ChatOpenAI
import uuid
# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Chatbot with Memory",
    page_icon="🤖",
    layout="wide"
)

openai_api = os.environ.get("OPENAI_API_KEY")
tavily_api = os.environ.get("TAVILY_API_KEY")

# Initialize components
@st.cache_resource
def init_components():
    db = DatabaseManager()
    llm = ChatOpenAI(
        model_name="gpt-4.1-mini", # gpt-4o, gpt-4o-mini, gpt-4.1-mini, gpt-4.1-nano, ada-2, 3-small
        temperature=0.7,
        max_tokens=1000,
        base_url="https://warranty-api-dev.picontechnology.com:8443",  # Ensure /v1 path if OpenAI-compatible
        openai_api_key=openai_api,  # Optional if handled in gateway
    )
    return db, llm

db, llm = init_components()

# Sidebar for session management
st.sidebar.title("🤖 Chat Sessions")

# Session management
if st.sidebar.button("➕ New Chat Session"):
    new_session_id = str(uuid.uuid4())
    if db.create_session(new_session_id):
        st.session_state.current_session = new_session_id
        st.session_state.messages = []
        st.rerun()

# Get all sessions
sessions = db.get_all_sessions()

if sessions:
    st.sidebar.subheader("Previous Sessions")
    for session in sessions[:10]:  # Show last 10 sessions
        session_name = f"Session {session['session_id'][:8]}..."
        message_count = session['message_count']
        updated_time = session['updated_at'].strftime("%m/%d %H:%M")
        
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            if st.button(f"{session_name}\n({message_count} msgs, {updated_time})", key=f"session_{session['session_id']}"):
                st.session_state.current_session = session['session_id']
                # Load chat history
                history = db.get_chat_history(session['session_id'])
                st.session_state.messages = [
                    {"role": msg['role'], "content": msg['content']} 
                    for msg in history
                ]
                st.rerun()
        
        with col2:
            if st.button("🗑️", key=f"delete_{session['session_id']}", help="Delete session"):
                if db.delete_session(session['session_id']):
                    if hasattr(st.session_state, 'current_session') and st.session_state.current_session == session['session_id']:
                        del st.session_state.current_session
                        st.session_state.messages = []
                    st.rerun()

# Main chat interface
st.title("🤖 AI Chatbot with Memory")
st.markdown("*This chatbot remembers our conversation history using PostgreSQL database*")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_session" not in st.session_state:
    # Create a new session
    session_id = str(uuid.uuid4())
    if db.create_session(session_id):
        st.session_state.current_session = session_id

# Display current session info
if hasattr(st.session_state, 'current_session'):
    st.info(f"📝 Current Session: {st.session_state.current_session[:8]}...")

# Display chat messages
chat_container = st.container()
with chat_container:
    if not st.session_state.messages:
        # Show welcome message
        welcome_msg = "Xin chào! Tôi là trợ lý AI của bạn. Tôi có thể giúp bạn hôm nay?"
        st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
        # Display welcome message
        st.chat_message("assistant").write(welcome_msg)
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

search_tool = {
    "type": "function",
    "function": {
        "name": "search",
        "description": "Search the internet for current information on a topic",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    },
    "implementation": TavilySearch(max_results=3)
}

retrieve_tool = {
    "type": "function",
    "function": {
        "name": "retrieve_history",
        "description": "Retrieves past conversation history to provide context",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string", 
                    "description": "What information to look for in the history"
                }
            },
            "required": ["query"]
        }
    },
    "implementation": retrieval_tool
}

tools =[search_tool, retrieve_tool]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State) -> str:
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}

tool_node = ToolNode(tools=[search_tool["implementation"], retrieve_tool["implementation"]])

graph_builder.add_node("tools", tool_node)
graph_builder.add_node("chatbot", chatbot)

graph_builder.add_edge(START, "chatbot")

# Define the condition for using the tool
graph_builder.add_conditional_edges("chatbot", tools_condition)

graph_builder.add_edge("tools", "chatbot")
graph = graph_builder.compile()

def stream_graph_update(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for key, value in event.items():
            # Only print messages from the chatbot node, not from tools
            if key == "chatbot" and "messages" in value and len(value["messages"]) > 0:
                print("Assistant:", value["messages"][-1].content)


# Chat input
if user_input := st.chat_input("Type your message here..."):

    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    # Save user message to database
    if hasattr(st.session_state, 'current_session'):
        db.save_message(st.session_state.current_session, "user", user_input)
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Get chat history for context
            for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
                for key, value in event.items():
                    # Only print messages from the chatbot node, not from tools
                    if key == "chatbot" and "messages" in value and len(value["messages"]) > 0:
                        response = value["messages"][-1].content
                        print("Assistant:", response)
            st.write(response)
    
    # Add assistant response to chat
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Save assistant message to database
    if hasattr(st.session_state, 'current_session'):
        db.save_message(st.session_state.current_session, "assistant", response)

# Footer
st.markdown("---")
st.markdown("**Tech Stack:** Streamlit + PostgreSQL + Docker + Gemini 2.0 Flash")

# Database connection status
try:
    conn = db.get_connection()
    if conn:
        conn.close()
        st.sidebar.success("✅ Database Connected")
    else:
        st.sidebar.error("❌ Database Connection Failed")
except:
    st.sidebar.error("❌ Database Connection Failed")