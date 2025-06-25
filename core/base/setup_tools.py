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
    
def add_event_information(user_input:str, mcp_client: MCPClient) -> str:
    
    """Add an event to the MCP server."""
    try:
        event_info = asyncio.run(mcp_client.add_event(user_input))
        return event_info
    except Exception as e:
        return f"Error adding event: {str(e)}"
    

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
    extract_event_info_tool = StructuredTool.from_function(
        func=lambda user_input: add_event_information(user_input, mcp_client),
        name="add_event",
        description="""Use this tool AUTOMATICALLY whenever the user mentions ANY event, appointment, meeting, reminder, or time-based activity in ANY language. 
    SEMANTIC PATTERNS - Use this tool when user mentions:
    - Time expressions: dates, hours, relative time (tomorrow, next week, in 2 hours, etc.)
    - Person names + time: "with [name] at [time]"
    - Location + time references
    - Activities with scheduled times
    - Future tense + time reference
    - Obligation/reminder expressions
    - Calendar-related activities
    - Recurring activities with time patterns

    UNIVERSAL INDICATORS (language-independent):
    - Names of people + time expressions
    - Numbers + time units (2pm, 3 hours, Monday, etc.)
    - Location names + temporal context
    - Action verbs + future time references
    - Modal verbs expressing necessity/planning + time
    - Question words about when/where + activities
    - Dates in any format (DD/MM, MM/DD, YYYY-MM-DD)
    - Times in any format (24h, 12h, relative)

    CONTEXTUAL CLUES to detect events:
    - Temporal expressions combined with activities
    - Personal pronouns + future activities
    - Proper nouns (names, places) + time context
    - Numbers representing time/dates
    - Expressions of obligation or planning
    - Social/professional activity contexts

    TABLE SCHEMA: events(event_id, event_name, start_time, end_time, location, description, priority)
    - event_id: Unique identifier for the event (UUID)
    - event_name: Required name of the event (VARCHAR 100)
    - start_time: Optional start time of the event (DATETIME)
    - end_time: Optional end time of the event (DATETIME)
    - location: Optional location of the event (TEXT)
    - description: Optional description of the event (TEXT)
    - priority: Optional priority level (low, medium, high)
    
    ALWAYS use this tool when you detect temporal context combined with activities, regardless of the language used. Focus on semantic meaning rather than specific keywords.""",
        args_schema={
            "type": "object",
            "properties": {
                "user_input": {
                    "type": "string",
                    "description": "The complete user input containing event or time-based activity information in any language."
                }
            },
            "required": ["user_input"]
        },
    )

    return [search_tool, retrieve_tool, extract_user_info_tool, extract_event_info_tool]
