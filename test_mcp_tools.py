import streamlit as st
from dotenv import load_dotenv
from typing_extensions import TypedDict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import json
import os
from database.storage import DatabaseManager
from langchain_openai import ChatOpenAI
from extract_user_info import save_user_information
import uuid
# Load environment variables
load_dotenv()
openai_api = os.environ.get("OPENAI_API_KEY")
db = DatabaseManager()

llm = ChatOpenAI(
        model_name="gpt-4o-mini", # gpt-4o, gpt-4o-mini, gpt-4.1-mini, gpt-4.1-nano, ada-2, 3-small
        temperature=0.2,
        max_tokens=1000,
        base_url="https://warranty-api-dev.picontechnology.com:8443",  # Ensure /v1 path if OpenAI-compatible
        openai_api_key=openai_api,
    )

class MCPClient():
    def __init__(self, server_path: str):
        self.server_path = server_path
        self.server_params = StdioServerParameters(
            command="python",
            args=[server_path]
        )
        
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


def update_user_information(user_input: str):
    """
    Update user information in the database.
    """
    try:
        user_input = asyncio.run(mcp_client.add_user_info(user_input))
        return user_input
    except Exception as e:
        return f"Error updating user information: {str(e)}"


# user_input = "my name is Pham Van Nam, i was born in 2003, now i student in DaNang and intern in HBG company"
# user_info = update_user_information(user_input)
# print("User information updated:", user_info)