import hashlib
import time

from app.config import get_settings
from services.embedding import embed_query
from services.pinecone_store import get_index

NAMESPACE = "cache"

def cache_get(question:str) -> str|None:
    s = get_settings()
    res = get_index().query(
        vector=embed_query(question),
        top_k=1,
        namespace=NAMESPACE,
        include_metadata=True,
        filter = {"ts":{"$gte":time.time() - s.cache_ttl_seconds}}
    )

    if res.matches and res.matches[0].score >= s.cache_similarity:
        return res.matches[0].metadata["answer"]

    return None

def cache_put(question:str,answer:str) -> None:
    rid = hashlib.sha256(question.lower().strip().encode()).hexdigest()[:32]
    get_index().upsert(
        vectors = [{
            "id":rid,
            "values":embed_query(question),
            "metadata":{"answer":answer,"ts":time.time()}
        }],
        namespace=NAMESPACE
    )