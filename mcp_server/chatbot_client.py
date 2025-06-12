import asyncio
import json
from typing import Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Path to your MCP server
MCP_SERVER_PATH = "/Users/nam.pv/Documents/work-space/memory_chat/mcp_server/mcp_server.py"


server_params = StdioServerParameters(
    command="python",
    args=[MCP_SERVER_PATH]
)

async def send_search_query(query: str, max_results: int = 5, search_depth: str = "basic") -> Dict[str, Any]:
    """
    Send a search query to the MCP server and return the response.
    """
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "search_web",
                    arguments={
                        "query": query,
                        "max_results": max_results,
                        "search_depth": search_depth
                    }
                )
                
                if hasattr(result, 'content') and result.content:
                    # If content is a list, get the first item
                    content = result.content[0] if isinstance(result.content, list) else result.content
                    # If content has text attribute, use it; otherwise use the content directly
                    if hasattr(content, 'text'):
                        return json.loads(content.text)
                    else:
                        return content
                else:
                    return {"status": "error", "results": [], "timestamp": "No content in response"}
                    
    except Exception as e:
        return {"status": "error", "results": [], "timestamp": str(e)}

def display_results(response: Dict[str, Any]):
    """
    Display search results in a readable format.
    """
    if response.get("status") == "success" and response.get("results"):
        print("\nSearch Results:")
        print("=" * 50)
        for idx, result in enumerate(response["results"], 1):
            print(f"\n{idx}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   Snippet: {result['content']}...")
            if len(result['content']) > 200:
                print("   ...")
            print(f"   Score: {result['score']:.2f}")
            print("-" * 40)
    else:
        error_msg = response.get("timestamp", "Unknown error")
        print(f"\nNo results found or an error occurred: {error_msg}")

async def interactive_search():
    """
    Run the interactive search interface.
    """
    print("Welcome to the Tavily Search Chatbot! Type 'exit' to quit.")
    print("You can also use commands like:")
    print("  - 'settings' to change search parameters")
    print("  - 'help' for more options")
    print("  - 'get_history_summary' to fetch chat history")
    print("  - 'test' to test connection to MCP server")
    print("  - 'bye' to exit the program")
    
    max_results = 5
    search_depth = "basic"
    
    while True:
        try:
            query = input(f"\n[Results: {max_results}, Depth: {search_depth}] Enter your search query: ").strip()
            
            if query.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break
                
            elif query.lower() == "settings":
                print(f"\nCurrent settings:")
                print(f"  Max Results: {max_results}")
                print(f"  Search Depth: {search_depth}")
                
                try:
                    new_max = input(f"Enter max results (current: {max_results}): ").strip()
                    if new_max:
                        max_results = int(new_max)
                        
                    new_depth = input(f"Enter search depth - basic/advanced (current: {search_depth}): ").strip()
                    if new_depth.lower() in ["basic", "advanced"]:
                        search_depth = new_depth.lower()
                except ValueError:
                    print("Invalid input, keeping current settings.")
                continue
                
            elif query.lower() == "help":
                print("\nAvailable commands:")
                print("  - Type any search query to search")
                print("  - 'settings' - Change search parameters")
                print("  - 'exit/quit/bye' - Exit the program")
                print("  - 'help' - Show this help message")
                continue
            
            elif query.lower() == "get_history_summary":
                print("Fetching chat history...")
                history = await get_chat_history(session_id)
                if isinstance(history, str):
                    print(f"Chat History: {history}")
                else:
                    print("Chat History:")
                    for item in history:
                        print(f"{item['role']}: {item['content']}")
                continue
            
            elif query.lower()=="test":
                print("Testing connection to MCP server...")
                response = await test_connection()
                if response:
                    #meta=None content=[TextContent(type='text', text='MCP server is running successfully!', annotations=None)] isError=False
                    text_response = response.content[0].text
                    print(f"Connection successful: {text_response}")
                else:
                    print("Failed to connect to MCP server.")
                continue

            elif not query:
                print("Please enter a valid query.")
                continue
                
            print("Searching...")
            response = await send_search_query(query, max_results, search_depth)
            display_results(response)
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

session_id = "076604be-bb9c-43ee-bed1-72f10657af68"
async def get_chat_history(session_id: str):
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool(
                    "get_history_summary",
                    arguments={
                        "session_id": session_id
                    }
                )
                if hasattr(result, 'content') and result.content:
                    # If content is a list, get the first item
                    content = result.content[0] if isinstance(result.content, list) else result.content
                    
                    if hasattr(content, 'text'):
                        return content.text
                elif hasattr(result, 'text'):
                    # If result has a text attribute, return it as a string
                    return result.text
                else:
                    return str(result)

    except Exception as e:
        return {"status": "error", "message": str(e)}

async def test_connection():
    """
    Test the connection to the MCP server.
    """
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.call_tool("test_mcp_server")
                return response
    except Exception as e:
        print(f"Failed to connect to MCP server: {e}")

def main():
    """
    Run the chatbot interface.
    """
    try:
        asyncio.run(interactive_search())
    except KeyboardInterrupt:
        print("\nGoodbye!")

if __name__ == "__main__":
    main()