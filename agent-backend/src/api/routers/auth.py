# ============================================
# auth.py - 认证接口（可选，根据需求决定是否实现）
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的路由（如需）：
# ═══════════════════════════════════════════
#
# 1. POST /auth/login
#    - 请求体: LoginRequest（定义在 schemas/auth.py）
#      - username: str
#      - password: str
#    - 响应: TokenResponse
#      - access_token: str（JWT）
#      - token_type: str = "bearer"
#      - expires_in: int（过期秒数）
#    - 实现：
#      1. 查数据库验证用户名密码（passlib 验哈希）
#      2. 生成 JWT（python-jose），payload 包含 user_id, role, exp
#      3. 返回 token
#
# 2. POST /auth/refresh
#    - 刷新 token，同上逻辑
#
# ═══════════════════════════════════════════
# 如果不需要认证，删掉此文件即可
# 路由挂在 /api/v1/auth 下
# ═══════════════════════════════════════════
