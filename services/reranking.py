
import os
from functools import lru_cache

import logfire
from flashrank import Ranker , RerankRequest

MODEL_NAME =  "ms-marco-MiniLM-L-12-v2"
CACHE_DIR = os.getenv("FLASHRANK_CACHE",".cache/flashrank")

@lru_cache
def _ranker() -> Ranker:
    logfire.info("loading FlashRank model",model=MODEL_NAME)
    return Ranker(model_name=MODEL_NAME,cache_dir=CACHE_DIR)

def rerank(query:str ,chunks:list[dict],top_n:int=4) -> list[dict]:

    if not chunks :
        return []

    passages= [{"id":i , "text":c["text"]} for i,c in enumerate(chunks)]

    try:
        with logfire.span("rerank",candidates=len(chunks)):
            result = _ranker().rerank(RerankRequest(query=query,passages=passages))
    except Exception as e:
        logfire.warn("rerank failed , using vector order",error=str(e))
        return chunks[:top_n]

    ranked = []
    for r in result[:top_n]:
        chunk = dict(chunks[r["id"]])
        chunk["rerank_score"] = float(r["score"])
        ranked.append(chunk)

    return ranked