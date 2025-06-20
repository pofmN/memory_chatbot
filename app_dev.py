import streamlit as st
from dotenv import load_dotenv
from database.storage import DatabaseManager
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_tavily import TavilySearch
from langchain.tools import StructuredTool
from typing import Annotated
from typing_extensions import TypedDict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import json
import os
from langchain_openai import ChatOpenAI
import uuid
# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="AI Chatbot with Memory",
    page_icon="🤖",
    layout="wide"
)

openai_api = os.environ.get("OPENAI_API_KEY")
tavily_api = os.environ.get("TAVILY_API_KEY")

@st.cache_resource
def init_components():
    db = DatabaseManager()
    llm = ChatOpenAI(
        model_name="gpt-4o-mini", # gpt-4o, gpt-4o-mini, gpt-4.1-mini, gpt-4.1-nano, ada-2, 3-small
        temperature=0.2,
        max_tokens=1000,
        base_url="https://warranty-api-dev.picontechnology.com:8443",  # Ensure /v1 path if OpenAI-compatible
        openai_api_key=openai_api,
    )
    return db, llm

db, llm = init_components()

st.sidebar.title("🤖 Chat Sessions")

if st.sidebar.button("➕ New Chat Session"):
    new_session_id = str(uuid.uuid4())
    if db.create_session(new_session_id):
        st.session_state.current_session = new_session_id
        st.session_state.messages = []
        st.rerun()

sessions = db.get_all_sessions()

class MCPClient():
    def __init__(self, server_path: str):
        self.server_path = server_path
        self.server_params = StdioServerParameters(
            command="python",
            args=[server_path]
        )
        
    async def get_history_summary(self, session_id: str) -> str:
        """
        Retrieve the summary of a chat session by its ID with improved error handling.
        """
        try:
            async with asyncio.timeout(15):
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        result = await session.call_tool(
                            "get_history_summary",
                            arguments={"session_id": session_id}
                        )
                        
                        if hasattr(result, 'content') and result.content:
                            content = result.content[0] if isinstance(result.content, list) else result.content
                            if hasattr(content, 'text'):
                                return content.text
                            else:
                                return str(content)
                        else:
                            return "No summary available for this session."
                            
        except asyncio.TimeoutError:
            return "MCP server request timed out"
        except asyncio.CancelledError:
            return "MCP operation was cancelled"
        except Exception as e:
            return f"Error retrieving summary: {str(e)}"
        
    async def add_user_info(self, user_input: str) -> str:
        """
        Add user information to the MCP server.
        """
        try:
            async with asyncio.timeout(15):
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        result = await session.call_tool(
                            "add_user_info",
                            arguments={"user_input": user_input}
                        )
                        
                        if hasattr(result, 'content') and result.content:
                            content = result.content[0] if isinstance(result.content, list) else result.content
                            return content.text if hasattr(content, 'text') else str(content)
                        else:
                            return "User information updated successfully."
                            
        except asyncio.TimeoutError:
            return "MCP server request timed out"
        except asyncio.CancelledError:
            return "MCP operation was cancelled"
        except Exception as e:
            return f"Error updating user information: {str(e)}"
        
MCP_SERVER_PATH = "/Users/nam.pv/Documents/work-space/memory_chat/mcp_server/mcp_server.py"
mcp_client = MCPClient(MCP_SERVER_PATH)


# async def async_mcp_history(session_id: str):
#     return await mcp_client.get_history_summary(session_id)
    
def mcp_history_tool(session_id: str) -> str:
    """
    Retrieve the summary of a chat session by its ID.
    """
    try:
        summary = asyncio.run(mcp_client.get_history_summary(session_id))
        return summary
    except Exception as e:
        return f"Error retrieving session summary: {str(e)}"

def update_user_information(user_input: str) -> str:
    """
    Update user information in the database.
    """
    try:
        user_info = asyncio.run(mcp_client.add_user_info(user_input))
        return user_info
    except Exception as e:
        return f"Error updating user information: {str(e)}"

if sessions:
    st.sidebar.subheader("Previous Sessions")
    for session in sessions[:10]:
        session_name = f"Session {session['session_id'][:8]}..."
        message_count = session['message_count']
        updated_time = session['last_updated'].strftime("%m/%d %H:%M")
        
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            if st.button(f"{session_name}\n({message_count} msgs, {updated_time})", key=f"session_{session['session_id']}"):
                st.session_state.current_session = session['session_id']
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

st.title("🤖 AI Chatbot with Memory")
st.markdown("*This chatbot remembers our conversation history using PostgreSQL database*")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_session" not in st.session_state:
    session_id = str(uuid.uuid4())
    if db.create_session(session_id):
        st.session_state.current_session = session_id

if hasattr(st.session_state, 'current_session'):
    st.info(f"📝 Current Session: {st.session_state.current_session[:8]}...")

# Display chat messages
chat_container = st.container()
with chat_container:
    if not st.session_state.messages:
        welcome_msg = "Xin chào! Tôi là trợ lý AI của bạn. Tôi có thể giúp bạn hôm nay?"
        st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
        st.chat_message("assistant").write(welcome_msg)
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

class State(TypedDict):
    messages: Annotated[list, add_messages]
    session_id: str

graph_builder = StateGraph(State)

