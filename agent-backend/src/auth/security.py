import json
import time
import uuid
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt,JWTError
from sqlalchemy import select
from passlib.context import CryptContext

from src.config import settings
from src.logger.logger import logger
from src.db.session import async_session_factory
from src.db.redis import connect_redis,set_redis_cache

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm

security=HTTPBearer()

pwt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def encode_password(password: str)->str:
    return pwt_context.hash(password)

def verify_password(plain_password: str, hashed_password: str)->bool:
    return pwt_context.verify(plain_password, hashed_password)

def generate_token(user_id: str,email:str,username:str)->tuple[str,int]:
    ex=int(time.time())+60*60*24
    payload = {"user_id": user_id,"email":email,"username":username,"exp":ex,"iat":int(time.time()),"jti":str(uuid.uuid4())}    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token,ex

def encode_token(token: str)->dict[str,Any] | None:
    try:
        payload=jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

async def blacklist_token(token: str):
    payload = encode_token(token)
    if payload is None:
        return
    jti = payload.get("jti")
    exp = payload.get("exp")
    if not exp or not jti:
        return
    current_time = int(time.time())
    ttl = max(exp - current_time, 0)
    try:
        redis_client = await connect_redis()
        await redis_client.set(f"blacklist:{jti}", "1", ex=ttl)
    except Exception as e:
        logger.warning(f"【auth】黑名单设置失败: {e}")

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = encode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token",headers={"WWW-Authenticate": "Bearer"})
    
    jti = payload.get("jti")
    if jti:
        try:
            redis_client = await connect_redis()
            is_blacklisted = await redis_client.exists(f"blacklist:{jti}")
            if is_blacklisted:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token blacklisted",headers={"WWW-Authenticate": "Bearer"})
        except HTTPException as e:
            raise
        except Exception as e:
            logger.warning(f"【auth】黑名单检查失败: {e}")

    user_id: str = payload.get("user_id")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID not found", headers={"WWW-Authenticate": "Bearer"})
    return user_id

async def get_user_info_from_db(user_id: str)->dict[str,Any] | None:
    from src.models.user import User
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            return None
    return {
        "user_id":user.user_id,
        "username":user.user_name,
        "email":user.email,
        "phone":user.phone,
        "status":user.status,
        "gender":user.gender,
        "created_at":user.created_at.isoformat(),
        "updated_at":user.updated_at.isoformat() if user.updated_at else None,
    }
 
async def get_user_info_from_redis(user_id:str):
    redis_client=await connect_redis()
    key=f"user:{user_id}"
    try:
        user_info=await redis_client.get(key)
        if user_info is not None:
            try:
                return json.loads(user_info)
            except json.JSONDecodeError as e:
                await redis_client.delete(key)

        user_data=await get_user_info_from_db(user_id)
        if user_data:
            await set_redis_cache(key,user_data,ex=3600)
            return user_data
        return None
    except UnicodeDecodeError:
        await redis_client.delete(key)
        user_data=await get_user_info_from_db(user_id)
        if user_data is not None:
            await set_redis_cache(key,user_data,ex=3600)
            return user_data
        return None
       
        
        
    
   
