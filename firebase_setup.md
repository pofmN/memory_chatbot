# Firebase Cloud Messaging Setup Guide

This guide will help you set up Firebase Cloud Messaging (FCM) for your Memory Chat application.

## 1. Create a Firebase Project

1. Go to the [Firebase Console](https://console.firebase.google.com/) and create a new project.
2. Enter your project name and follow the setup instructions.

## 2. Register Your Web App

1. In the Firebase Console, click on the "Web" icon to add a web app to your project.
2. Register your app with a name (e.g., "Memory Chat Web").
3. Copy the Firebase configuration object that looks like:
```javascript
const firebaseConfig = {
  apiKey: "...",
  authDomain: "...",
  projectId: "...",
  storageBucket: "...",
  messagingSenderId: "...",
  appId: "..."
};
```

## 3. Update the Firebase Configuration

Open `/Users/nam.pv/Documents/work-space/memory_chat/ui/firebase_messaging.html` and replace the placeholder configuration with your actual Firebase config.

## 4. Generate a VAPID Key

1. In the Firebase Console, go to Project Settings > Cloud Messaging.
2. In the "Web configuration" section, generate a new Web Push certificate.
3. Copy the generated key pair and replace the placeholder in the firebase_messaging.html file.

## 5. Generate a Service Account Key

1. In the Firebase Console, go to Project Settings > Service Accounts.
2. Click "Generate new private key" and save the JSON file.
3. Store this file securely and set the path in your environment variables:

```bash
export FIREBASE_CREDENTIALS_PATH="/path/to/your-service-account-key.json"
```

Or store the contents in an environment variable (for cloud deployments):

```bash
export FIREBASE_CREDENTIALS_JSON='{"type":"service_account","project_id":"...",...}'
```

## 6. Set Up Environment Variables

Create or update your `.env` file with:

```
# Firebase settings
FIREBASE_CREDENTIALS_PATH=/path/to/your-service-account-key.json
FCM_SERVICE_PORT=8001
FCM_SERVICE_URL=http://localhost:8001
```

## 7. Start the FCM Service

Run the FCM service with:

```bash
python fcm_service.py
```

The service will start on port 8001 by default.

## 8. Testing FCM

You can test FCM notifications with:

```bash
curl -X POST http://localhost:8001/api/fcm/send \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Notification","message":"This is a test notification","priority":"high"}'
```

## Troubleshooting

- **No notifications appearing**: Check browser permissions and make sure your web app is running over HTTPS or localhost.
- **FCM service errors**: Check the `fcm_service.log` file for detailed error messages.
- **Firebase initialization failed**: Verify your service account credentials are correct and accessible.