search_tool = TavilySearch(max_results=3)

retrieve_tool = StructuredTool.from_function(
    func=mcp_history_tool,
    name="retrieve_chat_history",
    description="""Use this tool when the user asks about previous messages, past conversations, personal information, 
    or mentions something discussed earlier. This tool retrieves relevant parts of the conversation history to help you answer questions about past interactions.
    If there is useful information in the chat history, answer base on that information no creative.""",
    args_schema={
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "The id of the chat session to retrieve history from. This is used to fetch relevant past messages for context."
            }
        },
        "required": ["session_id"]
    },
)

extract_user_info_tool = StructuredTool.from_function(
    func=update_user_information,
    name="extract_user_info",
    description="""Use this tool to extract user information from the input string, even lack of field. 
    Here is table schema: user_profile(id, user_name, phone_number, year_of_birth, address, major, additional_info, created_at, updated_at)
    
    - user_name: Required unique display name (VARCHAR 100)
    - phone_number: Optional contact number (VARCHAR 20) 
    - year_of_birth: Optional birth year (INTEGER)
    - address: Optional residence/location (TEXT)
    - major: Optional field of study/profession (VARCHAR 100)
    - additional_info: Optional extra details (TEXT)Save user information to database
    It returns a structured JSON object with user details.""",
    args_schema={
        "type": "object",
        "properties": {
            "user_input": {
                "type": "string",
                "description": "The input string containing user information."
            }
        },
        "required": ["user_input"]
    },
)

tools =[search_tool, retrieve_tool, extract_user_info_tool]
llm_with_tools = llm.bind_tools(tools)


def get_user_profile_context() -> str:
    """
    Retrieve user profile data and format it as context for the chatbot.
    """
    try:
        user_profile = db.get_user_profile()
        
        if user_profile:
            context = f"""
USER PROFILE INFORMATION:
- Name: {user_profile.get('user_name', 'Not provided')}
- Phone: {user_profile.get('phone_number', 'Not provided')}
- Year of Birth: {user_profile.get('year_of_birth', 'Not provided')}
- Address: {user_profile.get('address', 'Not provided')}
- Major/Field: {user_profile.get('major', 'Not provided')}
- Additional Info: {user_profile.get('additional_info', 'Not provided')}

Use this information to personalize your responses when relevant. Be natural and conversational.
"""
            return context
        else:
            return "\nUSER PROFILE: No user profile information available yet.\n"
    except Exception as e:
        print(f"Error retrieving user profile: {e}")
        return "\nUSER PROFILE: Error retrieving profile information.\n"


def chatbot(state: State) -> dict:
    user_info = get_user_profile_context()
    messages = state["messages"].copy()
    
    # Create system message with user profile
    system_message = {
        "role": "system", 
        "content": f"""You are a helpful AI assistant. {user_info}

Always use the user profile information when it's relevant to personalize your responses. 
If the user asks about their information or anything related to their profile, refer to the data above.
Be natural and conversational."""
    }

    messages.insert(0, system_message)
    
    # ✅ Invoke LLM with enriched messages
    response = llm_with_tools.invoke(messages)
    
    # Handle tool calls (session_id injection)
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call.get('name') == 'retrieve_chat_history':
                if 'args' not in tool_call:
                    tool_call['args'] = {}
                tool_call['args']['session_id'] = state.get("session_id")
    
    return {"messages": state["messages"] + [response]}

def review_response(state: State) -> str:
    response = state(["messages"][-1].content)
    #nomnom
    return response

tool_node = ToolNode(tools=tools)

graph_builder.add_node("chatbot", chatbot)

graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")

graph_builder.add_conditional_edges("chatbot", tools_condition)

graph_builder.add_edge("tools", "chatbot")
graph = graph_builder.compile()

# Chat input
if user_input := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    session_id = st.session_state.get('current_session', None)
    if session_id:
        db.save_message(session_id, "user", user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            all_responses = []  # ✅ Collect all responses
            
            for event in graph.stream({
                "messages": [{"role": "user", "content": user_input}], 
                "session_id": session_id
            }):
                for key, value in event.items():
                    print(f"📊 Event: {key}")
                    
                    if key == "chatbot" and "messages" in value and len(value["messages"]) > 0:
                        last_message = value["messages"][-1]
                        if hasattr(last_message, 'content') and last_message.content:
                            all_responses.append({
                                'content': last_message.content,
                                'has_tool_calls': hasattr(last_message, 'tool_calls') and bool(last_message.tool_calls)
                            })
            
            # ✅ Use the LAST response (which should include tool results)
            if all_responses:
                final_response = all_responses[-1]['content']
                print(f"✅ Using final response: {final_response[:100]}...")
                
                st.session_state.messages.append({"role": "assistant", "content": final_response})
                st.write(final_response)
                
                if session_id:
                    db.save_message(session_id, "assistant", final_response)
            else:
                st.error("❌ No response generated.")
    

st.markdown("---")
st.markdown("**Tech Stack:** Streamlit + PostgreSQL + Docker + Gemini 2.0 Flash")

try:
    conn = db.get_connection()
    if conn:
        conn.close()
        st.sidebar.success("✅ Database Connected")
    else:
        st.sidebar.error("❌ Database Connection Failed")
except:
    st.sidebar.error("❌ Database Connection Failed")