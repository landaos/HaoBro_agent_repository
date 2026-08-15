# ============================================
# Dockerfile - 生产环境容器镜像
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的部分：
# ═══════════════════════════════════════════
#
# 1. 多阶段构建：
#    - 阶段1（builder）:
#      FROM python:3.12-slim
#      - 安装 build 依赖（gcc, libpq-dev）
#      - pip install 项目依赖
#    - 阶段2（runtime）:
#      FROM python:3.12-slim
#      - 仅复制 site-packages 和源码
#      - 设置非 root 用户运行
#      - WORKDIR /app
#      - CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
#
# 2. 环境变量：
#    - PYTHONDONTWRITEBYTECODE=1
#    - PYTHONUNBUFFERED=1
#
# ═══════════════════════════════════════════
# 构建方式：
#   docker build -t agent-backend .
# ═══════════════════════════════════════════
