"""应用配置 — 从 .env 读取，Python 代码统一从这里取"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── 运行环境 ──
    app_env: str = Field("development", validation_alias="APP_ENV")

    # ── JWT ──
    secret_key: str = Field(..., validation_alias="SECRET_KEY")
    algorithm: str = Field("HS256", validation_alias="ALGORITHM")
    access_token_expire_hours: int = Field(24, validation_alias="ACCESS_TOKEN_EXPIRE_HOURS")

    # ── LLM（阿里云 DashScope） ──
    ali_access_key_secret: str = Field("", validation_alias="ALIYUN_ACCESS_KEY_SECRET")
    ali_base_url: str = Field("", validation_alias="ALIYUN_BASE_URL")

    # ── LLM（DeepSeek） ──
    deepseek_api_key: str = Field("", validation_alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field("", validation_alias="DEEPSEEK_BASE_URL")

    # ── 本地应用路径（可选，自动扫描不到时手动指定） ──
    kugou_path: str = Field("", validation_alias="KUGOU_PATH")

    # ── PostgreSQL ──
    db_host: str = Field("localhost", validation_alias="DB_HOST")
    db_port: int = Field(5432, validation_alias="DB_PORT")
    db_name: str = Field("agent_db", validation_alias="DB_NAME")
    db_user: str = Field("agent_user", validation_alias="DB_USER")
    db_password: str = Field("", validation_alias="DB_PASSWORD")

    @property
    def db_url(self):
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def db_url_sync(self):
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def pgvector_url(self):
        """PGVector 同步连接字符串（langchain_postgres 使用 psycopg 驱动）"""
        return f"postgresql+psycopg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # ── Redis ──
    redis_host: str = Field("localhost", validation_alias="REDIS_HOST")
    redis_port: int = Field(6379, validation_alias="REDIS_PORT")
    redis_db: int = Field(0, validation_alias="REDIS_DB")

    @property
    def redis_url(self):
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ── LangSmith ──
    langchain_tracing_v2: bool = Field(False, validation_alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: str = Field("", validation_alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field("", validation_alias="LANGCHAIN_PROJECT")

    # 聊天模型名称
    chat_model_name: str = Field("", validation_alias="CHAT_MODEL_NAME")

    # Ollama模型名称
    ollama_chat_model_name: str = Field("", validation_alias="OLLAMA_CHAT_MODEL_NAME")

    # 向量模型名称
    vector_model_name: str = Field("", validation_alias="TEXT_EMBEDDING_MODEL_NAME")

    # 重排序模型名称
    reranker_model_name: str = Field("", validation_alias="RERANKER_MODEL_NAME")

    # 限流配置
    rate_limit_enabled: str = Field("true", validation_alias="RATE_LIMIT_ENABLED")


settings = Settings()
