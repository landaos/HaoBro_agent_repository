# ============================================
# langsmith.py - LangSmith 初始化配置
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的代码：
# ═══════════════════════════════════════════
#
# 1. 初始化 LangSmith（应用启动时调用）：
#    import os
#    from src.config import settings
#
#    def setup_langsmith():
#        """配置 LangSmith 环境变量，用于 LLM 调用追踪与调试"""
#
#        # LangSmith 通过环境变量控制，设置即可自动生效
#        os.environ["LANGCHAIN_TRACING_V2"] = "true"        # 启用追踪
#        os.environ["LANGCHAIN_PROJECT"] = "agent-backend"   # 项目名称（LangSmith 控制台分组用）
#
#        # API 密钥（从 settings 中读取，安全存储）
#        # os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
#        # 注意：LANGSMITH_API_KEY 应配置在 .env 中：
#        #   LANGSMITH_API_KEY=ls_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
#        #   LANGSMITH_ENDPOINT=https://api.smith.langchain.com
#
#        # 采样率控制（生产环境可以只采样 10% 的请求以节省配额）
#        # os.environ["LANGCHAIN_TRACING_SAMPLING_RATE"] = "1.0"  # 1.0=全部追踪
#
#    # 可选：条件启用（开发环境可以关闭）
#    def setup_langsmith_if_enabled():
#        if settings.langsmith_api_key:
#            setup_langsmith()
#            logger.info("LangSmith 追踪已启用，项目：agent-backend")
#        else:
#            logger.info("LangSmith 未配置（LANGSMITH_API_KEY 为空），跳过追踪")
#
# ═══════════════════════════════════════════
# LangSmith 能干啥：
#   1. 追踪每次 LLM 调用的输入/输出/token 消耗
#   2. 可视化 Agent 的每一步决策（调了哪个 tool，返回了什么）
#   3. 对比不同 prompt 版本的效果
#   4. 生产环境问题回放
#
# 注册方式：免费版 https://smith.langchain.com 注册拿 API Key
# ═══════════════════════════════════════════
