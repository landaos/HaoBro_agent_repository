# ============================================
# redis.py - Redis 客户端封装
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的代码：
# ═══════════════════════════════════════════
#
# 1. 创建 Redis 连接池：
#    import redis.asyncio as aioredis
#    redis_client: aioredis.Redis | None = None
#
# 2. init_redis() / close_redis()：
#    - init_redis(): 创建 Redis 连接池
#      redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
#    - close_redis(): 关闭连接池
#
# 3. get_redis() -> Redis：
#    - 返回全局 Redis 实例
#    - 在应用启动时 init，关闭时 close
#
# ═══════════════════════════════════════════
# decode_responses=True 让 Redis 自动返回 str 而非 bytes
# 限流、缓存等操作均通过此客户端进行
# ═══════════════════════════════════════════
