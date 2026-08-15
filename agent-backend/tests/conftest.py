# ============================================
# conftest.py - pytest 测试配置与 fixtures
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的内容：
# ═══════════════════════════════════════════
#
# 1. 测试数据库 fixtures（使用测试专用 PostgreSQL）：
#    - 创建测试引擎和会话
#    - 每次测试前创建所有表，测试后 drop 所有表
#
# 2. 测试 Redis fixtures（可选）：
#    - 使用 fakeredis（模拟 Redis）代替真实 Redis
#    - pytest.fixture 注入 FakeRedis()
#
# 3. 测试客户端 fixture：
#    - @pytest_asyncio.fixture
#    - 创建 TestClient（httpx.AsyncClient）
#    - 使用 FastAPI 应用的 TESTING 模式
#
# 4. 测试数据 fixtures：
#    - sample_conversation: 创建测试用的会话记录
#    - sample_messages: 创建测试用的消息记录
#
# ═══════════════════════════════════════════
# pytest-asyncio 配置：
#   在 pyproject.toml 中加：
#   [tool.pytest.ini_options]
#   asyncio_mode = "auto"
# ═══════════════════════════════════════════
