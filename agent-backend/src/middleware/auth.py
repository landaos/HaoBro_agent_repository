# ============================================
# auth.py - JWT 认证中间件
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的代码：
# ═══════════════════════════════════════════
#
# 作用：验证每个请求的 JWT Token，将用户信息注入 request.state
#
# 一、JWT 工具函数（可选单独放在 core/auth.py）
#
#   1. create_access_token(data: dict, expires_delta: timedelta | None = None) -> str
#      - 使用 python-jose 的 jwt.encode
#      - payload 必需字段：sub（user_id）、role、exp、iat
#      - 签名密钥：settings.secret_key
#      - 默认过期时间：24 小时
#
#   2. verify_token(token: str) -> dict | None
#      - 使用 python-jose 的 jwt.decode
#      - 验证签名和过期时间
#      - 返回 payload 或 None（验证失败）
#      - 捕获 JWTError 异常，不抛出
#
# 二、认证中间件类
#
#   方式 A：使用 FastAPI 的 HTTPBearer 依赖（推荐，更可控）
#     class AuthDependency:
#         async def __call__(self, request: Request, db: AsyncSession = Depends(get_db)) -> User
#           1. 从 Authorization: Bearer <token> 提取 token
#           2. verify_token(token) → payload
#           3. 查数据库确认用户存在且 is_active=True
#           4. 将 user 对象注入 request.state.current_user
#           5. 返回 user 对象
#
#     注入方式：在需要认证的路由中使用 Depends(auth_dependency)
#
#   方式 B：使用 ASGI 中间件（全局拦截，慎用）
#     class AuthMiddleware(BaseHTTPMiddleware):
#         async def dispatch(self, request: Request, call_next):
#           1. 跳过白名单路径（/health, /auth/login, /docs, /openapi.json）
#           2. 验证 token
#           3. 注入 request.state.current_user
#           4. 调用 call_next
#           5. 如果验证失败返回 401
#
#     注册方式：app.add_middleware(AuthMiddleware)
#
# 三、白名单路径（不需要认证的端点）
#
#    /api/v1/health       健康检查
#    /api/v1/auth/login   登录
#    /api/v1/auth/refresh 刷新 token
#    /docs                 Swagger 文档
#    /openapi.json         OpenAPI 规范
#    /redoc                ReDoc 文档
#
# 四、权限校验辅助函数
#
#   require_permission(required_permission: str) -> callable
#     用法：@router.get("/documents", dependencies=[Depends(require_permission("document:read"))])
#     实现：
#       1. 从 request.state.current_user 获取用户
#       2. 查用户角色关联的权限列表
#       3. 检查是否包含 required_permission
#       4. 不包含则返回 403 Forbidden
#
# ═══════════════════════════════════════════
# 关闭 Swagger 认证的方法：
#   在生产环境（APP_ENV=production）移除白名单中的 /docs，或直接禁用 Swagger：
#   if settings.app_env == "production":
#       app.docs_url = None
#       app.redoc_url = None
# ═══════════════════════════════════════════
