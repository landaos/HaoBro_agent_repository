# ============================================
# privacy_filter.py - 数据隐私过滤与脱敏
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的代码：
# ═══════════════════════════════════════════
#
# 一、PII（个人身份信息）检测模式：
#
#    PII_PATTERNS = {
#        "phone":     (r"1[3-9]\d{9}",              "手机号"),
#        "id_card":   (r"\d{17}[\dXx]",              "身份证号"),
#        "email":     (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "邮箱"),
#        "bank_card": (r"\d{16,19}",                 "银行卡号"),
#        "ip":        (r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "IP地址"),
#    }
#
# 二、脱敏函数：
#
#    def mask_pii(text: str) -> tuple[str, list[dict]]:
#        """将文本中的 PII 脱敏，返回 (脱敏后文本, 脱敏记录)
#        手机号：138****8000
#        身份证：110***************
#        邮箱：u***@example.com
#        """
#
#    def mask_pii_log(text: str) -> str:
#        """日志专用脱敏（只保留类型信息，不保留部分明文）
#        手机号 → [PII:手机号]
#        """
#
# 三、日志过滤器：
#
#    class PrivacyFilter(logging.Filter):
#        """在日志输出前自动脱敏"""
#        def filter(self, record):
#            record.msg = mask_pii_log(record.msg)
#            return True
#
# 四、数据库存储过滤器：
#
#    class PrivacyMiddleware(BaseHTTPMiddleware):
#        """在请求进入 agent 前脱敏，在响应返回前脱敏"""
#        async def dispatch(self, request, call_next):
#            # 请求进来时：记录原始输入但不记录 PII
#            # 让 response 经过脱敏
#            response = await call_next(request)
#            # 如果响应体包含脱敏后的内容，确保正确
#            return response
#
# ═══════════════════════════════════════════
# 合规要求（中国个人信息保护法）：
#   1. 日志中不得包含明文 PII
#   2. 数据库中 PII 字段必须加密或脱敏
#   3. 用户有权要求删除其个人数据
#
# 建议用 logging 的 filter 机制：
#   logger.add("logs/agent.log", filter=privacy_filter)
# ═══════════════════════════════════════════
