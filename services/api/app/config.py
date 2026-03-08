from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import os
from typing import List, Optional

from pydantic import BaseModel, Field


def _default_database_path() -> Path:
    return Path(os.getenv("DATABASE_PATH", str(Path(os.getenv("DATA_DIR", "data")) / "chess_tutor.sqlite3")))


def _cors_allow_origins() -> List[str]:
    value = os.getenv("CORS_ALLOW_ORIGINS")
    if not value:
        return ["*"]
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseModel):
    app_name: str = "AI Chess Tutor API"
    data_dir: Path = Field(default_factory=lambda: Path(os.getenv("DATA_DIR", "data")))
    database_path: Path = Field(default_factory=_default_database_path)
    stockfish_path: Optional[str] = os.getenv("STOCKFISH_PATH")
    ollama_base_url: Optional[str] = os.getenv("OLLAMA_BASE_URL")
    llm_summary_provider: Optional[str] = os.getenv("LLM_SUMMARY_PROVIDER")
    llm_summary_model: Optional[str] = os.getenv("LLM_SUMMARY_MODEL")
    llm_summary_api_key: Optional[str] = os.getenv("LLM_SUMMARY_API_KEY")
    llm_move_provider: Optional[str] = os.getenv("LLM_MOVE_PROVIDER")
    llm_move_model: Optional[str] = os.getenv("LLM_MOVE_MODEL")
    llm_move_api_key: Optional[str] = os.getenv("LLM_MOVE_API_KEY")
    llm_chat_provider: Optional[str] = os.getenv("LLM_CHAT_PROVIDER")
    llm_chat_model: Optional[str] = os.getenv("LLM_CHAT_MODEL")
    llm_chat_api_key: Optional[str] = os.getenv("LLM_CHAT_API_KEY")
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    cors_allow_origins: List[str] = Field(default_factory=_cors_allow_origins)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
