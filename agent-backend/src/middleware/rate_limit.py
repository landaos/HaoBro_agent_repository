# ============================================
# rate_limit.py - 限流中间件
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的中间件：
# ═══════════════════════════════════════════
#
# 1. 定义 RateLimitMiddleware(BaseHTTPMiddleware)：
#    - 每个请求进来时执行以下逻辑：
#      1. 跳过 /health 路径（不限制健康检查）
#      2. 从请求中获取 user_id（从 Header: X-User-ID 或 JWT）
#      3. 拼接 rate limit key: f"ratelimit:{user_id}:{path}"
#      4. 调用 services/rate_limiter.py 的 check_rate_limit()
#      5. 如果超限 → 返回 429 Too Many Requests
#      6. 在响应头写入限流信息（X-RateLimit-*）
#      7. 通过 → 继续执行
#
# 2. 在 main.py 中注册：
#    app.add_middleware(RateLimitMiddleware)
#
# ═══════════════════════════════════════════
# 注意：
# - 如果用户未认证（无 user_id），可以用 IP 地址兜底
# - 限流窗口和上限从 settings.api_rate_limit 读取
# ═══════════════════════════════════════════
