from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    app_name: str = "LPU Library AI"
    database_url: str = ""
    ai_gateway_api_key: str = ""
    chat_model: str = "openai/gpt-4o-mini"
    embedding_model: str = "openai/text-embedding-3-small"
    top_k: int = 6
    chunk_size: int = 1000
    chunk_overlap: int = 160
    max_upload_mb: int = 4
    admin_ingest_key: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

def local_path(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else BASE_DIR / p
