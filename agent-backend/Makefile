# ============================================
# Makefile - 常用命令一键执行
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的命令：
# ═══════════════════════════════════════════
#
# 变量定义：
#   PYTHON   = python
#   UVICORN  = uvicorn
#   ALEMBIC  = alembic
#
# 1. 开发环境（.PHONY: dev）
#    dev:
#        $(UVICORN) src.main:app --reload --host 0.0.0.0 --port 8000
#
# 2. 生产启动（.PHONY: start）
#    start:
#        $(UVICORN) src.main:app --host 0.0.0.0 --port 8000 --workers 4
#
# 3. 安装依赖（.PHONY: install）
#    install:
#        pip install -e ".[dev]"
#
# 4. 数据库迁移（.PHONY: migrate）
#    migrate:
#        $(ALEMBIC) upgrade head
#    migrate-new:
#        $(ALEMBIC) revision --autogenerate -m "$(message)"
#    migrate-reset:
#        $(ALEMBIC) downgrade base && $(ALEMBIC) upgrade head
#
# 5. 测试（.PHONY: test）
#    test:
#        pytest tests/ -v --cov=src --cov-report=term-missing
#    test-file:
#        pytest tests/$(file) -v
#
# 6. 代码检查（.PHONY: lint）
#    lint:
#        ruff check src/
#    lint-fix:
#        ruff check src/ --fix
#
# 7. Docker 相关（.PHONY: docker-up docker-down）
#    docker-up:
#        docker compose up -d
#    docker-down:
#        docker compose down
#
# 8. 预提交安装（.PHONY: pre-commit）
#    pre-commit:
#        pre-commit install
#
# ═══════════════════════════════════════════
# 使用示例：
#   make dev          # 启动开发服务器
#   make test         # 运行测试
#   make lint         # 代码检查
#   make migrate      # 执行数据库迁移
# ═══════════════════════════════════════════
