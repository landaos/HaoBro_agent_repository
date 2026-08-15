# ============================================
# stats.py - 数据统计看板服务
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的代码：
# ═══════════════════════════════════════════
#
# 类：StatsService
#
# 用途：为管理后台提供数据统计看板 API
#
# 1. get_overview(db, days: int = 30) -> dict
#    - 总览数据（过去 N 天的汇总）
#    - 返回：
#       total_conversations: int        总对话数
#       total_messages: int             总消息数
#       total_users: int                总用户数
#       active_users: int               活跃用户数（N 天内发过消息的）
#       total_knowledge_bases: int      总知识库数
#       total_documents: int            总文档数
#       total_chunks: int               总文档块数
#
# 2. get_conversation_trend(db, days: int = 30) -> list[dict]
#    - 对话趋势（按天统计）
#    - 返回：[{date: "2026-07-01", count: 150}, ...]
#
# 3. get_message_trend(db, days: int = 30) -> list[dict]
#    - 消息趋势（按天统计）
#    - 返回：[{date: "2026-07-01", count: 750}, ...]
#
# 4. get_user_activity(db, days: int = 30) -> list[dict]
#    - 用户活跃度排行
#    - 返回：[{user_id: 1, username: "admin", message_count: 500}, ...]
#    - limit: 20（只返回前 20 名）
#
# 5. get_top_queries(db, days: int = 30, limit: int = 10) -> list[dict]
#    - 高频问题排行
#    - 对 user 角色的消息按内容分组计数
#    - 排除过短的查询（< 5 个字符）
#    - 返回：[{query: "如何重置密码", count: 50}, ...]
#
# 6. get_token_usage(db, days: int = 30) -> dict
#    - Token 消耗统计
#    - 如果消息表中记录了 token_count 字段
#    - 返回：{total_tokens: 1000000, avg_per_conversation: 500}
#
# 7. get_knowledge_base_stats(db) -> list[dict]
#    - 知识库使用统计
#    - 按知识库统计文档数、块数、引用次数（如果有反馈数据）
#    - 返回：[{kb_name: "产品手册", doc_count: 50, chunk_count: 2000}, ...]
#
# 8. get_system_health(db, redis) -> dict
#    - 系统健康状态
#    - DB 连接状态、Redis 连接状态、响应时间 P50/P95/P99
#    - 返回：{db: "ok", redis: "ok", p50_ms: 120, p95_ms: 500, p99_ms: 2000}
#
# ═══════════════════════════════════════════
# 缓存策略：
# ═══════════════════════════════════════════
#
# 统计数据不需要实时精确，建议缓存：
#   - 概览数据：缓存 5 分钟
#   - 趋势数据：缓存 10 分钟
#   - 排行榜数据：缓存 30 分钟
#   - 系统健康：不缓存（实时检测）
#
# 实现方式：在 service 层使用 redis 做 cache-aside
#   cache_key = f"stats:overview:{days}"
#   cached = await redis.get(cache_key)
#   if cached:
#       return json.loads(cached)
#   data = await compute_overview(db, days)
#   await redis.setex(cache_key, 300, json.dumps(data))
# ═══════════════════════════════════════════
