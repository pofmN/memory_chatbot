import sys
import os
import logging
import signal
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agent.bg_running.background_alert_service import start_alert_service, stop_alert_service, get_service_status

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutting down services...")
    stop_alert_service()
    sys.exit(0)

def main():
    """Main function to start services"""
    print("🚀 Starting Background Alert Service...")
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the service
    start_alert_service()
    
    print("✅ Background Alert Service started successfully!")
    print("📋 Service will check for alerts every minute")
    print("💡 New recommendations will be generated every 4 hours")
    print("🔔 Press Ctrl+C to stop the service")
    
    try:
        while True:
            status = get_service_status()
            if not status['running']:
                print("⚠️ Service stopped unexpectedly, restarting...")
                start_alert_service()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
        stop_alert_service()

if __name__ == "__main__":
    main()