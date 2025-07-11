import streamlit as st
import streamlit.components.v1 as components
import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import time
from core.base.storage import DatabaseManager

from ui.ui_components import (
    initialize_session_state, 
    render_sidebar, 
    render_header, 
    render_session_info,
    render_chat_messages, 
    render_footer, 
    render_database_status
    
)
from core.base.mcp_client import (
    initialize_session, 
    initialize_messages
)

from agent.bg_running.background_alert_service import (
    start_alert_service
    )

from core.base.setup_graph import setup_graph


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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('background_alerts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def initialize_alert_service():
    """Initialize the background alert service with Streamlit session"""
    if "alert_service_started" not in st.session_state:
        try:
            start_alert_service()
            st.session_state.alert_service_started = True
            st.success("🚀 Background Alert Service started successfully!")
        except Exception as e:
            st.error(f"❌ Failed to start alert service: {e}")
            st.session_state.alert_service_started = False

def collect_fcm_token():
    # Load Firebase config from environment variables
    firebase_api_key = os.getenv("FIREBASE_API_KEY")
    firebase_auth_domain = os.getenv("FIREBASE_AUTH_DOMAIN")
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
    firebase_messaging_sender_id = os.getenv("FIREBASE_MESSAGING_SENDER_ID")
    firebase_app_id = os.getenv("FIREBASE_APP_ID")
    firebase_vapid_key = os.getenv("FIREBASE_VAPID_KEY")
    
    components.html(f"""
    <script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-messaging-compat.js"></script>

    <script>
    const firebaseConfig = {{
        apiKey: "{firebase_api_key}",
        authDomain: "{firebase_auth_domain}",
        projectId: "{firebase_project_id}",
        messagingSenderId: "{firebase_messaging_sender_id}",
        appId: "{firebase_app_id}"
    }};

    firebase.initializeApp(firebaseConfig);
    const messaging = firebase.messaging();

    // Function to get user agent info
    function getUserAgent() {{
        return navigator.userAgent;
    }}

    // Function to generate a simple user ID (you can customize this)
    function getUserId() {{
        let userId = localStorage.getItem('fcm_user_id');
        if (!userId) {{
            userId = 'user_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('fcm_user_id', userId);
        }}
        return userId;
    }}

    // Function to store token in database via FastAPI
    async function storeTokenInDatabase(token) {{
        try {{
            const response = await fetch('http://localhost:8001/api/fcm/register', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({{
                    token: token,
                    user_id: getUserId(),
                    device_type: 'web',
                    user_agent: getUserAgent()
                }})
            }});

            const result = await response.json();
            
            if (result.success) {{
                console.log('✅ FCM Token stored successfully:', result.message);
                console.log('Token ID:', result.token);
                
                // Show success message in console
                console.log('🔔 Push notifications are now enabled!');
                
                // Optionally store token locally for future reference
                localStorage.setItem('fcm_token_stored', 'true');
                localStorage.setItem('fcm_token_timestamp', new Date().toISOString());
            }} else {{
                console.error('❌ Failed to store FCM token:', result.message);
            }}
        }} catch (error) {{
            console.error('❌ Error calling FCM API:', error);
        }}
    }}

    // Function to request permission and get token
    async function requestPermissionAndGetToken() {{
        try {{
            // Request notification permission
            const permission = await Notification.requestPermission();
            
            if (permission === 'granted') {{
                console.log('✅ Notification permission granted');
                
                try {{
                    // Get FCM token
                    const currentToken = await messaging.getToken({{ 
                        vapidKey: '{firebase_vapid_key}' 
                    }});
                    
                    if (currentToken) {{
                        console.log('✅ FCM Token retrieved:', currentToken);
                        
                        // Store token in database
                        await storeTokenInDatabase(currentToken);
                        
                        // Monitor token refresh
                        messaging.onTokenRefresh(() => {{
                            console.log('🔄 FCM Token refreshed');
                            messaging.getToken({{ vapidKey: '{firebase_vapid_key}' }}).then((refreshedToken) => {{
                                console.log('🔄 New FCM Token:', refreshedToken);
                                storeTokenInDatabase(refreshedToken);
                            }});
                        }});
                        
                    }} else {{
                        console.warn('⚠️ No FCM registration token available');
                    }}
                }} catch (tokenError) {{
                    console.error('❌ Error getting FCM token:', tokenError);
                }}
            }} else {{
                console.log('❌ Notification permission denied');
            }}
        }} catch (error) {{
            console.error('❌ Error requesting permission:', error);
        }}
    }}

    // Function to initialize service worker and get token
    async function initializeFCM() {{
        try {{
            // Check if service worker is supported
            if ('serviceWorker' in navigator) {{
                // Register service worker
                const registration = await navigator.serviceWorker.register('/firebase-messaging-sw.js');
                console.log('✅ Service Worker registered successfully');
                
                // Use service worker for messaging
                messaging.useServiceWorker(registration);
                
                // Check if token was already stored recently (to avoid spam)
                const tokenStored = localStorage.getItem('fcm_token_stored');
                const tokenTimestamp = localStorage.getItem('fcm_token_timestamp');
                
                if (tokenStored && tokenTimestamp) {{
                    const timeDiff = Date.now() - new Date(tokenTimestamp).getTime();
                    const hoursDiff = timeDiff / (1000 * 60 * 60);
                    
                    if (hoursDiff < 24) {{
                        console.log('ℹ️ FCM token was recently stored, skipping...');
                        return;
                    }}
                }}
                
                // Request permission and get token
                await requestPermissionAndGetToken();
                
            }} else {{
                console.warn('⚠️ Service workers not supported');
            }}
        }} catch (error) {{
            console.error('❌ Error initializing FCM:', error);
        }}
    }}

    // Handle incoming messages (optional - for foreground messages)
    messaging.onMessage((payload) => {{
        console.log('📨 Message received in foreground:', payload);
        
        // Display notification manually for foreground messages
        if (payload.notification) {{
            new Notification(payload.notification.title, {{
                body: payload.notification.body,
                icon: payload.notification.icon || '🔔'
            }});
        }}
    }});

    // Auto-initialize FCM when script loads
    document.addEventListener('DOMContentLoaded', initializeFCM);
    
    // Also initialize immediately if DOM is already loaded
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', initializeFCM);
    }} else {{
        initializeFCM();
    }}
    </script>
    """, height=0)

def initialize_session_with_db(db):
    """Initialize session and load chat history from database"""
    # Get or create session
    if 'single_session_id' not in st.session_state:
        # Create new session with user_id
        session_id = db.create_session(user_id="12345678-1234-1234-1234-123456789012")
        st.session_state.single_session_id = session_id
        print(f"✅ Created new session: {session_id}")
    else:
        session_id = st.session_state.single_session_id
        print(f"📋 Using existing session: {session_id}")
    
    # Load chat history from database
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Check if we need to load history
    if len(st.session_state.messages) == 0:
        try:
            chat_history = db.get_chat_history(session_id)
            if chat_history:
                st.session_state.messages = []
                for msg in chat_history:
                    st.session_state.messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
                print(f"✅ Loaded {len(chat_history)} messages from database")
            else:
                print("📝 No previous chat history found")
        except Exception as e:
            print(f"❌ Error loading chat history: {e}")
    
    return session_id

def main():
    """Main application function"""
    
    db, llm = init_components()
    
    initialize_session_state()
    
    # ✅ Replace these lines:
    # initialize_session(db)
    # initialize_messages()
    
    # ✅ With this:
    session_id = initialize_session_with_db(db)
    
    initialize_alert_service()
    
    # Setup graph
    graph = setup_graph(db, llm)
    
    render_sidebar()
    render_header()
    render_session_info()
    render_chat_messages()

    if user_input := st.chat_input("Type your message here..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        
        # Save user message to database
        session_id = st.session_state.get('single_session_id')
        if session_id:
            success = db.save_message(session_id, "user", user_input)
            if success:
                print(f"✅ User message saved to database")
            else:
                print(f"❌ Failed to save user message")
        
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
                        success = db.save_message(session_id, "assistant", final_response)
                        if success:
                            print(f"✅ Assistant message saved to database")
                        else:
                            print(f"❌ Failed to save assistant message")
                else:
                    st.error("❌ No response generated.")

    render_footer()
    render_database_status(db)
    collect_fcm_token()
    
    # Load Firebase messaging components for FCM support
    #st.button("Test Alert", on_click=test_alert("asdfqweqweqweqweq","qweqweqweq"), type="primary")

if __name__ == "__main__":
    main()