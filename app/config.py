# app/config.py
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    #Pinecone
    pinecone_api_key: str = Field(...,description="Pinecone API Key")
    pinecone_index:str="goa-guide-travel-index"
    embed_model:str="llama-text-embed-v2"
    embed_dim:int = 1024

    #portkey gateway
    portkey_api_key:str=Field(...,description="Portkey API Key")
    portkey_url:str="https://api.portkey.ai/v1"
    portkey_config_fast:str=""
    portkey_config_smart:str=""
    fast_model:str=""
    smart_model:str="deepseek-chat"

    #observability
    logfire_token:str=""

    #rules
    rate_limit_per_min:int=Field(10,ge=1)
    cache_similarity:float=Field(.95,ge=0,le=1.0)
    cache_ttl_seconds:int = 7*24*3600
    retrieval_min_score:float = 0.0
    freshness_day:int=365

    #Paths
    docs_dir: str = str(ROOT_DIR/"data"/"knowledge")
    review_file: str = str(ROOT_DIR / "data" / "review_queue.jsonl")
    users_file: str = str(ROOT_DIR / "data" / "users.json")

    admin_emails: str = ""

    @property
    def admin_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.admin_emails.split(",") if e.strip()}

@lru_cache
def get_settings() -> Settings:
    return Settings()