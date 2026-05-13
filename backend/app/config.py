from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "app" / "raw"
WIKI_DIR = BASE_DIR / "app" / "wiki"


class Settings(BaseSettings):
    # 数据库
    database_url: str = "postgresql+asyncpg://knowableplat:knowableplat@localhost:5432/knowableplat"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM
    anthropic_base_url: str = "https://open.bigmodel.cn/api/anthropic"
    anthropic_auth_token: str = ""
    anthropic_model: str = "glm-5.1"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # URL 抓取
    jina_reader_url: str = "https://r.jina.ai/"
    firecrawl_api_url: str = ""
    firecrawl_api_key: str = ""

    # 应用
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True

    model_config = {"env_file": str(BASE_DIR.parent / ".env"), "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()


def ensure_dirs() -> None:
    for d in [RAW_DIR, WIKI_DIR]:
        d.mkdir(parents=True, exist_ok=True)
