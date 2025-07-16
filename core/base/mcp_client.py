import asyncio
import json
import os
import uuid
from typing import Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
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
        
    async def add_event(self, user_input: str) -> str:
        """Add an event to the MCP server."""
        try:
            async with asyncio.timeout(15):
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        print("session initialized")
                        result = await session.call_tool(
                            "add_event",
                            arguments={"user_input": user_input}
                        )
                        print("result:", result)
                        if hasattr(result, 'content') and result.content:
                            content = result.content[0] if isinstance(result.content, list) else result.content
                            return content.text if hasattr(content, 'text') else str(content)
                        else:
                            return "Event added successfully."
        except Exception as e:
            return f"Error adding event at mcp client: {str(e)}"
        
    async def add_activity(self, user_input: str) -> str:
        """Add an activity to the MCP server."""
        try:
            async with asyncio.timeout(15):
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        result = await session.call_tool(
                            "add_activity",
                            arguments={"user_input": user_input}
                        )
                        
                        if hasattr(result, 'content') and result.content:
                            content = result.content[0] if isinstance(result.content, list) else result.content
                            return content.text if hasattr(content, 'text') else str(content)
                        else:
                            return "Activity added successfully."
        except Exception as e:
            return f"Error adding activity: {str(e)}"   
            

def init_mcp_client() -> MCPClient:
    """Initialize MCP client"""
    if os.path.exists('/app/mcp/server.py'):
        MCP_SERVER_PATH = '/app/mcp/server.py'
    else:
        # Local development path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        MCP_SERVER_PATH = os.path.join(project_root, "mcp", "server.py")
    
    if not os.path.exists(MCP_SERVER_PATH):
        raise FileNotFoundError(f"MCP server not found at: {MCP_SERVER_PATH}")
    
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
    
def add_event_information(user_input:str, mcp_client: MCPClient) -> str:
    
    """Add an event to the MCP server."""
    try:
        event_info = asyncio.run(mcp_client.add_event(user_input))
        return event_info
    except Exception as e:
        return f"Error adding event: {str(e)}"
    
def add_activity_information(user_input: str, mcp_client: MCPClient) -> str:
    """Add an activity to the MCP server."""
    try:
        activity_info = asyncio.run(mcp_client.add_activity(user_input))
        return activity_info
    except Exception as e:
        return f"Error adding activity: {str(e)}"

def initialize_session(db):
    """Initialize single persistent session"""
    if "single_session_id" not in st.session_state:
        sessions = db.get_all_sessions()
        if sessions:
            print(f"✅ Found existing session: {sessions[0]['session_id']}")
            st.session_state.single_session_id = sessions[0]['session_id']
            history = db.get_chat_history(st.session_state.single_session_id)
            st.session_state.messages = [
                {"role": msg['role'], "content": msg['content']}
                for msg in history
            ]
        else:
            print("❌ No existing session found, creating a new one")
            new_session_id = str(uuid.uuid4())
            if db.create_session(new_session_id):
                st.session_state.single_session_id = new_session_id
                st.session_state.messages = []

def initialize_messages():
    """Initialize messages in session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []

