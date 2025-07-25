import sys
import streamlit as st
import os
import threading
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import asyncio
import firebase_admin
from firebase_admin import messaging, credentials

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agent.recommendation.services import (
    get_due_alerts, update_alert_status
)
from agent.recommendation.activity_analyzer import activity_analyzer
from agent.recommendation.recommendation_engine import generate_recommendations
from core.base.alchemy_storage import DatabaseManager

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
db = DatabaseManager()


class BackgroundAlertService:
    """Background service for managing alerts and recommendations"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.check_interval = 60
        self.last_recommendation_generation = datetime.now() - timedelta(hours=1)
        
    def start(self):
        """Start the background service"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_service, daemon=True)
            self.thread.start()
            logger.info("🚀 Background Alert Service started")
        else:
            logger.warning("⚠️ Background Alert Service is already running")
    
    def stop(self):
        """Stop the background service"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=5)
            logger.info("🛑 Background Alert Service stopped")
    
    def _run_service(self):
        """Main service loop"""
        while self.running:
            try:
                self._generate_activity_analysis()
                print("🔍 Analyzing user activities...")
                time.sleep(5)

                self._generate_periodic_recommendations()
                print("🔄 Checking for due alerts...")
                time.sleep(5)

                self._process_due_alerts()
                print("Cleaning up old alerts...")
                time.sleep(5)

                self._cleanup_old_alerts()
                print("Finished processing alerts and recommendations")
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ Error in background service: {e}")
            
            time.sleep(self.check_interval)

    def _generate_activity_analysis(self):
        """Generate activity analysis for upcoming events"""
        try:
            time_since_last = datetime.now() - self.last_recommendation_generation
            print(f"Last recommendation generation: {self.last_recommendation_generation}, time since last recommendation: {time_since_last}")            
            if time_since_last.total_seconds() >= 3600:
                logger.info("🔍 Generating activity analysis for user activities...")
                activity_analyzer.analyze_activities()
        except Exception as e:
            logger.error(f"❌ Error generating activity analysis: {e}")

    def _process_due_alerts(self):
        """Process alerts that are due to be sent"""
        try:
            due_alerts = get_due_alerts()
            if due_alerts:
                logger.info(f"📋 Found {len(due_alerts)} upcoming alert in 30 minutes")
                
                fcm_tokens = self._get_fcm_tokens()
                if not fcm_tokens:
                    logger.warning("⚠️ No FCM tokens available")
                    return
                    
                for alert in due_alerts:
                    # Find matching token for user
                    user_token = next((token for token in fcm_tokens if token['user_id'] == alert['user_id']), None)
                    if user_token:
                        alert['fcm_token'] = user_token['token']
                        asyncio.run(self._create_browser_notification(alert))
                        time.sleep(60)
                    else:
                        logger.warning(f"⚠️ No FCM token found for user {alert['user_id']}")
            else:
                logger.info("❌ No due alerts found")
        except Exception as e:
            logger.error(f"❌ Error processing due alerts: {e}")

    def _get_fcm_tokens(self):
        """Get all active FCM tokens from the API"""
        try:
            fcm_service_url = os.environ.get("FCM_SERVICE_URL", "http://localhost:8001")
            response = requests.get(f"{fcm_service_url}/api/fcm/tokens")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    tokens = result.get('tokens', [])
                    logger.info(f"✅ Retrieved {len(tokens)} FCM tokens")
                    return tokens
                else:
                    logger.error(f"❌ API returned error: {result}")
                    return []
            else:
                logger.error(f"❌ HTTP error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error calling FCM tokens API: {e}")
            return []

    async def _create_browser_notification(self, alert: Dict):
        """Create browser notification and updating alert status"""
        try:
            print(f"🔔 Creating browser notification for alert: {alert['title']}")
            
            if 'fcm_token' not in alert:
                logger.error("❌ No FCM token provided for alert")
                return
                
            cred = credentials.Certificate(os.environ.get("FIREBASE_CREDENTIALS_PATH"))
            
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=alert['title'],
                    body=alert['message']
                ),
                data={
                    'user_id': str(alert['user_id']),
                    'title': str(alert['title']),
                    'message': str(alert['message'])
                },
                token=alert['fcm_token']
            )
            
            response = messaging.send(message)
            logger.info(f"✅ Notification sent successfully: {response}")
            
            update_alert_status(alert['alert_id'], 'sent')
            
        except Exception as e:
            logger.error(f"❌ Error creating browser notification: {e}")
    
    def _generate_periodic_recommendations(self):
        """Generate new recommendations periodically"""
        try:
            time_since_last = datetime.now() - self.last_recommendation_generation
            print(f"Last recommendation generation: {self.last_recommendation_generation}, time since last recommendation: {time_since_last}")            
            if time_since_last.total_seconds() >= 3600:
                logger.info("🎯 Generating new recommendations...")
                result = generate_recommendations()
                
                if result.get('success'):
                    recommendations = result.get('recommendations', [])
                    alerts_created = result.get('alerts_created', 0)
                    
                    logger.info(f"✅ Generated {len(recommendations)} recommendations, {alerts_created} alerts created")
                    self.last_recommendation_generation = datetime.now()
                else:
                    logger.warning(f"⚠️ Failed to generate recommendations: {result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            logger.error(f"❌ Error generating periodic recommendations: {e}")
    
    def _cleanup_old_alerts(self):
        """Clean up old alerts"""
        with db.get_session() as session:
            try:
                from database.alchemy_models import Alert
                from datetime import datetime, timedelta
                
                cutoff_date = datetime.now() - timedelta(days=30)
                
                deleted_count = session.query(Alert).filter(
                    Alert.status == 'sent',
                    Alert.created_at < cutoff_date
                ).delete(synchronize_session=False)
                
                session.commit()
                
                if deleted_count > 0:
                    logger.info(f"🗑️ Cleanup: {deleted_count} old alerts deleted")
                    
            except Exception as e:
                logger.error(f"❌ Error in cleanup: {e}")
                session.rollback()

    def get_service_status(self) -> Dict:
        """Get service status information"""
        return {
            "running": self.running,
            "check_interval": self.check_interval,
            "last_recommendation_generation": self.last_recommendation_generation.isoformat(),
            "thread_alive": self.thread.is_alive() if self.thread else False,
            "pending_alerts_count": self.alert_queue.qsize()

        }
    def force_check_alerts(self):
        """Force check for due alerts (for manual triggering)"""
        try:
            logger.info("🔄 Force checking alerts...")
            self._process_due_alerts()
            # self._check_upcoming_events()  # Uncomment when ready
        except Exception as e:
            logger.error(f"❌ Error in force check: {e}")

# Global service instance
alert_service = BackgroundAlertService()

def start_alert_service():
    """Start the background alert service"""
    alert_service.start()

def stop_alert_service():
    """Stop the background alert service"""
    alert_service.stop()

def force_check_alerts():
    """Force check for alerts"""
    alert_service.force_check_alerts()

def get_service_status():
    """Get service status"""
    return alert_service.get_service_status()
