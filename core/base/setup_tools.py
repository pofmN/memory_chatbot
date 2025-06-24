import asyncio
from langchain_tavily import TavilySearch
from langchain.tools import StructuredTool
from core.base.mcp_client import MCPClient


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
