# ============================================
# logging_config.py - logging 结构化日志配置
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的代码：
# ═══════════════════════════════════════════
#
# 1. 配置日志（应用启动时初始化一次）：
#    import sys
#    from src.logger.logger import get_logger
#
#    def setup_logging():
#        logger = get_logger("agent", log_file="agent.log")
#
# ═══════════════════════════════════════════
# 使用方式：
#   from src.logger.logger import logger
#   logger.info(f"用户 {user_id} 发送消息: {message}")
#   logger.error("数据库连接失败")  # 自动记录异常栈
#
# 日志文件位置：logs/agent-2026-07-15.log
# ═══════════════════════════════════════════
