from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = ConfigDict(
        extra='ignore',
        env_file='.env',
        case_sensitive=True
    )
    
    DATABASE_URL: str = "postgresql://omnissiah:omnissiah@postgres:5432/omnissiah"
    FASTAPI_ENV: str = "development"
    FASTAPI_DEBUG: bool = True
    
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""
    
    OPENAI_API_KEY: str = ""
    DEEP_AGENT_MODEL: str = "gpt-4o-mini"
    
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000


@lru_cache()
def get_settings():
    return Settings()
