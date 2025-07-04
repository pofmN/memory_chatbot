import streamlit as st
import sys
import os
from datetime import datetime
from typing import List, Dict

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.base.storage import DatabaseManager
from psycopg2.extras import RealDictCursor

db = DatabaseManager()

def get_user_notifications(user_id: str = 'default_user') -> List[Dict]:
    """Get triggered/active alerts for display as notifications"""
    try:
        conn = db.get_connection()
        if conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT alert_id, alert_type, title, message, priority, 
                           trigger_time, status, source, created_at
                    FROM alert 
                    WHERE status IN ('triggered', 'active') 
                    AND (trigger_time IS NULL OR trigger_time <= NOW())
                    ORDER BY created_at DESC
                    LIMIT 10
                """)
                return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        st.error(f"Error getting notifications: {e}")
        return []
    finally:
        if conn:
            conn.close()
    return []

def mark_notification_read(alert_id: str):
    """Mark alert as read by updating status to 'sent'"""
    try:
        conn = db.get_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE alert 
                    SET status = 'sent'
                    WHERE alert_id = %s
                """, (alert_id,))
            conn.commit()
    except Exception as e:
        st.error(f"Error marking notification as read: {e}")
    finally:
        if conn:
            conn.close()

def mark_all_notifications_read():
    """Mark all triggered alerts as sent"""
    try:
        conn = db.get_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE alert 
                    SET status = 'sent'
                    WHERE status = 'triggered'
                """)
            conn.commit()
            return cur.rowcount
    except Exception as e:
        st.error(f"Error marking all notifications as read: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def display_notifications():
    """Display notifications in the Streamlit sidebar using alert table"""
    notifications = get_user_notifications()
    
    if notifications:
        st.sidebar.markdown("---")
        
        # Header with notification count
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            st.sidebar.subheader(f"🔔 Tips & Alerts ({len(notifications)})")
        with col2:
            if st.sidebar.button("✅", help="Mark all as read", key="mark_all_read"):
                count = mark_all_notifications_read()
                st.sidebar.success(f"Marked {count} notifications as read!")
                st.rerun()
        
        # Display each notification
        for notification in notifications:
            priority_color = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(notification.get('priority', 'medium'), '🟡')
            
            # Icon based on alert type
            type_icon = {
                'event': '📅',
                'recommendation': '💡',
                'reminder': '⏰',
                'activity': '🏃',
                'system': '⚙️'
            }.get(notification.get('alert_type', 'system'), '📋')
            
            with st.sidebar.expander(
                f"{priority_color} {type_icon} {notification.get('title', 'Alert')}", 
                expanded=False
            ):
                st.write(notification.get('message', 'No message'))
                
                # Show additional info
                if notification.get('source'):
                    st.caption(f"📍 Source: {notification['source']}")
                
                st.caption(f"🕒 Created: {notification.get('created_at', 'Unknown')}")
                
                if notification.get('trigger_time'):
                    st.caption(f"⏰ Trigger: {notification['trigger_time']}")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("✓ Read", key=f"read_{notification['alert_id']}"):
                        mark_notification_read(notification['alert_id'])
                        st.rerun()
                
                with col2:
                    # Show alert type
                    st.caption(f"📋 {notification.get('alert_type', 'alert').title()}")
    else:
        st.sidebar.markdown("---")
        st.sidebar.info("🔔 No new notifications")

def show_high_priority_alerts():
    """Show high priority alerts as popups"""
    notifications = get_user_notifications()
    
    if notifications:
        # Get high priority alerts
        high_priority = [n for n in notifications if n.get('priority') == 'high']
        
        if high_priority:
            latest_alert = high_priority[0]
            
            # Show as warning message
            st.warning(f"🚨 **High Priority Alert:** {latest_alert.get('title', 'Alert')}")
            
            with st.expander("📋 View Details", expanded=True):
                st.write(latest_alert.get('message', 'No message'))
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("✓ Mark as Read", key=f"popup_read_{latest_alert['alert_id']}"):
                        mark_notification_read(latest_alert['alert_id'])
                        st.rerun()
                
                with col2:
                    st.caption(f"Type: {latest_alert.get('alert_type', 'alert')}")

def create_notification_dashboard():
    """Create a full notification dashboard using alert table"""
    st.header("🔔 Notifications & Alerts")
    
    # Service status
    try:
        from agent.bg_running.background_alert_service import get_service_status
        status = get_service_status()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Service Status", "🟢 Running" if status['running'] else "🔴 Stopped")
        with col2:
            st.metric("Check Interval", f"{status['check_interval']}s")
        with col3:
            st.metric("Last Recommendation", status['last_recommendation_generation'][:10])
    except Exception as e:
        st.error(f"Cannot get service status: {e}")
    
    # Control buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🔄 Force Check Alerts"):
            try:
                from agent.bg_running.background_alert_service import force_check_alerts
                force_check_alerts()
                st.success("✅ Alert check triggered!")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        if st.button("✅ Mark All Read"):
            count = mark_all_notifications_read()
            st.success(f"Marked {count} notifications as read!")
            st.rerun()
    
    with col3:
        if st.button("🎯 Generate Recommendations"):
            try:
                from agent.recommendation.recommendation_engine import generate_recommendations
                result = generate_recommendations()
                if result.get('success'):
                    st.success(f"Generated {len(result.get('recommendations', []))} recommendations!")
                else:
                    st.error(f"Failed: {result.get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Display alert statistics
    st.subheader("📊 Alert Statistics")
    try:
        conn = db.get_connection()
        if conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get alert counts by status
                cur.execute("""
                    SELECT status, COUNT(*) as count
                    FROM alert 
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                    GROUP BY status
                """)
                stats = cur.fetchall()
                
                if stats:
                    cols = st.columns(len(stats))
                    for i, stat in enumerate(stats):
                        with cols[i]:
                            icon = {
                                'pending': '⏳',
                                'triggered': '🔔',
                                'sent': '✅',
                                'active': '🟢'
                            }.get(stat['status'], '📋')
                            st.metric(
                                f"{icon} {stat['status'].title()}", 
                                stat['count']
                            )
    except Exception as e:
        st.error(f"Error getting statistics: {e}")
    finally:
        if conn:
            conn.close()
    
    # Display all notifications
    st.subheader("📋 All Notifications")
    all_notifications = get_user_notifications()
    
    if all_notifications:
        for notification in all_notifications:
            priority_color = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(notification.get('priority', 'medium'), '🟡')
            
            with st.expander(f"{priority_color} {notification.get('title', 'Alert')}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(notification.get('message', 'No message'))
                
                with col2:
                    st.caption(f"**Type:** {notification.get('alert_type', 'alert')}")
                    st.caption(f"**Priority:** {notification.get('priority', 'medium')}")
                    st.caption(f"**Source:** {notification.get('source', 'system')}")
                    st.caption(f"**Status:** {notification.get('status', 'unknown')}")
                    st.caption(f"**Created:** {notification.get('created_at', 'Unknown')}")
                
                if st.button("✓ Mark as Read", key=f"dashboard_read_{notification['alert_id']}"):
                    mark_notification_read(notification['alert_id'])
                    st.rerun()
    else:
        st.info("No notifications to display")

# Auto-refresh functionality
def auto_refresh_notifications():
    """Auto-refresh notifications every 30 seconds"""
    import time
    
    if 'last_notification_check' not in st.session_state:
        st.session_state.last_notification_check = time.time()
    
    # Check for new notifications every 30 seconds
    if time.time() - st.session_state.last_notification_check > 30:
        st.session_state.last_notification_check = time.time()
        notifications = get_user_notifications()
        
        if notifications:
            # Show toast notification for new alerts
            high_priority = [n for n in notifications if n.get('priority') == 'high']
            if high_priority:
                st.toast(f"🔔 You have {len(high_priority)} high priority alerts!", icon="🔔")
            else:
                st.toast(f"🔔 You have {len(notifications)} new notifications!", icon="🔔")