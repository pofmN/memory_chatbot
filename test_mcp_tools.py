import streamlit as st
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import os
from core.base.storage import DatabaseManager
from langchain_openai import ChatOpenAI
from agent.recommendation.services import update_alert_status
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

# class MCPClient():
#     def __init__(self, server_path: str):
#         self.server_path = server_path
#         self.server_params = StdioServerParameters(
#             command="python",
#             args=[server_path]
#         )
        
#     async def add_user_info(self, user_input: str) -> str:
#         """
#         Add user information to the MCP server.
#         """
#         try:
#             async with asyncio.timeout(15):
#                 async with stdio_client(self.server_params) as (read, write):
#                     async with ClientSession(read, write) as session:
#                         await session.initialize()
                        
#                         result = await session.call_tool(
#                             "add_user_info",
#                             arguments={"user_input": user_input}
#                         )
                        
#                         if hasattr(result, 'content') and result.content:
#                             content = result.content[0] if isinstance(result.content, list) else result.content
#                             return content.text if hasattr(content, 'text') else str(content)
#                         else:
#                             return "User information updated successfully."
                            
#         except asyncio.TimeoutError:
#             return "MCP server request timed out"
#         except asyncio.CancelledError:
#             return "MCP operation was cancelled"
#         except Exception as e:
#             return f"Error updating user information: {str(e)}"
        
#     async def add_activity(self, user_input: str) -> str:
#         """
#         Add an activity to the MCP server.
        
#         Args:
#             user_input (str): The user input containing activity details.
        
#         Returns:
#             str: Confirmation message or error message.
#         """
#         try:
#             async with asyncio.timeout(15):
#                 async with stdio_client(self.server_params) as (read, write):
#                     async with ClientSession(read, write) as session:
#                         await session.initialize()
                        
#                         result = await session.call_tool(
#                             "add_activity",
#                             arguments={"user_input": user_input}
#                         )
                        
#                         if hasattr(result, 'content') and result.content:
#                             content = result.content[0] if isinstance(result.content, list) else result.content
#                             return content.text if hasattr(content, 'text') else str(content)
#                         else:
#                             return "Activity added successfully."
                            
#         except asyncio.TimeoutError:
#             return "MCP server request timed out"
#         except asyncio.CancelledError:
#             return "MCP operation was cancelled"
#         except Exception as e:
#             return f"Error adding activity: {str(e)}"
        
# MCP_SERVER_PATH = "/Users/nam.pv/Documents/work-space/memory_chat/mcp/server.py"
# mcp_client = MCPClient(MCP_SERVER_PATH)


# def add_activity_information(user_input: str) -> str:
#     """
#     Add an activity to the MCP server.
    
#     Args:
#         user_input (str): The user input containing activity details.
    
#     Returns:
#         str: Confirmation message or error message.
#     """
#     return asyncio.run(mcp_client.add_activity(user_input))


# user_input = "tôi sẽ vui chơi với gia đình vào 8h tối hằng ngày"
# user_activity_info = add_activity_information(user_input)
# print(f"User Activity Info: {user_activity_info}")

import random
import asyncio
from plyer import notification
from desktop_notifier import DesktopNotifier # working solution
from notifiers import notify
import pync


# 2. Change the function definition to be async
async def show_daily_recommendation():
    """
    Displays a notification using the desktop-notifier library.
    """
    print("Generating daily recommendation...")
    recommendations = [
        "Take a 5-minute break to stretch.",
        "Review your top priority for the day.",
        "Drink a glass of water.",
        "Think of one thing you're grateful for.",
        "Close unused tabs and apps."
    ]
    
    message = random.choice(recommendations)
    title = "Daily Recommendation ✨"
    pync.notify(
        title=title,
        message=message,
    )    


def test_alert(title: str, message: str):
    print(f"Test Alert - Title: {title}, Message: {message}")
    """Test function to send an alert notification."""
    asyncio.run(show_daily_recommendation())

