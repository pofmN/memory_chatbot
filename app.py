import streamlit as st
from dotenv import load_dotenv
from core.base.storage import DatabaseManager
from langgraph.graph import StateGraph, START
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
        model_name="gpt-4o", # gpt-4o, gpt-4o-mini, gpt-4.1-mini, gpt-4.1-nano, ada-2, 3-small
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

    # async def search_web(self, query: str, max_results: int = 3, search_depth: str = "basic") -> dict:
    #     """
    #     Send a search query to the MCP server and return the response.
    #     """
    #     try:
    #         async with stdio_client(self.server_params) as (read, write):
    #             async with ClientSession(read, write) as session:
    #                 await session.initialize()
    #                 result = await session.call_tool(
    #                     "search_web",
    #                     arguments={
    #                         "query": query,
    #                         "max_results": max_results,
    #                         "search_depth": search_depth
    #                     }
    #                 )
    #                 if hasattr(result, 'content') and result.content:
    #                     content = result.content[0] if isinstance(result.content, list) else result.content
    #                     return json.loads(content.text) if hasattr(content, 'text') else content
    #                 else:
    #                     return {"status": "error", "results": [], "timestamp": "No content in response"}
    #     except Exception as e:
    #         return {"status": "error", "results": [], "timestamp": str(e)}
        
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
        
MCP_SERVER_PATH = "/Users/nam.pv/Documents/work-space/memory_chat/mcp_server/mcp_server.py"
mcp_client = MCPClient(MCP_SERVER_PATH)

# async def async_mcp_search(query: str, max_results: int = 3):
#     """
#     Search the web using the MCP server.
#     """
#     response = mcp_client.search_web(query, max_results)
#     if response.get("status") == "success":
#             formatted_results = []
#             for item in response.get("results", []):
#                 formatted_results.append(
#                     {
#                         "title": item.get("title", "No title"),
#                         "url": item.get("url", "No URL"),
#                         "content": item.get("content", "No content"),
#                         "score": item.get("score", 0.0)
#                     }
#                 )
#             response = "/n".join(formatted_results)
#     else:
#         response = "Error while searching the web."
#     return response


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

if sessions:
    st.sidebar.subheader("Previous Sessions")
    for session in sessions[:10]:
        session_name = f"Session {session['session_id'][:8]}..."
        message_count = session['message_count']
        updated_time = session['updated_at'].strftime("%m/%d %H:%M")
        
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
    description="Use this tool when the user asks about previous messages, past conversations, personal information, or mentions something discussed earlier. This tool retrieves relevant parts of the conversation history to help you answer questions about past interactions.",
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
tools =[search_tool, retrieve_tool]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State) -> str:
    response = llm_with_tools.invoke(state["messages"])
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call.get('name') == 'retrieve_chat_history':
                if 'args' not in tool_call:
                    tool_call['args'] = {}
                tool_call['args']['session_id'] = state.get("session_id")
    return {"messages": state["messages"] + [response]}

def review_response(state: State) -> str:
    response = state(["messages"][-1].content)
    
    return response

tool_node = ToolNode(tools=[search_tool, retrieve_tool])

graph_builder.add_node("tools", tool_node)
graph_builder.add_node("chatbot", chatbot)

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
        db.save_message(st.session_state.current_session, "user", user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            for event in graph.stream({"messages": [{"role": "user", "content": user_input}], "session_id": session_id}):
                for key, value in event.items():
                    # Only print messages from the chatbot node, not from tools
                    if key == "chatbot" and "messages" in value and len(value["messages"]) > 0:
                        response = value["messages"][-1].content
                        print("Assistant:", response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
            st.write(response)
    
    
    if hasattr(st.session_state, 'current_session'):
        db.save_message(st.session_state.current_session, "assistant", response)

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