from core.base.schema import EventInformation
from langgraph.graph import StateGraph, START, END
from datetime import datetime
import json
from typing import Literal
from typing import List, Optional
from typing_extensions import TypedDict
import dotenv
import os
from langchain.chat_models import ChatOpenAI
from prompt import EXTRACT_EVENT_SYSTEM_PROMPT
from core.base.storage import DatabaseManager
dotenv.load_dotenv()

openai_api = os.environ.get("OPENAI_API_KEY")


llm = ChatOpenAI(
        model_name="gpt-4o-mini", # gpt-4o, gpt-4o-mini, gpt-4.1-mini, gpt-4.1-nano, ada-2, 3-small
        temperature=0.1 ,
        max_tokens=1000,
        base_url="https://warranty-api-dev.picontechnology.com:8443",  # Ensure /v1 path if OpenAI-compatible
        openai_api_key=openai_api,
    )

db = DatabaseManager()

class EventState(TypedDict):
    """State for the event extraction agent."""
    user_input: str
    current_context: str
    extracted_event: List[dict]
    validated_event: List[dict]
    saved_result: List[dict]
    error: Optional[str]
    current_date_time: str
    user_timezone: str

class EventExtractionAgent:
    def __init__(self):
        self.llm = llm
        self.db = DatabaseManager
        self._create_graph() = self._create_graph()
    def _create_graph(self) -> StateGraph:
        """Create the event extraction graph"""
        graph = StateGraph(EventState)
        
        graph.add_node("extract", self._extract_node)
        graph.add_node("validate", self._validate_node)
        graph.add_node("save", self._save_node)
        
        graph.add_edge(START, "extract")
        graph.add_conditional_edges("extract", self._should_continue, {
            "validate": "validate",
            "end": END
        })
        graph.add_conditional_edges("validate", self._should_save, {
            "save": "save",
            "end": END
        })
        graph.add_edge("save", END)
        
        return graph.compile()
    def _extract_node(self, state: EventState) -> dict:
        """Extract event information from user input."""
        user_input = state["user_input"]
        current_context = state["current_context"]
        current_date_time = state["current_date_time", datetime.now().isoformat()]
        user_timezone = state["user_timezone"]
        prompt = f"""
        {EXTRACT_EVENT_SYSTEM_PROMPT}
        Current date/time: {current_date_time}
        User timezone: {user_timezone}
        Current context: {current_context}
        User input: {user_input}
        
        """

        

        response = self.llm.invoke(prompt)
        extracted_event = json.loads(response.content)

        
