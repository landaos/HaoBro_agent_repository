# ============================================
# auth.py - 认证相关的 Pydantic 模型
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的模型（如需要认证的话）：
# ═══════════════════════════════════════════
#
# 1. LoginRequest(BaseModel)
#    - username: str
#    - password: str
#
# 2. TokenResponse(BaseModel)
#    - access_token: str
#    - token_type: str = "bearer"
#    - expires_in: int
#
# 3. TokenPayload(BaseModel 或直接 dict)
#    - sub: str（user_id）
#    - role: str
#    - exp: datetime
#
# ═══════════════════════════════════════════
# 如果不需要认证，此文件可以留空或删除
# ═══════════════════════════════════════════
