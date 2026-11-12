
from functools import lru_cache
from pinecone import Pinecone
from app.config import get_settings
from services.pinecone_store import _client

BATCH_SIZE = 90

def embed(texts:list[str],input_type:str) -> list[list[float]]:
    s = get_settings()
    vectors: list[list[float]] = []

    for i in range(0,len(texts),BATCH_SIZE):
        res = _client().inference.embed(
            model=s.embed_model,
            inputs = texts[i:i+BATCH_SIZE],
            parameters={"input_type": input_type, "truncate": "END"}
        )
        vectors.extend(e.values for e in res)
    
    return vectors

def embed_passages(texts:list[str])-> list[list[float]]:
    return embed(texts,"passage")

def embed_query(text:str) -> list[float]:
    return embed([text],"query")[0]