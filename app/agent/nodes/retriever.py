
import time

import logfire
from app.agent.state import ChatState
from app.config import get_settings
from services.embedding import embed_query
from services.pinecone_store import get_index
from services.reranking import rerank

CANDIDATES = 10
KEEP = 4

def retrieve_node(state:ChatState) -> dict:
    s = get_settings()
    question = state["question"]
    print("entering retriever layer")
    with logfire.span("retrieve",candidates=CANDIDATES):
        res = get_index().query(
            vector = embed_query(question),
            top_k=CANDIDATES,
            namespace="goa-guide-docs",
            include_metadata=True
        )

    now = time.time()
    max_age = s.freshness_day * 86400
    candidates = [
        {
            "text":m.metadata["text"],
            "source":m.metadata["source"],
            "updated_at": m.metadata["updated_at"],
            "score":m.score,
            "stale":(now - m.metadata["updated_at"]) > max_age
        }
        for m in res.matches
    ]

    chunks = rerank(question,candidates,top_n=KEEP)

    best = chunks[0].get("rerank_score") if chunks else None
    need_review = best is None or best < s.retrieval_min_score
    return {"chunks":chunks,"need_review":need_review}