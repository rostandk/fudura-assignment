"""
config.py
This module defines the Settings class for application configuration.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from environment or .env file.
    """
    log_level: str = "DEBUG"  
    telemetry_dir: str = "data/telemetry"
    assets_file: str = "data/assets/assets.json"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/fudura_monitoring"


    # Configure loading of .env and its encoding
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )

# Instantiate once for the whole app
settings = Settings()