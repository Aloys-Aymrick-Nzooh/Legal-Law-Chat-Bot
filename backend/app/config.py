"""Application configuration."""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/legal_chatbot"
    )

    # Ollama (for chat)


   
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "")

    # GraphRAG
    graphrag_data_dir: str = os.getenv("GRAPHRAG_DATA_DIR", "/app/graphrag_data")

    # App
    app_name: str = "Legal Chatbot"
    debug: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
