import streamlit as st
from typing import Dict, Any
from core.base.storage import DatabaseManager

def generate_custom_system_prompt(personality: str, style: str, length: str, language: str, instructions: str) -> str:
    """Generate a custom system prompt based on user preferences"""
    
    # Style mappings
    style_instructions = {
        "Conversational": "Use a natural, conversational tone. Be friendly and approachable.",
        "Formal": "Use formal language and professional tone. Be respectful and business-like.",
        "Technical": "Use precise, technical language. Include relevant technical details and terminology.",
        "Simple": "Use simple, clear language. Avoid jargon and complex explanations.",
        "Detailed": "Provide thorough, comprehensive explanations with examples and context.",
        "Brief": "Keep responses concise and to the point. Avoid unnecessary elaboration."
    }
    
    # Length mappings
    length_instructions = {
        "Brief": "Keep responses short and concise (1-2 sentences when possible).",
        "Balanced": "Provide appropriately sized responses based on the question complexity.",
        "Detailed": "Provide comprehensive responses with explanations and examples.",
        "Comprehensive": "Give thorough, in-depth responses covering all aspects of the topic."
    }
    
    # Language mappings
    language_instructions = {
        "English": "Respond in English only.",
        "Vietnamese": "Respond in Vietnamese only.",
        "Mixed (English + Vietnamese)": "You can use both English and Vietnamese as appropriate. Switch languages naturally based on context.",
        "Auto-detect": "Detect the user's language preference and respond accordingly."
    }

    prompt = f"""{personality}

COMMUNICATION GUIDELINES:
- Style: {style_instructions.get(style, style)}
- Length: {length_instructions.get(length, length)}
- Language: {language_instructions.get(language, language)}"""
    
    if instructions:
        prompt += f"\n\nSPECIAL INSTRUCTIONS:\n{instructions}"
    
    return prompt

def get_personality_presets() -> Dict[str, str]:
    """Get predefined personality options"""
    return {
        "Friendly Assistant": "You are a friendly and helpful AI assistant. Be warm, encouraging, and supportive in your responses.",
        "Professional Advisor": "You are a professional AI advisor. Provide clear, concise, and expert-level guidance. Be formal and business-like.",
        "Creative Companion": "You are a creative and imaginative AI companion. Be playful, innovative, and think outside the box.",
        "Study Buddy": "You are a patient and knowledgeable study companion. Help with learning, explain concepts clearly, and encourage academic growth.",
        "Casual Friend": "You are a casual and laid-back AI friend. Be conversational, use informal language, and be relatable.",
        "Custom": "Write your own custom personality..."
    }

def initialize_session_state():
    """Initialize session state variables for UI components"""
    if "selected_personality" not in st.session_state:
        st.session_state.selected_personality = "Friendly Assistant"
    if "communication_style" not in st.session_state:
        st.session_state.communication_style = "Conversational"
    if "response_length" not in st.session_state:
        st.session_state.response_length = "Balanced"
    if "language_pref" not in st.session_state:
        st.session_state.language_pref = "Vietnamese"
    if "special_instructions" not in st.session_state:
        st.session_state.special_instructions = ""
    if "custom_personality" not in st.session_state:
        st.session_state.custom_personality = ""
    
    # Initialize custom prompts
    if "custom_prompts" not in st.session_state:
        st.session_state.custom_prompts = {
            "Default": {
                "personality": "Friendly Assistant",
                "style": "Conversational",
                "length": "Balanced",
                "language": "Auto-detect",
                "instructions": "khi trả lời tôi phải gọi tôi là hoàng thượng đi kèm với kính thưa hoàng đế."
            }
        }

