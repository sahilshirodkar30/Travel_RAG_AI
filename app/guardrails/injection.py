"""Goa-specific guardrail patterns.

Two separate checks:
- find_question_injection(): runs on every user question. Blocks injection attempts
  and clearly off-topic requests (poems, code, stocks, politics, medical advice).
- find_document_injection(): runs on uploaded files during ingestion. Blocks only
  instruction-hijacking text, so ordinary travel content always passes.
"""
import re

# Attempts to override the bot's instructions. Checked for questions AND documents.
INJECTION_PATTERNS = [
    r"\bignore (all |any |the |your )?(previous|above|prior|earlier) (instructions|rules|prompts?)\b",
    r"\bdisregard (all |any |the |your )?.{0,30}(instructions|rules|policy|guidelines)\b",
    r"\b(reveal|print|show|repeat|leak|output) .{0,30}(system prompt|hidden instructions|your instructions)\b",
    r"\byou are now (a|an|in|my|no longer)\b",
    r"\bdeveloper mode\b|\bjailbreak\b",
    r"<\s*/?\s*(script|iframe|object|embed)\b",
    r"\[\s*/?\s*(system|assistant)\s*\]|</?system>",
]

# Topics outside the Goa travel guide. Checked for QUESTIONS only.
OFF_TOPIC_PATTERNS = [
    r"\b(poem|poetry|song|lyrics|joke|essay|homework|story about)\b",
    r"\b(stocks?|shares? price|crypto|bitcoin|forex|investment)\b",
    r"\b(python|javascript|sql|java|code|debug|regex|api key)\b",
    r"\b(election|politic\w*|government policy)\b",
    r"\b(diagnos\w*|prescription|dosage|medical advice)\b",
]

# If a question mentions any of these, it is treated as travel-related and not off-topic.
TRAVEL_TERMS = re.compile(
    r"\b(goa|goan|beach\w*|hotel|hostel|bus|buses|train|ferry|taxi|cab|scooter|food|fish|"
    r"festival|trip|travel\w*|visit\w*|route|itinerary|stay|temple|church|fort|market|"
    r"pune|mumbai|mapusa|panjim|panaji|margao|calangute|baga|palolem|morjim|days?|budget)\b",
    re.IGNORECASE,
)

_INJECTION_RE = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]
_OFF_TOPIC_RE = [re.compile(p, re.IGNORECASE) for p in OFF_TOPIC_PATTERNS]


def _matches(regexes: list[re.Pattern], text: str) -> list[str]:
    return [r.pattern for r in regexes if r.search(text)]


def find_question_injection(question: str) -> list[str]:
    """Check a user question. Returns reasons for blocking, or an empty list if allowed."""
    hits = _matches(_INJECTION_RE, question)
    if hits:
        return hits
    if not TRAVEL_TERMS.search(question) and _matches(_OFF_TOPIC_RE, question):
        return ["off-topic: not about Goa travel"]
    return []


def find_document_injection(text: str) -> list[str]:
    """Check an uploaded file during ingestion. Only instruction-hijacking text is blocked."""
    return _matches(_INJECTION_RE, text)