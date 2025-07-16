
import streamlit as st
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import os
import logging
import firebase_admin
import typing
from typing import Dict
from firebase_admin import credentials, messaging
from core.base.storage import DatabaseManager
from langchain_openai import ChatOpenAI
from agent.recommendation.services import update_alert_status
import uuid

# Load environment variables
load_dotenv()
openai_api = os.environ.get("OPENAI_API_KEY")
db = DatabaseManager()

llm = ChatOpenAI(
        model_name="gpt-4o-mini", # gpt-4o, gpt-4o-mini, gpt-4.1-mini, gpt-4.1-nano, ada-2, 3-small
        temperature=0.2,
        max_tokens=1000,
        base_url="https://warranty-api-dev.picontechnology.com:8443",  # Ensure /v1 path if OpenAI-compatible
        openai_api_key=openai_api,
    )
import requests
import os

def test_fcm_tokens_api():
    """Test the FCM tokens API"""
    fcm_service_url = os.environ.get("FCM_SERVICE_URL", "http://localhost:8001")
    
    try:
        response = requests.get(f"{fcm_service_url}/api/fcm/tokens")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            tokens = data.get('tokens', [])
            print(f"\n📱 Found {len(tokens)} FCM tokens:")
            for i, token in enumerate(tokens, 1):
                print(f"{i}. User: {token['user_id']}")
                print(f"   Token: {token['token'][:20]}...")
                print(f"   Device: {token['device_type']}")
                print(f"   Created: {token['created_at']}")
                print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
def _create_browser_notification(alert: Dict):
        """Create browser notification and updating alert status"""
        try:
            print(f"🔔 Creating browser notification for alert: {alert['title']}")
            
            if 'fcm_token' not in alert:
                print("❌ No FCM token provided for alert")
                return
            
            # Clear existing environment variables first
            if 'FIREBASE_CREDENTIALS_PATH' in os.environ:
                del os.environ['FIREBASE_CREDENTIALS_PATH']

            # Force reload with override
            load_dotenv(override=True)
            cred = credentials.Certificate(os.environ.get("FIREBASE_CREDENTIALS_PATH"))
            
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=alert['title'],
                    body=alert['message']
                ),
                data={
                    'alert_id': str(alert['id']),
                    'user_id': str(alert['user_id']),
                    'title': str(alert['title']),
                    'message': str(alert['message'])
                },
                token=alert['fcm_token']
            )
            
            # Send the message
            try:
                response = messaging.send(message)
                print(f"✅ Notification sent successfully: {response}")
            except Exception as e:
                print(f"❌ Firebase API call error: {e}")
                return
        except Exception as e:
            print(f"❌ Error creating browser notification: {e}")

if __name__ == "__main__":
    test_fcm_tokens_api()
    alert = {
        "id": str(uuid.uuid4()),
        "title": "Test Alert",
        "message": "This is a test notification",
        "user_id": "12345678-1234-1234-1234-123456789012",
        "fcm_token": "dvSCA2_oorB__KGGk6L5Tq:APA91bHYvuFXF3tUjEE1nO2jcon_V8xeU9mrlSUYOlPyDcdEVvksC1ly2Vm86GDx053H6vTexiHe6rQwe40kh572huNd45Iw1y4t3cnYpF-8RQpenAedAY4"
    }
    _create_browser_notification(alert)

