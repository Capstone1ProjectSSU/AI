from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Server settings
    app_title: str = "HiScore Queueable Tasks and LLM-Chart API"
    app_version: str = "1.0.0"
    app_description: str = "Formal API for long-running music processing tasks with a unified queueing interface"

    # Celery settings
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # File storage settings
    upload_dir: str = "./uploads"
    output_dir: str = "./outputs"

    # Task settings
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    supported_audio_formats: list[str] = [
        "mp3", "wav", "ogg", "flac", "m4a", "aac", "wma"
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
