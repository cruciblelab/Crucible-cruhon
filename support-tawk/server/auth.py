from __future__ import annotations
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import config
from .database import Agent

_SECRET = config.server.secret_key
_HOURS = config.admin.session_hours
_bearer = HTTPBearer(auto_error=False)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(agent_id: int, role: str) -> str:
    payload = {
        "sub": str(agent_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=_HOURS),
    }
    return jwt.encode(payload, _SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, _SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token süresi doldu")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Geçersiz token")


def get_current_agent(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> Agent:
    if not creds:
        raise HTTPException(status_code=401, detail="Kimlik doğrulama gerekli")
    payload = decode_token(creds.credentials)
    agent = Agent.get_or_none(Agent.id == int(payload["sub"]), Agent.is_active == True)
    if not agent:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
    return agent


def require_admin(agent: Agent = Depends(get_current_agent)) -> Agent:
    if agent.role != "admin":
        raise HTTPException(status_code=403, detail="Yönetici yetkisi gerekli")
    return agent


def verify_ws_token(token: str) -> Agent | None:
    try:
        payload = decode_token(token)
        return Agent.get_or_none(Agent.id == int(payload["sub"]), Agent.is_active == True)
    except Exception:
        return None
