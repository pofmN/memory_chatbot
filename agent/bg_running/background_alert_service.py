import sys
import streamlit as st
import os
import queue
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agent.recommendation.services import (
    get_upcoming_events, get_due_alerts, get_pending_alerts,
    update_alert_status, create_system_alert, alert_exists
)
from agent.recommendation.recommendation_engine import generate_recommendations
from core.base.storage import DatabaseManager

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


def display_alert():
    try:
        st.toast(" Creating test alert...", icon="🔔")
    except Exception as e:
        st.error(f"❌ Error creating test alert: {e}")
        return None

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
                self._generate_periodic_recommendations()
                print("🔄 Checking for due alerts...")

                self._process_due_alerts()
                print("Cleaning up old alerts...")

                self._cleanup_old_alerts()
                print("Finished processing alerts and recommendations")
                
            except Exception as e:
                logger.error(f"❌ Error in background service: {e}")
            
            time.sleep(self.check_interval)
    
    def _process_due_alerts(self):
        """Process alerts that are due to be sent"""
        try:
            due_alerts = get_due_alerts()
            
            if due_alerts:
                logger.info(f"📋 Found {len(due_alerts)} upcoming alert in 30 minutes")
                
                for alert in due_alerts:
                    self._create_browser_notification(alert)
                    time.sleep(60)  # moi alert cach 10 phut
            else:
                logger.info("✅ No due alerts found")
                print("❌ No due alerts found")
                    
        except Exception as e:
            logger.error(f"❌ Error processing due alerts: {e}")
    
    def _create_browser_notification(self, alert: Dict):
        """Create browser notification and updating alert status"""
        try:
            alert_id = alert.get('alert_id')
            logger.info(f"🔔 Alert: {alert.get('title', 'System Alert')} - {alert.get('message', '')}")
            
            update_rows = update_alert_status(alert_id, 'sent')
            if update_rows:
                logger.info(f"✅ Alert status updated for ID: {alert_id}")
            else:
                logger.warning(f"⚠️ No rows updated for alert ID: {alert_id}, it may already be sent")
            
            logger.info(f"📱 Alert marked as sent for browser display: {alert_id}")
            
        except Exception as e:
            logger.error(f"❌ Error updating alert status for browser notification: {e}")

    
    def _send_email_notification(self, alert: Dict):
        """Send email notification if configured"""
        try: 
            # Email configuration
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            sender_email = os.getenv('SENDER_EMAIL', '')
            sender_password = os.getenv('SENDER_PASSWORD', '')
            recipient_email = os.getenv('RECIPIENT_EMAIL', '')
            
            if not all([sender_email, sender_password, recipient_email]):
                logger.debug("📧 Email configuration incomplete, skipping email notification")
                return
            
            # Create message
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = recipient_email
            message["Subject"] = f"📋 Tip of the Day: {alert.get('title', 'System Alert')}"
            
            # Email body
            body = f"""
            <html>
            <body>
                <h2>💡 Daily Tip & Recommendation</h2>
                <p><strong>Title:</strong> {alert.get('title', 'No title')}</p>
                <p><strong>Message:</strong> {alert.get('message', 'No message')}</p>
                <p><strong>Priority:</strong> {alert.get('priority', 'medium')}</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p><small>This is an automated message from your Personal Assistant</small></p>
            </body>
            </html>
            """
            
            message.attach(MIMEText(body, "html"))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(message)
                
            logger.info(f"📧 Email notification sent for alert: {alert['alert_id']}")
            
        except Exception as e:
            logger.error(f"❌ Error sending email notification: {e}")
    
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
        conn = None
        try:
            conn = db.get_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM alert 
                        WHERE status = 'sent' 
                        AND created_at < NOW() - INTERVAL '30 days'
                    """)
                    deleted_alerts = cur.rowcount

                conn.commit()
                if deleted_alerts > 0:
                    logger.info(f"🗑️ Cleanup: {deleted_alerts} old alerts deleted")
                        
        except Exception as e:
            logger.error(f"❌ Error in cleanup: {e}")
        finally:
            if conn:
                conn.close()

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