def render_sidebar():
    """Render the sidebar with customization options"""
    personality_presets = get_personality_presets()
    
    st.sidebar.title("🎨 Customize Your AI")
    st.sidebar.markdown("---")
    
    # ✅ Custom Personality Section
    st.sidebar.subheader("🤖 AI Personality")
    
    selected_personality = st.sidebar.selectbox(
        "Choose AI personality:",
        list(personality_presets.keys()),
        index=list(personality_presets.keys()).index(st.session_state.selected_personality),
        key="personality_selectbox"
    )
    
    # Update session state immediately
    if selected_personality != st.session_state.selected_personality:
        st.session_state.selected_personality = selected_personality
    
    if selected_personality == "Custom":
        custom_personality = st.sidebar.text_area(
            "Describe your AI's personality:",
            placeholder="You are a...",
            height=100,
            value=st.session_state.custom_personality,
            key="custom_personality_input"
        )
        if custom_personality != st.session_state.custom_personality:
            st.session_state.custom_personality = custom_personality
        personality_prompt = custom_personality if custom_personality else personality_presets["Friendly Assistant"]
    else:
        personality_prompt = personality_presets[selected_personality]
    
    # Store personality prompt
    st.session_state.personality_prompt = personality_prompt
        
    # ✅ Communication Style Section
    st.sidebar.subheader("💬 Communication Style")
    
    communication_style = st.sidebar.selectbox(
        "Response style:",
        ["Conversational", "Formal", "Technical", "Simple", "Detailed", "Brief"],
        index=["Conversational", "Formal", "Technical", "Simple", "Detailed", "Brief"].index(st.session_state.communication_style),
        key="communication_style_selectbox"
    )
    
    if communication_style != st.session_state.communication_style:
        st.session_state.communication_style = communication_style
    
    # ✅ Response Length
    response_length = st.sidebar.selectbox(
        "Response length preference:",
        ["Balanced", "Brief", "Detailed", "Comprehensive"],
        index=["Balanced", "Brief", "Detailed", "Comprehensive"].index(st.session_state.response_length),
        key="response_length_selectbox"
    )
    
    if response_length != st.session_state.response_length:
        st.session_state.response_length = response_length
    
    # ✅ Language Preference
    language_pref = st.sidebar.selectbox(
        "Language preference:",
        ["English", "Vietnamese", "Mixed (English + Vietnamese)", "Auto-detect"],
        index=["English", "Vietnamese", "Mixed (English + Vietnamese)", "Auto-detect"].index(st.session_state.language_pref),
        key="language_pref_selectbox"
    )
    
    if language_pref != st.session_state.language_pref:
        st.session_state.language_pref = language_pref
    
    # ✅ Special Instructions
    st.sidebar.subheader("📝 Special Instructions")
    special_instructions = st.sidebar.text_area(
        "Additional instructions for your AI:",
        placeholder="Always ask follow-up questions, focus on practical solutions, etc.",
        height=80,
        value=st.session_state.special_instructions,
        key="special_instructions_input"
    )
    
    if special_instructions != st.session_state.special_instructions:
        st.session_state.special_instructions = special_instructions
    
    # ✅ Save/Load Presets
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Prompt Presets")
    
    # Preset management
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        preset_name = st.text_input("Preset name:", placeholder="My Custom AI")
        if st.button("💾 Save Preset"):
            if preset_name:
                st.session_state.custom_prompts[preset_name] = {
                    "personality": st.session_state.selected_personality,
                    "custom_personality": st.session_state.custom_personality,
                    "style": st.session_state.communication_style,
                    "length": st.session_state.response_length,
                    "language": st.session_state.language_pref,
                    "instructions": st.session_state.special_instructions
                }
                st.success(f"✅ Saved '{preset_name}'")
            else:
                st.error("Please enter a preset name")
    
    with col2:
        if st.session_state.custom_prompts:
            selected_preset = st.selectbox("Load preset:", list(st.session_state.custom_prompts.keys()))
            if st.button("📂 Load Preset"):
                preset = st.session_state.custom_prompts[selected_preset]
                st.session_state.selected_personality = preset.get("personality", "Friendly Assistant")
                st.session_state.custom_personality = preset.get("custom_personality", "")
                st.session_state.communication_style = preset.get("style", "Conversational")
                st.session_state.response_length = preset.get("length", "Balanced")
                st.session_state.language_pref = preset.get("language", "Vietnamese")
                st.session_state.special_instructions = preset.get("instructions", "")
                
                # Update personality prompt
                if st.session_state.selected_personality == "Custom":
                    st.session_state.personality_prompt = st.session_state.custom_personality
                else:
                    st.session_state.personality_prompt = personality_presets[st.session_state.selected_personality]
                
                st.success(f"✅ Loaded '{selected_preset}'")
                st.rerun()
    
    # ✅ Preview Generated Prompt
    st.sidebar.markdown("---")
    st.sidebar.subheader("👁️ Prompt Preview")
    
    with st.sidebar.expander("View generated system prompt"):
        preview_prompt = generate_custom_system_prompt(
            st.session_state.personality_prompt,
            st.session_state.communication_style,
            st.session_state.response_length,
            st.session_state.language_pref,
            st.session_state.special_instructions
        )
        st.code(preview_prompt, language="text")
    
    # ✅ Control buttons
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Apply Now", help="Apply changes immediately"):
            st.rerun()
    with col2:
        if st.button("🔄 Reset", help="Reset to defaults"):
            st.session_state.selected_personality = "Friendly Assistant"
            st.session_state.personality_prompt = personality_presets["Friendly Assistant"]
            st.session_state.communication_style = "Conversational"
            st.session_state.response_length = "Balanced"
            st.session_state.language_pref = "Auto-detect"
            st.session_state.special_instructions = ""
            st.session_state.custom_personality = ""
            st.rerun()

