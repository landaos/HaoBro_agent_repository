from socket import RDS_CANCEL_SENT_TO

from fastapi import HTTPException, Request
from src.db.redis import connect_redis
from config import settings

_RATE_LIMIT_ENABLED = settings.rate_limit_enabled.lower() == "true"

def rate_limit(limit:int=10,windows:int=60):
    async def dependency(request: Request):
        if not _RATE_LIMIT_ENABLED:
            return
        client_id = request.client.host
        key = f"rate_limit:{request.url.path}:{client_id}"
        redis = await connect_redis()

        current_count=await redis.get(key)
        current_count=int(current_count) if current_count else 0
        
        if current_count >= limit:
            raise HTTPException(status_code=429, detail="请求过于频繁，触发了速率限制，请稍后重试")   

        if current_count ==0:
            await redis.setex(key,windows,1)
        else:
            await redis.incr(key)
    return dependency

class RateLimitMiddleware:
    def __init__(self,app,limit: int = 100, windows: int = 60):
        self.app = app
        self.limit = limit
        self.windows = windows
    async def __call__(self, scope, receive, send):
        if not _RATE_LIMIT_ENABLED:
            await self.app(scope, receive, send)
            return
        
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from fastapi import Request
        request = Request(scope, receive=receive)

        client_id = request.client.host

        key = f"rate_limit:{request.url.path}:{client_id}"

        redis = await connect_redis()

        current_count=await redis.get(key)
        current_count=int(current_count) if current_count else 0

        if current_count >= self.limit:
            from starlette.responses import JSONResponse
            response = JSONResponse({"detail": "请求过于频繁，触发了速率限制，请稍后重试"},status_code=429)
            await response(scope,receive,send)
            return
        
        if current_count ==0:
            await redis.setex(key,self.windows,1)
        else:
            await redis.incr(key)
        
        await self.app(scope, receive, send)
        
        