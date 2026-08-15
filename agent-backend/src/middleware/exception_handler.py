# ============================================
# exception_handler.py - 全局异常处理 + 统一错误码
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的代码：
# ═══════════════════════════════════════════
#
# 1. 定义统一错误响应模型（也可放在 schemas/common.py）：
#    class ErrorResponse(BaseModel):
#        error_code: str     # 业务错误码，如 "RATE_LIMITED", "INVALID_INPUT"
#        message: str        # 用户可读的错误描述
#        detail: Any | None  # 额外调试信息（生产环境可为空）
#
# 2. 自定义异常类：
#    class AppException(Exception):
#        def __init__(self, error_code: str, message: str, status_code: int = 400, detail: Any = None):
#            ...
#    # 子类示例：
#    class RateLimitException(AppException): ...
#    class NotFoundException(AppException): ...
#    class LLMException(AppException): ...
#
# 3. 注册全局异常处理器（在 main.py 中调用此模块的注册函数）：
#    def register_exception_handlers(app: FastAPI):
#        @app.exception_handler(AppException)
#        async def app_exception_handler(request, exc):
#            return JSONResponse(
#                status_code=exc.status_code,
#                content={"error_code": exc.error_code, "message": exc.message, "detail": exc.detail}
#            )
#        @app.exception_handler(Exception)
#        async def global_exception_handler(request, exc):
#            # 记录完整异常栈到日志
#            logger.opt(exception=True).error("Unhandled exception: {}", exc)
#            return JSONResponse(
#                status_code=500,
#                content={"error_code": "INTERNAL_ERROR", "message": "服务器内部错误"}
#            )
#        @app.exception_handler(ValidationError)  # Pydantic 校验错误
#        async def validation_handler(request, exc):
#            return JSONResponse(status_code=422, content={"error_code": "INVALID_INPUT", "message": str(exc)})
#
# ═══════════════════════════════════════════
# 错误码规范（建议）：
#   RATE_LIMITED    429  请求过频繁
#   INVALID_INPUT   422  参数校验失败
#   UNAUTHORIZED    401  未认证
#   FORBIDDEN       403  无权限
#   NOT_FOUND       404  资源不存在
#   LLM_ERROR       502  LLM 调用失败
#   INTERNAL_ERROR  500  服务器内部错误（不暴露细节）
# ═══════════════════════════════════════════
