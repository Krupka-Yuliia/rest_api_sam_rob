import time
from fastapi import Request, HTTPException
import redis.asyncio as redis

RATE_LIMITS = {
    "anonymous": (2, 60),
    "authenticated": (10, 60),
}

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

async def rate_limit(request: Request, user_id: str | None):
    identity = user_id or request.client.host
    limit_type = "authenticated" if user_id else "anonymous"
    limit, period = RATE_LIMITS[limit_type]

    key = f"rate_limit_{identity}"
    now = int(time.time())
    window_start = now - period

    await r.zremrangebyscore(key, min=0, max=window_start)

    request_count = await r.zcard(key)
    if request_count >= limit:
        raise HTTPException(status_code=429, detail="Too many requests for rate limit")

    await r.zadd(key, {str(now): now})
    await r.expire(key, period)
