import json
import asyncio
from datetime import datetime
from typing import Any

import redis.asyncio as redis
from redis.asyncio import ConnectionPool
from src.logger.logger import logger
from src.config import settings

REDIS_HOST = settings.redis_host
REDIS_PORT = settings.redis_port
REDIS_DB = settings.redis_db

# 全局连接池
_pool: ConnectionPool | None = None
_pool_loop_id: int | None = None


async def _get_pool() -> ConnectionPool:
    global _pool, _pool_loop_id
    current_loop_id = id(asyncio.get_running_loop())
    if _pool is not None and _pool_loop_id != current_loop_id:
        try:
            await _pool.disconnect()
        except Exception:
            pass
        _pool = None

    if _pool is None:
        _pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
        )
        _pool_loop_id = current_loop_id
    return _pool


async def connect_redis():
    pool = await _get_pool()
    redis_client = redis.Redis(connection_pool=pool)
    return redis_client


async def close_redis():
    global _pool, _pool_loop_id
    if _pool:
        try:
            await _pool.disconnect()
        except Exception:
            pass
        _pool = None
        _pool_loop_id = None


async def check_redis_connection() -> bool:
    try:
        redis_client = await connect_redis()
        await redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"redis客户端连接失败: {e}")
        return False


async def get_redis_cache_str(key: str) -> str | None:
    try:
        redis_client = await connect_redis()
        return await redis_client.get(key)
    except Exception as e:
        logger.warning(f"redis客户端获取缓存str失败: {e}")
        return None


async def get_redis_cache_json(key: str) -> list | dict | None:
    try:
        redis_client = await connect_redis()
        cache = await redis_client.get(key)
        if cache:
            return json.loads(cache)
        return None
    except Exception as e:
        logger.warning(f"redis客户端获取缓存list或者dict等类型失败: {e}")
        return None


def _json_default(obj: Any) -> str:
    """JSON 序列化时处理 datetime 等特殊类型"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


async def set_redis_cache(key: str, value: Any, ex: int = 3600) -> bool:
    try:
        redis_client = await connect_redis()
        if isinstance(value, str):
            await redis_client.set(key, value, ex=ex)
        elif isinstance(value, (list, dict)):
            await redis_client.set(key, json.dumps(value, ensure_ascii=False, default=_json_default), ex=ex)
        else:
            await redis_client.set(key, str(value), ex=ex)
        return True
    except Exception as e:
        logger.error(f"redis客户端设置缓存失败: {e}")
        return False


async def delete_redis_cache(key: str) -> bool:
    try:
        redis_client = await connect_redis()
        await redis_client.delete(key)
        return True
    except Exception as e:
        logger.error(f"redis客户端删除缓存失败: {e}")
        return False


async def exists_redis_cache(key: str) -> bool:
    try:
        redis_client = await connect_redis()
        return await redis_client.exists(key) > 0
    except Exception as e:
        logger.error(f"redis客户端判断缓存是否存在失败: {e}")
        return False