def render_header():
    """Render the main header with current AI mode indicator"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("🤖 AI Chatbot with Memory")
        st.markdown("*This chatbot remembers our conversation history*")

    with col2:
        # Show current personality
        current_personality = st.session_state.get('selected_personality', 'Friendly Assistant')
        st.info(f"🎭 Mode: {current_personality}")
        
        if st.button("🗑️ Clear Chat", help="Clear all conversation history"):
            if st.session_state.get('single_session_id'):
                st.session_state.messages = []
                st.rerun()

def render_chat_messages():
    """Render chat messages in a container"""
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            welcome_msg = "Xin chào! Tôi là trợ lý AI của bạn. Tôi có thể giúp bạn hôm nay?"
            st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
            st.chat_message("assistant").write(welcome_msg)
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

def render_session_info():
    """Render session information"""
    if st.session_state.get('single_session_id'):
        st.info(f"📝 Session: {st.session_state.single_session_id[:8]}... | Messages: {len(st.session_state.messages)}")

def render_footer():
    """Render the footer with tech stack and database status"""
    st.markdown("---")
    st.markdown("**Tech Stack:** Streamlit + PostgreSQL + Docker + GPT-4o-mini + Tavily Search")

def render_database_status(db):
    """Render database connection status"""
    try:
        conn = db.get_connection()
        if conn:
            conn.close()
            st.success("✅ Database Connected")
        else:
            st.error("❌ Database Connection Failed")
    except:
        st.error("❌ Database Connection Failed")

# Add this to your ui_components.py file

import time

def render_notification_auto_refresh():
    """Auto-refresh notifications every 30 seconds"""
    if 'last_notification_check' not in st.session_state:
        st.session_state.last_notification_check = time.time()
    
    # Check for new notifications every 30 seconds
    if time.time() - st.session_state.last_notification_check > 30:
        st.session_state.last_notification_check = time.time()
        
        # Check for new high priority alerts
        try:
            db = DatabaseManager()
            conn = db.get_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) FROM alert 
                        WHERE status = 'triggered' 
                        AND priority = 'high'
                    """)
                    high_priority_count = cur.fetchone()[0]
                    
                    if high_priority_count > 0:
                        st.toast(f"🔔 You have {high_priority_count} high priority alerts!", icon="🔔")
        except Exception:
            pass
        finally:
            if conn:
                conn.close()