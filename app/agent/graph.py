"""LangGraph flow and the public entry point handle_question(), used by the UI and the API."""
import time

import logfire
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agent.nodes.planner import plan_node
from app.agent.nodes.responder import REFUSAL, respond_node
from app.agent.nodes.retriever import retrieve_node
from app.agent.state import ChatState
from app.cache.semantic_cache import cache_get, cache_put
from app.guardrails.injection import find_question_injection
from app.hitl.review_queue import enqueue
from app.security.rate_limiter import limiter

MAX_QUESTION_CHARS = 1000
REVIEW_MSG = ("I'm not fully sure about this one, so I've sent it to our local experts "
              "to verify. Please check back soon.")
PREVIEW_CHARS = 80


def _preview(text: str | None) -> str:
    """Short, single-line preview for logs."""
    if not text:
        return ""
    flat = " ".join(text.split())
    return flat[:PREVIEW_CHARS] + ("..." if len(flat) > PREVIEW_CHARS else "")


# ---- nodes ----

def cache_node(state: ChatState) -> dict:
    # Cached answers ignore earlier turns, so skip the cache for follow-up questions
    if state.get("has_history"):
        logfire.info("cache skipped, follow-up question")
        return {"cached": False}

    start = time.perf_counter()
    with logfire.span("node.cache", question=_preview(state["question"])) as span:
        hit = cache_get(state["question"])
        span.set_attribute("hit", bool(hit))
        span.set_attribute("duration_ms", round((time.perf_counter() - start) * 1000, 1))
    if hit:
        logfire.info("cache hit, skipping LLM", answer_chars=len(hit))
        return {"answer": hit, "cached": True}
    logfire.info("cache miss")
    return {"cached": False}


def plan_node_logged(state: ChatState) -> dict:
    with logfire.span("node.plan", question=_preview(state["question"])) as span:
        update = plan_node(state)
        span.set_attribute("tier", update.get("tier"))
    logfire.info("planner chose tier", tier=update.get("tier"))
    return update


def retrieve_node_logged(state: ChatState) -> dict:
    with logfire.span("node.retrieve", question=_preview(state["question"])) as span:
        update = retrieve_node(state)
        chunks = update.get("chunks", [])
        span.set_attribute("chunk_count", len(chunks))
        span.set_attribute("needs_review", update.get("needs_review"))

    scores = [round(c.get("rerank_score", 0.0), 3) for c in chunks]
    logfire.info(
        "retrieval finished",
        chunk_count=len(chunks),
        sources=sorted({c["source"] for c in chunks}),
        rerank_scores=scores,
        stale_chunks=sum(1 for c in chunks if c.get("stale")),
        needs_review=update.get("needs_review"),
    )
    return update


def respond_node_logged(state: ChatState) -> dict:
    with logfire.span("node.respond", tier=state.get("tier")) as span:
        update = respond_node(state)
        span.set_attribute("blocked", bool(update.get("blocked")))
        span.set_attribute("degraded", bool(update.get("degraded")))
        span.set_attribute("needs_review", bool(update.get("needs_review")))

    logfire.info(
        "response generated",
        answer_chars=len(update.get("answer", "")),
        answer_preview=_preview(update.get("answer")),
        blocked=bool(update.get("blocked")),
        degraded=bool(update.get("degraded")),
        needs_review=bool(update.get("needs_review")),
    )
    return update


def review_node(state: ChatState) -> dict:
    sources = sorted({c["source"] for c in state.get("chunks", [])})
    with logfire.span("node.review", sources=sources):
        enqueue(state["question"], state.get("answer", ""), sources)
    logfire.info("sent to human review queue", sources=sources)
    return {"answer": REVIEW_MSG}


def remember_node(state: ChatState) -> dict:
    """Store this turn's answer in the thread history. Every path ends here."""
    return {"messages": [AIMessage(content=state.get("answer", ""))]}


# ---- routing ----

def _route_after_cache(state: ChatState) -> str:
    route = "hit" if state.get("cached") else "miss"
    logfire.debug("route after cache", route=route)
    return route


