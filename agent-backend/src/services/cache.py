# ============================================
# cache.py - Redis 响应缓存服务
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的代码：
# ═══════════════════════════════════════════
#
# 1. 缓存 key 规范：
#    CACHE_PREFIX = "agent:cache:"
#    # key 格式：agent:cache:{意图}:{用户消息的哈希}
#    # 例：agent:cache:order_query:dingdan_id_02
#
# 2. async def get_cached_response(redis: Redis, message: str, intent: str | None) -> str | None
#    - 从 Redis 中查询缓存
#    - key = f"{CACHE_PREFIX}{intent}:{hashlib.md5(message.encode()).hexdigest()}"
#    - 如果命中 → 返回缓存的回复
#    - 如果未命中 → 返回 None
#
# 3. async def set_cached_response(redis: Redis, message: str, intent: str, response: str, ttl: int = 3600) -> None
#    - 将回复写入缓存
#    - ttl = 1 小时（可根据业务调整，如政策类可 24h，查询类 5min）
#
# 4. async def invalidate_cache(redis: Redis, pattern: str) -> None
#    - 按模式批量删除缓存（如数据更新时清理相关缓存）
#    - 例：invalidate_cache("agent:cache:order_query:*")
#
# ═══════════════════════════════════════════
# 什么场景适合缓存：
#   - 相同问题反复问（如 "退货政策是什么"）
#   - 查询类（订单状态、物流信息）— 短缓存即可
#   - 政策/条款类 — 长缓存
# 什么场景不适合：
#   - 个性化回复（含用户姓名、上下文）
#   - 需要实时数据的查询
# ═══════════════════════════════════════════
