"""Human review queue (L6). Low-confidence answers wait here for an admin to approve or edit."""
import json
import time
import uuid
from pathlib import Path

from app.cache.semantic_cache import cache_put
from app.config import get_settings


def _path() -> Path:
    return Path(get_settings().review_file)


def _read() -> list[dict]:
    p = _path()
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _write(items: list[dict]) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in items), encoding="utf-8")


def enqueue(question: str, draft: str, sources: list[str]) -> None:
    items = _read()
    items.append({
        "id": uuid.uuid4().hex[:8],
        "question": question,
        "draft": draft,
        "sources": sources,
        "status": "pending",
        "ts": time.time(),
    })
    _write(items)


def pending() -> list[dict]:
    return [i for i in _read() if i["status"] == "pending"]


def decide(item_id: str, approve: bool, edited_answer: str | None = None) -> None:
    items = _read()
    for item in items:
        if item["id"] == item_id and item["status"] == "pending":
            item["status"] = "approved" if approve else "rejected"
            if approve:
                # An approved answer is cached so similar questions get it next time
                cache_put(item["question"], edited_answer or item["draft"])
    _write(items)