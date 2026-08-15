# ============================================
# audit_log.py - 审计日志中间件
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的代码：
# ═══════════════════════════════════════════
#
# 作用：自动记录关键操作的审计日志（谁、何时、做了什么）
#
# 实现方式：ASGI 中间件
#
# class AuditLogMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#
#       1. 记录请求开始时间
#         start_time = time.time()
#
#       2. 放行请求
#         response = await call_next(request)
#
#       3. 计算耗时
#         duration_ms = int((time.time() - start_time) * 1000)
#
#       4. 判断是否需要记录审计日志
#         - 只记录写操作：POST / PUT / PATCH / DELETE
#         - 跳过白名单路径：/health, /docs, /openapi.json
#         - 只记录需要审计的路径前缀：
#           /api/v1/auth/*
#           /api/v1/users/*
#           /api/v1/roles/*
#           /api/v1/knowledge-bases/*
#           /api/v1/documents/*
#
#       5. 构造审计日志记录
#         log_entry = {
#             "user_id": request.state.current_user.id if hasattr else None,
#             "username": request.state.current_user.username if hasattr else "anonymous",
#             "action": f"{request.method.lower()}_{resource_type}",
#             "resource": request.url.path,
#             "ip_address": request.client.host if request.client else None,
#             "user_agent": request.headers.get("user-agent"),
#             "status_code": response.status_code,
#             "duration_ms": duration_ms
#         }
#
#       6. 异步写入审计日志
#         - 方案 A：直接写入数据库（简单，但可能影响响应速度）
#         - 方案 B：通过 task_queue 异步写入（推荐，高并发下不阻塞）
#           await task_queue.enqueue("write_audit_log", log_entry)
#         - 方案 C：先写入 Redis List，由定时任务批量刷到 DB（性能最好）
#
#       7. 返回响应
#         return response
#
# ═══════════════════════════════════════════
# 配置开关（控制审计日志的详细程度）：
# ═══════════════════════════════════════════
#
# 在 config.py 中添加：
#   AUDIT_LOG_ENABLED: bool = True        # 总开关
#   AUDIT_LOG_BODY: bool = False          # 是否记录请求体（可能包含敏感信息）
#   AUDIT_LOG_HEADERS: bool = False       # 是否记录请求头（默认不记录）
#   AUDIT_LOG_BATCH_SIZE: int = 100       # 批量写入的条数
#   AUDIT_LOG_INTERVAL: int = 10          # 批量写入间隔（秒）
#
# ═══════════════════════════════════════════
# 注意事项：
# ═══════════════════════════════════════════
#
# 1. 审计日志不支持删除操作，只能 set status=archived
# 2. 建议通过 task_queue 异步写入，避免影响主请求性能
# 3. 生产环境中审计日志数据量会快速增长，务必配置自动归档
# 4. 不要在审计日志中记录密码、token 等敏感信息
# 5. 审计日志中间件应在认证中间件之后注册（确保能获取用户信息）
# ═══════════════════════════════════════════
