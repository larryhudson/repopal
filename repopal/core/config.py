from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Project"
    DATABASE_URL: str = "sqlite:///./test.db"  # Default for testing
    REDIS_URL: str = "redis://localhost:6379"  # Default for testing
    TESTING: bool = False
    
    # OpenAI Settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"

    model_config = {
        "env_file": ".env"
    }


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
