import streamlit as st
from core.base.schema import State
from core.utils.get_user_profile import get_user_profile_context


def create_chatbot_function(llm_with_tools):
    """Create chatbot function with dependencies"""
    def chatbot(state: State) -> dict:
        """Chatbot function that uses session state values"""
        
        user_info = get_user_profile_context()
        messages = state["messages"].copy()
        
        # Create system message with custom prompt and user profile
        system_message = {
            "role": "system", 
            "content": user_info
        }

        messages.insert(0, system_message)
        
        # Debug: Print current settings
        print("="*50)
        print("Current Settings:")
        print(f"Personality: {st.session_state.get('selected_personality', 'Not set')}")
        print(f"Style: {st.session_state.get('communication_style', 'Not set')}")
        print(f"Length: {st.session_state.get('response_length', 'Not set')}")
        print(f"Language: {st.session_state.get('language_pref', 'Not set')}")
        print(f"Instructions: {st.session_state.get('special_instructions', 'Not set')}")
        print("="*50)
        
        response = llm_with_tools.invoke(messages)
        
        # Handle tool calls (session_id injection)
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call.get('name') == 'retrieve_chat_history':
                    if 'args' not in tool_call:
                        tool_call['args'] = {}
                    tool_call['args']['session_id'] = state.get("session_id")
        
        return {"messages": state["messages"] + [response]}
    
    return chatbot