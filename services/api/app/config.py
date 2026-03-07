from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import os
from typing import Optional

from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = "AI Chess Tutor API"
    data_dir: Path = Field(default_factory=lambda: Path("data"))
    database_path: Path = Field(default_factory=lambda: Path("data/chess_tutor.sqlite3"))
    stockfish_path: Optional[str] = os.getenv("STOCKFISH_PATH")
    ollama_base_url: Optional[str] = os.getenv("OLLAMA_BASE_URL")
    ollama_model: Optional[str] = os.getenv("OLLAMA_MODEL")
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "8000"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
