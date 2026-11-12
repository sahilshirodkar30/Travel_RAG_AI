"""Pinecone connection: create the index if needed, and return a reusable index handle."""
from functools import lru_cache

from pinecone import Pinecone, ServerlessSpec

from app.config import get_settings


@lru_cache
def _client() -> Pinecone:
    return Pinecone(api_key=get_settings().pinecone_api_key)


def ensure_index() -> None:
    """Create the serverless index on first run if it does not exist."""
    s = get_settings()
    if not _client().has_index(s.pinecone_index):
        _client().create_index(
            name=s.pinecone_index,
            dimension=s.embed_dim,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )


@lru_cache
def get_index():
    """One index handle per process. Pass namespace='docs' or 'cache' on each call."""
    ensure_index()
    return _client().Index(get_settings().pinecone_index)