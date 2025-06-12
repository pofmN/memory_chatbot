from typing import Annotated
import dotenv
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain_tavily import TavilySearch
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()
openai_api = os.environ.get("OPENAI_API_KEY")
tavily_api = os.environ.get("TAVILY_API_KEY")
llm = ChatOpenAI(
    model_name="gpt-4.1-mini", # gpt-4o, gpt-4o-mini, gpt-4.1-mini, gpt-4.1-nano, ada-2, 3-small
    temperature=0.7,
    max_tokens=1000,
    base_url="https://warranty-api-dev.picontechnology.com:8443",  # Ensure /v1 path if OpenAI-compatible
    openai_api_key=openai_api,  # Optional if handled in gateway
)
class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

search_tool = TavilySearch(max_results=3)
tools =[search_tool]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State) -> str:
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}

tool_node = ToolNode(tools=[search_tool])

graph_builder.add_node("tools", tool_node)
graph_builder.add_node("chatbot", chatbot)

graph_builder.add_edge(START, "chatbot")

# Define the condition for using the tool
graph_builder.add_conditional_edges("chatbot", tools_condition)

graph_builder.add_edge("tools", "chatbot")
graph = graph_builder.compile()

def stream_graph_update(user_input: str):
    for event in graph.stream({"mșssages": [{"role": "user", "content": user_input}]}):
        for key, value in event.items():
            # Only print messages from the chatbot node, not from tools
            if key == "chatbot" and "messages" in value and len(value["messages"]) > 0:
                print("Assistant:", value["messages"][-1].content)

while True:
    try:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Exiting the chatbot. Goodbye!")
            break
        stream_graph_update(user_input)
    except Exception as e:
        user_input = input(f"An error occurred {e}.\nPlease try again: ")

    