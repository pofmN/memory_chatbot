import streamlit as st
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from database.storage import DatabaseManager
from ui.ui_components import (
    initialize_session_state, 
    render_sidebar, 
    render_header, 
    render_session_info,
    render_chat_messages, 
    render_footer, 
    render_database_status
)
from core import (
    initialize_session, 
    initialize_messages, 
    setup_graph
)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Chatbot with Memory",
    page_icon="🤖",
    layout="wide"
)

# Initialize environment variables
openai_api = os.environ.get("OPENAI_API_KEY")
tavily_api = os.environ.get("TAVILY_API_KEY")

@st.cache_resource
def init_components():
    """Initialize database and LLM components"""
    db = DatabaseManager()
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0.2,
        max_tokens=1000,
        base_url="https://warranty-api-dev.picontechnology.com:8443",
        openai_api_key=openai_api,
    )
    return db, llm

def main():
    """Main application function"""
    # Initialize components
    db, llm = init_components()
    
    # Initialize session state
    initialize_session_state()
    initialize_session(db)
    initialize_messages()
    
    # Setup graph
    graph = setup_graph(db, llm)
    
    # Render UI components
    render_sidebar()
    render_header()
    render_session_info()
    render_chat_messages()
    
    # Chat input and processing
    if user_input := st.chat_input("Type your message here..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        
        # Save user message to database
        session_id = st.session_state.get('single_session_id')
        if session_id:
            db.save_message(session_id, "user", user_input)
        
        # Process with assistant
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                all_responses = []
                
                for event in graph.stream({
                    "messages": [{"role": "user", "content": user_input}], 
                    "session_id": session_id
                }):
                    for key, value in event.items():
                        print(f"📊 Event: {key}")
                        
                        if key == "chatbot" and "messages" in value and len(value["messages"]) > 0:
                            last_message = value["messages"][-1]
                            if hasattr(last_message, 'content') and last_message.content:
                                all_responses.append({
                                    'content': last_message.content,
                                    'has_tool_calls': hasattr(last_message, 'tool_calls') and bool(last_message.tool_calls)
                                })
                
                if all_responses:
                    final_response = all_responses[-1]['content']
                    print(f"✅ Using final response: {final_response[:100]}...")
                    
                    # Add assistant message
                    st.session_state.messages.append({"role": "assistant", "content": final_response})
                    st.write(final_response)
                    
                    # Save assistant message to database
                    if session_id:
                        db.save_message(session_id, "assistant", final_response)
                else:
                    st.error("❌ No response generated.")
    
    # Render footer
    render_footer()
    render_database_status(db)

if __name__ == "__main__":
    main()