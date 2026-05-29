from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ai_provider: str = Field(default="auto", alias="AI_PROVIDER")
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-v4-flash", alias="DEEPSEEK_MODEL")
    github_token: str = Field(default="", alias="GITHUB_TOKEN")
    max_files: int = Field(default=20, alias="MAX_FILES")
    max_patch_chars: int = Field(default=30000, alias="MAX_PATCH_CHARS")
    request_timeout: int = Field(default=60, alias="REQUEST_TIMEOUT")
    ai_timeout_seconds: int = Field(default=30, alias="AI_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
