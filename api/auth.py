import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError

JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "1440"))

bearer = HTTPBearer()

def create_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRES_MIN)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    token = creds.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
