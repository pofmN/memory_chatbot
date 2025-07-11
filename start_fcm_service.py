import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.getenv("FCM_SERVICE_PORT", 8001))
    
    # Start FastAPI server
    print(f"🚀 Starting FCM Service on port {port}...")
    uvicorn.run("core.base.fast_server:app", host="0.0.0.0", port=port, reload=True)
