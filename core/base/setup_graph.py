
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from core.base.mcp_client import init_mcp_client
from core.base.setup_tools import setup_tools
from core.base.schema import State
from core.utils.create_chatbot import create_chatbot_function


def setup_graph(db, llm):
    """Setup and return the LangGraph"""
    mcp_client = init_mcp_client()
    tools = setup_tools(mcp_client)
    llm_with_tools = llm.bind_tools(tools)
    
    graph_builder = StateGraph(State)
    
    chatbot_function = create_chatbot_function(db, llm_with_tools)
    tool_node = ToolNode(tools=tools)
    
    graph_builder.add_node("chatbot", chatbot_function)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    graph_builder.add_edge("tools", "chatbot")
    
    return graph_builder.compile()
