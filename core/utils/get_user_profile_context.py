import streamlit as st
from core.utils.get_current_profile import get_user_profile
from ui.ui_components import generate_custom_system_prompt, get_personality_presets


def get_user_profile_context() -> str:
    """Retrieve user profile data and format it as context for the chatbot."""
    try:
        user_profile = get_user_profile()
        
        profile_context = ""
        if user_profile:
            profile_context = f"""
USER PROFILE INFORMATION:
- Name: {user_profile.get('user_name', 'Not provided')}
- Phone: {user_profile.get('phone_number', 'Not provided')}
- Year of Birth: {user_profile.get('year_of_birth', 'Not provided')}
- Address: {user_profile.get('address', 'Not provided')}
- Major/Field: {user_profile.get('major', 'Not provided')}
- Additional Info: {user_profile.get('additional_info', 'Not provided')}"""
        else:
            profile_context = "\nUSER PROFILE: No user profile information available yet."
        
        # Get personality presets for fallback
        personality_presets = get_personality_presets()
        
        # Generate custom system prompt based on session state
        custom_prompt = generate_custom_system_prompt(
            st.session_state.get('personality_prompt', personality_presets['Friendly Assistant']),
            st.session_state.get('communication_style', 'Conversational'),
            st.session_state.get('response_length', 'Balanced'),
            st.session_state.get('language_pref', 'Vietnamese'),
            st.session_state.get('special_instructions', '')
        )
        
        return f"""{custom_prompt}

{profile_context}

Use the user profile information to personalize your responses when relevant. Be natural and conversational."""
        
    except Exception as e:
        print(f"Error retrieving user profile: {e}")
        return "\nUSER PROFILE: Error retrieving profile information.\n"