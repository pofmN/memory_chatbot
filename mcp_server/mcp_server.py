import os
import uvicorn
from fastmcp import FastMCP
from tavily import TavilyClient
from pydantic import BaseModel
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.storage import DatabaseManager
from database.storage import DatabaseManager
from typing import Optional, List
from extract_user_info import save_user_information
import json

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY not found in .env file")

db = DatabaseManager()
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# Define the search result model
class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    score: float

class SearchResponse(BaseModel):
    status: str
    results: List[SearchResult]
    timestamp: str


mcp = FastMCP("Web Search, Retrieve Server")

@mcp.tool()
async def search_web(query: str, max_results: int = 5, search_depth: str = "basic") -> SearchResponse:
    try:
        response = tavily_client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth
        )
        results = [
            SearchResult(
                title=result["title"],
                url=result["url"],
                content=result["content"],
                score=result.get("score", 0.0)
            )
            for result in response["results"]
        ]
        return SearchResponse(
            status="success",
            results=results,
            timestamp=str(response.get("timestamp", ""))
        )
    except Exception as e:
        return SearchResponse(
            status="error",
            results=[],
            timestamp=str(e)
        )
    
@mcp.tool()
async def get_history_summary(session_id: str) -> str:
    """
    Retrieve the summary of a chat session by its ID.
    """
    session = db.get_all_sessions()
    if not session:
        return "No sessions found."
    summary = db.get_session_summary(session_id)
    if not summary:
        return "No summary available for this session."
    if isinstance(summary, list):
        summary = " ".join(str(item) for item in summary)
    else:
        summary = str(summary)

    return f"Summary for session {summary}"

@mcp.tool()
async def add_user_info(user_input: str) -> str:
    """
    Extract user information from the input string.
    
    Args:
        user_input (str): The input string containing user information.
        
    Returns:
        dict: Extracted user information as a dictionary
    """
    try:    
        user_info = save_user_information(user_input)
    except json.JSONDecodeError as e:
        return {
            "error": str(e),
            "response": "Failed to extract user information."
        }

    return user_info

@mcp.tool()
async def test_mcp_server() -> str:
    """
    A simple test tool to check if the MCP server is running.
    """
    return "MCP server is running successfully!"

if __name__ == "__main__":
    mcp.run(transport="stdio")
