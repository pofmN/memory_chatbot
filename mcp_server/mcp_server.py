import os
import uvicorn
from fastmcp import FastMCP
from tavily import TavilyClient
from pydantic import BaseModel
from dotenv import load_dotenv
# Add parent directory to path to import storage
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage import DatabaseManager
from storage import DatabaseManager
from typing import Optional, List
import json

# Load environment variables
load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY not found in .env file")

# Initialize Tavily client
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


# Initialize FastMCP
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
async def test_mcp_server() -> str:
    """
    A simple test tool to check if the MCP server is running.
    """
    return "MCP server is running successfully!"

if __name__ == "__main__":
    # uvicorn.run(mcp.app, host="0.0.0.0", port=8000)
    mcp.run(transport="stdio")
