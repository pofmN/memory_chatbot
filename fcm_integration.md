# Firebase Cloud Messaging (FCM) Integration

This document explains how the Firebase Cloud Messaging (FCM) system is integrated into the Memory Chat application to provide real-time notifications to users even when the application tab is closed.

## Overview

The FCM integration consists of several components:

1. **FCM Token Database Table**: Stores device tokens for sending push notifications
2. **FastAPI Service**: Manages token registration and sending notifications
3. **Firebase Client Integration**: JS code for registering browsers with Firebase
4. **Background Service Integration**: Connects alerts to the FCM service

## Components

### 1. Database Schema

The FCM system uses two tables:
- `fcm_tokens`: Stores device tokens for push notifications
- `notification_history`: Tracks notification delivery and acknowledgment

```sql
CREATE TABLE IF NOT EXISTS fcm_tokens (
    token_id SERIAL PRIMARY KEY,
    token TEXT NOT NULL UNIQUE,
    device_info TEXT,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES user_profile(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notification_history (
    notification_id SERIAL PRIMARY KEY,
    alert_id INTEGER,
    title VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    shown_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    FOREIGN KEY (alert_id) REFERENCES alert(alert_id) ON DELETE SET NULL
);
```

### 2. FastAPI Service

The FastAPI service (`fast_server.py`) handles:
- Token registration and management
- Sending notifications to registered devices
- Processing alerts from the database

Key endpoints:
- `POST /api/fcm/register`: Register a new device token
- `POST /api/fcm/unregister/{token}`: Unregister a token
- `POST /api/fcm/send`: Send a notification to all registered devices
- `POST /api/alerts/send/{alert_id}`: Send a specific alert
- `POST /api/alerts/process-due`: Process all due alerts

### 3. Client-Side Integration

The client-side integration includes:
- Firebase SDK integration
- Service worker for background notifications
- Web app manifest for installation

Required files:
- `firebase_messaging.html`: Main Firebase integration code
- `firebase-messaging-sw.js`: Service worker for background notifications
- `manifest.json`: Web app manifest for installation

### 4. Alert System Integration

The background alert service has been updated to:
- Queue notifications for in-app display
- Send alerts via FCM for offline delivery
- Update alert status after delivery

## Setup Instructions

1. Follow the steps in `firebase_setup.md` to create a Firebase project
2. Configure environment variables in `.env`:
   ```
   FIREBASE_CREDENTIALS_PATH=/path/to/your-service-account-key.json
   FCM_SERVICE_PORT=8001
   FCM_SERVICE_URL=http://localhost:8001
   ```
3. Start the FCM service:
   ```bash
   python fcm_service.py
   ```
4. Start the Streamlit app:
   ```bash
   streamlit run app_dev.py
   ```

## Docker Deployment

Use Docker Compose to deploy the entire system including the FCM service:

```bash
docker-compose up -d
```

## Testing FCM

Use the testing script to send test notifications:

```bash
python tools/test_fcm.py --action send --title "Test" --message "This is a test notification"
```

To register a test token:

```bash
python tools/test_fcm.py --action register --token "YOUR_FCM_TOKEN"
```

## How It Works

1. Users access the Streamlit app in their browser
2. The browser requests notification permission
3. A Firebase token is generated and registered with the backend
4. When alerts are triggered, they're sent via FCM
5. Users receive notifications even when the browser tab is closed

## Security Considerations

- Firebase credentials must be kept secure
- In production, restrict CORS origins
- Use HTTPS for all communications
