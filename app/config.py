"""Configuration management for Bharatam AI application."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Settings
    app_name: str = "Bharatam AI"
    app_version: str = "0.1.0"
    debug: bool = True
    
    # API Keys (to be added in later tasks)
    openai_api_key: str = ""
    google_speech_api_key: str = ""
    google_tts_api_key: str = ""
    
    # Session Settings
    session_timeout_minutes: int = 30
    
    # Supported Languages
    supported_languages: List[str] = ["en", "hi"]
    
    # Vector Database Settings
    vector_db_path: str = "./data/vector_db"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