def _route_after_respond(state: ChatState) -> str:
    route = "review" if state.get("needs_review") else "done"
    logfire.debug("route after respond", route=route)
    return route


# ---- graph wiring ----

def build_graph():
    g = StateGraph(ChatState)
    g.add_node("cache", cache_node)
    g.add_node("plan", plan_node_logged)
    g.add_node("retrieve", retrieve_node_logged)
    g.add_node("respond", respond_node_logged)
    g.add_node("review", review_node)
    g.add_node("remember", remember_node)

    g.set_entry_point("cache")
    g.add_conditional_edges("cache", _route_after_cache, {"hit": "remember", "miss": "plan"})
    g.add_edge("plan", "retrieve")
    g.add_edge("retrieve", "respond")
    g.add_conditional_edges("respond", _route_after_respond, {"review": "review", "done": "remember"})
    g.add_edge("review", "remember")
    g.add_edge("remember", END)
    return g.compile(checkpointer=MemorySaver())


graph = build_graph()


# ---- history helpers ----

def get_history_count(thread_id: str) -> int:
    """Number of earlier questions in this thread (each turn is one question and one answer)."""
    snapshot = graph.get_state({"configurable": {"thread_id": thread_id}})
    messages = snapshot.values.get("messages", []) if snapshot.values else []
    return len(messages) // 2


# ---- public entry point ----

def _result(answer: str, sources: list[str] | None = None, blocked: bool = False,
            history_count: int = 0) -> dict:
    return {
        "answer": answer,
        "sources": sources or [],
        "blocked": blocked,
        "history_count": history_count,
    }


def handle_question(user_id: str, question: str, thread_id: str) -> dict:
    started = time.perf_counter()
    log = logfire.with_tags("chat")

    log.info("question received", user_id=user_id, thread_id=thread_id,
             question=_preview(question), length=len(question))

    if len(question) > MAX_QUESTION_CHARS:
        log.warn("question too long", length=len(question), limit=MAX_QUESTION_CHARS)
        return _result("Please keep your question shorter than 1000 characters.")

    if not limiter.allow(user_id):
        log.warn("rate limited", user_id=user_id)
        return _result("You're asking too fast. Please wait a minute.")

    matches = find_question_injection(question)
    if matches:
        log.warn("prompt injection blocked", user_id=user_id, patterns=matches)
        return _result(REFUSAL, blocked=True)

    previous = get_history_count(thread_id)
    config = {"configurable": {"thread_id": thread_id}}

    # Every field is set on every turn, so nothing carries over from the last question
    turn_input = {
        "question": question,
        "messages": [HumanMessage(content=question)],
        "has_history": previous > 0,
        "cached": False,
        "needs_review": False,
        "blocked": False,
        "degraded": False,
        "chunks": [],
        "answer": "",
    }

    with logfire.span("chat.graph", user_id=user_id, previous_turns=previous) as span:
        out = graph.invoke(turn_input, config)
        span.set_attribute("cached", bool(out.get("cached")))
        span.set_attribute("needs_review", bool(out.get("needs_review")))
        span.set_attribute("blocked", bool(out.get("blocked")))

    answer = out.get("answer") or "Sorry, I couldn't prepare an answer. Please try again."
    if not out.get("answer"):
        log.error("graph finished without an answer", state_keys=sorted(out.keys()))

    blocked = bool(out.get("blocked"))
    sources = [] if blocked else sorted({c["source"] for c in out.get("chunks", [])})

    cacheable = (out.get("chunks") and not out.get("cached") and not out.get("needs_review")
                 and not out.get("degraded") and not blocked and previous == 0)
    if cacheable:
        cache_put(question, answer)
        log.info("answer cached", answer_chars=len(answer))

    history_count = get_history_count(thread_id)
    log.info(
        "question finished",
        user_id=user_id,
        total_ms=round((time.perf_counter() - started) * 1000, 1),
        from_cache=bool(out.get("cached")),
        blocked=blocked,
        history_count=history_count,
        sources=sources,
        answer_preview=_preview(answer),
    )
    return _result(answer, sources, blocked, history_count)