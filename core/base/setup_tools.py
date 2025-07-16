import asyncio
from langchain_tavily import TavilySearch
from langchain.tools import StructuredTool
from core.base.mcp_client import (
    MCPClient, 
    mcp_history_tool, 
    update_user_information, 
    add_event_information, 
    add_activity_information
)

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
        description="""Use this tool AUTOMATICALLY whenever the user mentions a scheduled, purpose-driven event, appointment, meeting, or reminder that is not a regular habit. This tool is for one-time or infrequent occurrences with a specific goal (e.g., a meeting, doctor's appointment, or deadline).

        ### Semantic Patterns:
        - Explicit scheduling: "meeting at 2 PM", "appointment with Dr. Smith tomorrow"
        - Future-oriented actions: "set a reminder for next week", "plan a call on Friday"
        - Specific purposes: "project review", "client presentation"
        - Time-bound commitments: "interview at 10 AM", "conference on July 5th"

        ### Universal Indicators (language-independent):
        - Proper nouns + time (e.g., "with John at 3 PM", "at office tomorrow")
        - Specific dates/times (e.g., "2025-07-02", "2 PM", "next Monday")
        - Obligation or planning verbs (e.g., "must attend", "schedule", "arrange")
        - Context of formal/professional events (e.g., "team sync", "workshop")

        ### Contextual Clues:
        - Temporal expressions with specific intent (e.g., "deadline is Thursday")
        - Names of people/places + time (e.g., "with Sarah at hotel")
        - Non-routine activities with clear start/end times
        - Phrases indicating commitment or necessity (e.g., "need to", "have to")

        ### Table Schema: events(event_id, event_name, start_time, end_time, location, description, priority)
        - event_id: Unique identifier for the event (UUID)
        - event_name: Required name of the event (VARCHAR 100)
        - start_time: Optional start time of the event (DATETIME)
        - end_time: Optional end time of the event (DATETIME)
        - location: Optional location of the event (TEXT)
        - description: Optional description of the event (TEXT)
        - priority: Optional priority level (low, medium, high)

        ALWAYS use this tool for scheduled, non-habitual events with a clear purpose, even in any language. Focus on semantic intent rather than routine behaviors.""",
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

    extract_activity_tool = StructuredTool.from_function(
        func=lambda user_input: add_activity_information(user_input, mcp_client),
        name="add_activity",
        description="""Use this tool to extract information from the input message when the user refers to routine, habitual, or casual activities that occur regularly or spontaneously, such as personal routines, hobbies, or daily tasks (e.g., eating, playing football, watching TV).

        ### Semantic Patterns:
        - Routine behaviors: "I eat at 6 PM", "jogging every evening"
        - Hobbies/leisure: "play football on Thursdays", "watch TV at night"
        - Daily/personal tasks: "reading before bed", "cooking dinner"
        - Recurring habits: "morning workout", "evening walk"

        ### Universal Indicators (language-independent):
        - Time expressions with regularity (e.g., "every day at 6 PM", "usually in the evening")
        - Casual or personal context (e.g., "my hobby", "relaxing")
        - No specific purpose or commitment (e.g., "just chilling")
        - Repetitive time patterns (e.g., "Mondays and Wednesdays")

        ### Contextual Clues:
        - Habitual language (e.g., "always", "often", "usually")
        - Lack of formal scheduling (e.g., no specific date or appointment)
        - Personal enjoyment or relaxation (e.g., "fun activity", "leisure time")
        - Tags like "hobby", "routine", or "personal"

        ### Table Schema: activities(id, activity_name, description, start_at, end_at, tags)
        - name: The name of the activity (required, max 100 characters).
        - description: A brief description of the activity (optional).
        - start_at: The start time of the activity in TIMESTAMP format (e.g., '2025-07-01 15:00:00+07:00'), inferred from the input or defaulting to the current date (July 01, 2025) if only time is provided.
        - end_at: The end time of the activity in TIMESTAMP format, inferred from the input or estimated as 1 hour after start_at if not specified.
        - tags: An array of text tags (e.g., ARRAY['work', 'meeting']) relevant to the activity, inferred from the input (optional, default to empty array if none).

        ALWAYS use this tool for regular, habitual, or casual activities, even in any language. Focus on semantic intent indicating routine or personal behavior rather than scheduled events.""",
        args_schema={
            "type": "object",
            "properties": {
                "user_input": {
                    "type": "string",
                    "description": "The input string containing activity information."
                }
            },
            "required": ["user_input"]
        },
    )

    return [search_tool, retrieve_tool, extract_user_info_tool, extract_event_info_tool, extract_activity_tool]
