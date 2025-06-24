import asyncio
import json
import os
import uuid
from typing import Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_tavily import TavilySearch
from langchain.tools import StructuredTool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing import Annotated
from typing_extensions import TypedDict
from ui.ui_components import generate_custom_system_prompt, get_personality_presets
import streamlit as st

class MCPClient():
    def __init__(self, server_path: str):
        self.server_path = server_path
        self.server_params = StdioServerParameters(
            command="python",
            args=[server_path]
        )

    async def get_history_summary(self, session_id: str) -> str:
        """Retrieve the summary of a chat session by its ID."""
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
                            return content.text if hasattr(content, 'text') else str(content)
                        else:
                            return "No summary available for this session."
                            
        except Exception as e:
            return f"Error retrieving summary: {str(e)}"
        
    async def add_user_info(self, user_input: str) -> str:
        """Add user information to the MCP server."""
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
                            
        except Exception as e:
            return f"Error updating user information: {str(e)}"

def init_mcp_client() -> MCPClient:
    """Initialize MCP client"""
    MCP_SERVER_PATH = "/Users/nam.pv/Documents/work-space/memory_chat/mcp/server.py"
    return MCPClient(MCP_SERVER_PATH)

def mcp_history_tool(session_id: str, mcp_client: MCPClient) -> str:
    """Retrieve the summary of a chat session by its ID."""
    try:
        summary = asyncio.run(mcp_client.get_history_summary(session_id))
        return summary
    except Exception as e:
        return f"Error retrieving session summary: {str(e)}"

def update_user_information(user_input: str, mcp_client: MCPClient) -> str:
    """Update user information in the database."""
    try:
        user_info = asyncio.run(mcp_client.add_user_info(user_input))
        return user_info
    except Exception as e:
        return f"Error updating user information: {str(e)}"

def initialize_session(db):
    """Initialize single persistent session"""
    if "single_session_id" not in st.session_state:
        sessions = db.get_all_sessions()
        if sessions:
            st.session_state.single_session_id = sessions[0]['session_id']
            history = db.get_chat_history(st.session_state.single_session_id)
            st.session_state.messages = [
                {"role": msg['role'], "content": msg['content']} 
                for msg in history
            ]
        else:
            new_session_id = str(uuid.uuid4())
            if db.create_session(new_session_id):
                st.session_state.single_session_id = new_session_id
                st.session_state.messages = []

def initialize_messages():
    """Initialize messages in session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []

## Converted to another file
def setup_tools(mcp_client: MCPClient) -> list:
    """Setup and return all tools"""
    search_tool = TavilySearch(max_results=3)

    retrieve_tool = StructuredTool.from_function(
        func=lambda session_id: mcp_history_tool(session_id, mcp_client),
        name="retrieve_chat_history",
        description="""Use this tool when the user asks about previous messages, past conversations, personal information, 
        or mentions something discussed earlier. This tool retrieves relevant parts of the conversation history to help you answer questions about past interactions.
        If there is useful information in the chat history, answer based on that information no creative.""",
        args_schema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The id of the chat session to retrieve history from."
                }
            },
            "required": ["session_id"]
        },
    )

    extract_user_info_tool = StructuredTool.from_function(
        func=lambda user_input: update_user_information(user_input, mcp_client),
        name="extract_user_info",
        description="""Use this tool to extract user information from the input string, even lack of field. 
        Here is table schema: user_profile(id, user_name, phone_number, year_of_birth, address, major, additional_info, created_at, updated_at)
        
        - user_name: Required unique display name (VARCHAR 100)
        - phone_number: Optional contact number (VARCHAR 20) 
        - year_of_birth: Optional birth year (INTEGER)
        - address: Optional residence/location (TEXT)
        - major: Optional field of study/profession (VARCHAR 100)
        - additional_info: Optional extra details (TEXT)
        
        Extract and save user information to database.""",
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

    return [search_tool, retrieve_tool, extract_user_info_tool]

def get_user_profile_context(db) -> str:
    """Retrieve user profile data and format it as context for the chatbot."""
    try:
        user_profile = db.get_user_profile()
        
        profile_context = ""
        if user_profile:
            profile_context = f"""
USER PROFILE INFORMATION:
- Name: {user_profile.get('user_name', 'Not provided')}
- Phone: {user_profile.get('phone_number', 'Not provided')}
- Year of Birth: {user_profile.get('year_of_birth', 'Not provided')}
- Address: {user_profile.get('address', 'Not provided')}
- Major/Field: {user_profile.get('major', 'Not provided')}
- Additional Info: {user_profile.get('additional_info', 'Not provided')}"""
        else:
            profile_context = "\nUSER PROFILE: No user profile information available yet."
        
        # Get personality presets for fallback
        personality_presets = get_personality_presets()
        
        # Generate custom system prompt based on session state
        custom_prompt = generate_custom_system_prompt(
            st.session_state.get('personality_prompt', personality_presets['Friendly Assistant']),
            st.session_state.get('communication_style', 'Conversational'),
            st.session_state.get('response_length', 'Balanced'),
            st.session_state.get('language_pref', 'Vietnamese'),
            st.session_state.get('special_instructions', '')
        )
        
        return f"""{custom_prompt}

{profile_context}

Use the user profile information to personalize your responses when relevant. Be natural and conversational."""
        
    except Exception as e:
        print(f"Error retrieving user profile: {e}")
        return "\nUSER PROFILE: Error retrieving profile information.\n"

class State(TypedDict):
    messages: Annotated[list, add_messages]
    session_id: str

def create_chatbot_function(db, llm_with_tools):
    """Create chatbot function with dependencies"""
    def chatbot(state: State) -> dict:
        """Chatbot function that uses session state values"""
        
        user_info = get_user_profile_context(db)
        messages = state["messages"].copy()
        
        # Create system message with custom prompt and user profile
        system_message = {
            "role": "system", 
            "content": user_info
        }

        messages.insert(0, system_message)
        
        # Debug: Print current settings
        print("="*50)
        print("Current Settings:")
        print(f"Personality: {st.session_state.get('selected_personality', 'Not set')}")
        print(f"Style: {st.session_state.get('communication_style', 'Not set')}")
        print(f"Length: {st.session_state.get('response_length', 'Not set')}")
        print(f"Language: {st.session_state.get('language_pref', 'Not set')}")
        print(f"Instructions: {st.session_state.get('special_instructions', 'Not set')}")
        print("="*50)
        
        response = llm_with_tools.invoke(messages)
        
        # Handle tool calls (session_id injection)
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call.get('name') == 'retrieve_chat_history':
                    if 'args' not in tool_call:
                        tool_call['args'] = {}
                    tool_call['args']['session_id'] = state.get("session_id")
        
        return {"messages": state["messages"] + [response]}
    
    return chatbot

def setup_graph(db, llm):
    """Setup and return the LangGraph"""
    mcp_client = init_mcp_client()
    tools = setup_tools(mcp_client)
    llm_with_tools = llm.bind_tools(tools)
    
    graph_builder = StateGraph(State)
    
    chatbot_function = create_chatbot_function(db, llm_with_tools)
    tool_node = ToolNode(tools=tools)
    
    graph_builder.add_node("chatbot", chatbot_function)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    graph_builder.add_edge("tools", "chatbot")
    
    return graph_builder.compile()
