from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from datetime import datetime
from core.base.storage import DatabaseManager

app = FastAPI()
db = DatabaseManager()

class TokenRequest(BaseModel):
    token: str
    user_id: str = "default_user"
    device_type: str = "web"
    user_agent: str = ""

@app.post("/api/fcm/register")
async def register_fcm_token(token_request: TokenRequest):
    """Store FCM token in database"""
    try:
        conn = db.get_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
            
        with conn.cursor() as cur:
            # Check if token already exists
            cur.execute("""
                SELECT id FROM fcm_tokens 
                WHERE token = %s AND user_id = %s
            """, (token_request.token, token_request.user_id))
            
            existing_token = cur.fetchone()
            
            if existing_token:
                # Update existing token
                cur.execute("""
                    UPDATE fcm_tokens 
                    SET is_active = true, last_used = %s, user_agent = %s
                    WHERE token = %s AND user_id = %s
                """, (datetime.now(), token_request.user_agent, token_request.token, token_request.user_id))
                
                message = "Token updated successfully"
            else:
                # Insert new token
                cur.execute("""
                    INSERT INTO fcm_tokens (token, user_id, device_type, user_agent, is_active, created_at, last_used)
                    VALUES (%s, %s, %s, %s, true, %s, %s)
                """, (
                    token_request.token,
                    token_request.user_id,
                    token_request.device_type,
                    token_request.user_agent,
                    datetime.now(),
                    datetime.now()
                ))
                
                message = "Token registered successfully"
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": message,
            "token": token_request.token[:10] + "..." # Don't return full token for security
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error storing token: {str(e)}"
        }

@app.get("/api/fcm/tokens")
async def get_active_tokens():
    """Get all active FCM tokens"""
    try:
        conn = db.get_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
            
        with conn.cursor() as cur:
            cur.execute("""
                SELECT token, user_id, device_type, created_at, last_used 
                FROM fcm_tokens 
                WHERE is_active = true
                ORDER BY created_at DESC
            """)
            
            tokens = cur.fetchall()
            
        conn.close()
        
        return {
            "success": True,
            "tokens": [
                {
                    "token": token[0][:10] + "...", # Truncated for security
                    "user_id": token[1],
                    "device_type": token[2],
                    "created_at": token[3].isoformat(),
                    "last_used": token[4].isoformat()
                }
                for token in tokens
            ],
            "total_count": len(tokens)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error retrieving tokens: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)