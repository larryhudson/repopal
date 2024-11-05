from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Existing settings...
    SLACK_SIGNING_SECRET: str = ''
    SLACK_BOT_TOKEN: str = ''
    SLACK_APP_ID: str = ''
    PROJECT_NAME: str = "FastAPI Project"
    DATABASE_URL: str = "sqlite:///./test.db"  # Default for testing
    REDIS_URL: str = "redis://localhost:6379"  # Default for testing
    TESTING: bool = False

    # LLM Settings
    LLM_MODEL: str = "claude-3-haiku-20240307"  # Default model
    LLM_API_KEY: str = ""     # API key for the model provider
    LLM_PROVIDER: str = "anthropic"  # Provider (openai, azure, anthropic, etc)

    model_config = {
        "env_file": ".env"
    }


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
