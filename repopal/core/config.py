from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Project"
    DATABASE_URL: str = "sqlite:///./test.db"  # Default for testing
    REDIS_URL: str = "redis://localhost:6379"  # Default for testing
    TESTING: bool = False
    
    # LLM Settings
    LLM_MODEL: str = "gpt-4"  # Default model
    LLM_API_KEY: str = ""     # API key for the model provider
    LLM_PROVIDER: str = "openai"  # Provider (openai, azure, anthropic, etc)

    model_config = {
        "env_file": ".env"
    }


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
