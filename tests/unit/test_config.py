"""Unit tests for configuration management."""

import pytest
from app.config import Settings


@pytest.mark.unit
class TestSettings:
    """Tests for Settings configuration."""
    
    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()
        assert settings.app_name == "Bharatam AI"
        assert settings.app_version == "0.1.0"
        assert settings.debug is True
        assert settings.session_timeout_minutes == 30
    
    def test_supported_languages(self):
        """Test supported languages configuration."""
        settings = Settings()
        assert "en" in settings.supported_languages
        assert "hi" in settings.supported_languages
    
    def test_vector_db_path(self):
        """Test vector database path configuration."""
        settings = Settings()
        assert settings.vector_db_path == "./data/vector_db"
    
    def test_api_keys_default_empty(self):
        """Test that API keys default to empty strings."""
        settings = Settings()
        assert settings.openai_api_key == ""
        assert settings.google_speech_api_key == ""
        assert settings.google_tts_api_key == ""
