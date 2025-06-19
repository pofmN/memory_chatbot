from mcp import stdio_client, ClientSession, StdioServerParameters
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
import asyncio

server_params = StdioServerParameters(
    command="python",
    args=["/Users/nam.pv/Documents/work-space/memory_chat/mcp_server/mcp_server.py"]
)

async def test_mcp_server():
    """
    A simple test tool to check if the MCP server is running.
    """
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                print("Tools loaded successfully:", tools)
                return f"MCP server is running successfully with {tools}"
    except Exception as e:
        return f"Error connecting to MCP server: {str(e)}"

asyncio.run(test_mcp_server())