from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from datetime import datetime
from core.base.alchemy_storage import DatabaseManager
from database.alchemy_models import FCMToken, User
from sqlalchemy import func

app = FastAPI(title="FCM Token API", version="1.0.0")
db = DatabaseManager()

class TokenRequest(BaseModel):
    token: str
    user_id: str = "default_user"
    device_type: str = "web"
    user_agent: str = ""

@app.post("/api/fcm/register")
async def register_fcm_token(token_request: TokenRequest):
    """Store FCM token in database using SQLAlchemy"""
    try:
        print(f"🔔 Registering FCM token: {token_request.token[:10]}...")
        
        with db.get_session() as session:
            # Check if token already exists
            existing_token = session.query(FCMToken).filter(
                FCMToken.token == token_request.token
            ).first()
            
            if existing_token:
                print(f"✅ Token already exists: {token_request.token[:10]}...")
                existing_token.is_active = True
                existing_token.last_used = func.current_timestamp()
                existing_token.user_agent = token_request.user_agent
                message = "Token updated successfully"
            else:
                print(f"✅ Registering new token: {token_request.token[:10]}...")
                # Ensure user exists
                user = db.get_or_create_user(token_request.user_id)
                if not user:
                    raise HTTPException(status_code=400, detail="Failed to create user")
                
                new_token = FCMToken(
                    token=token_request.token,
                    user_id=user.user_id,
                    device_type=token_request.device_type,
                    user_agent=token_request.user_agent,
                    is_active=True
                )
                session.add(new_token)
                message = "Token registered successfully"
            
            session.commit()
        
        return {
            "success": True,
            "message": message,
            "token_preview": token_request.token[:10] + "..."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing token: {str(e)}")

@app.get("/api/fcm/tokens")
async def get_active_tokens():
    """Get all active FCM tokens from database using SQLAlchemy"""
    try:
        with db.get_session() as session:
            tokens = session.query(FCMToken).filter(
                FCMToken.is_active == True
            ).order_by(FCMToken.created_at.desc()).all()
            
            return {
                "success": True,
                "tokens": [
                    {
                        "token": token.token,
                        "user_id": str(token.user_id),
                        "device_type": token.device_type,
                        "created_at": token.created_at.isoformat() if token.created_at else None,
                        "last_used": token.last_used.isoformat() if token.last_used else None
                    }
                    for token in tokens
                ],
                "total_count": len(tokens)
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tokens: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "FCM Token API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)