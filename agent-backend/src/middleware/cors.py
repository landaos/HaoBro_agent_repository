# ============================================
# cors.py - CORS 跨域配置
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的代码：
# ═══════════════════════════════════════════
#
# 1. 定义注册函数：
#    def register_cors(app: FastAPI):
#        app.add_middleware(
#            CORSMiddleware,
#            allow_origins=settings.cors_origins,      # settings 中配置
#            allow_credentials=True,
#            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#            allow_headers=["*"],
#            expose_headers=["X-Request-ID", "X-RateLimit-*"],
#        )
#
# 2. 需要在 config.py 中新增配置项：
#    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
#    # 生产环境改为前端实际域名
#    # 如果前端部署方式和后端同域，可以设为 ["*"]
#
# ═══════════════════════════════════════════
# 在 main.py 中注册（放在最前面，在所有路由之前）：
#   from src.middleware.cors import register_cors
#   register_cors(app)
# ═══════════════════════════════════════════
