# ============================================
# stats.py - 数据统计看板 API 路由
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的路由：
# ═══════════════════════════════════════════
#
# 所有路由挂载在 /api/v1/stats 下
# 所有路由都需要 admin 或 editor 角色权限
# 权限：require_permission("system:view_stats")
#
# 1. GET /stats/overview
#    - 总览数据
#    - 查询参数：days（默认 30）
#    - 响应：OverviewResponse
#      { total_conversations, total_messages, total_users,
#        active_users, total_documents, total_chunks }
#
# 2. GET /stats/conversation-trend
#    - 对话趋势（按天）
#    - 查询参数：days（默认 30）
#    - 响应：list[{date, count}]
#
# 3. GET /stats/message-trend
#    - 消息趋势（按天）
#    - 查询参数：days（默认 30）
#    - 响应：list[{date, count}]
#
# 4. GET /stats/top-queries
#    - 高频问题排行
#    - 查询参数：days（默认 30），limit（默认 10）
#    - 响应：list[{query, count}]
#
# 5. GET /stats/user-activity
#    - 用户活跃度排行
#    - 查询参数：days（默认 30），limit（默认 20）
#    - 响应：list[{user_id, username, message_count, last_active}]
#
# 6. GET /stats/knowledge-bases
#    - 知识库使用统计
#    - 响应：list[{kb_id, kb_name, doc_count, chunk_count, owner}]
#
# 7. GET /stats/system-health
#    - 系统健康状态
#    - 响应：{db, redis, uptime, p50_ms, p95_ms, p99_ms}
#
# ═══════════════════════════════════════════
# 缓存策略：
#   概览/趋势数据缓存 5 分钟（Redis），
#   排行榜缓存 30 分钟，
#   系统健康实时不缓存。
#
# 接口响应：
#   Cache-Control: public, max-age=300
# ═══════════════════════════════════════════
