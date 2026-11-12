from pathlib import Path

root = Path(".")

FILES = [
    # project root
    "README.md",
    "requirements.txt",
    "Dockerfile",
    ".env.example",
    ".gitignore",

    # app
    "app/__init__.py",
    "app/main.py",
    "app/config.py",
    "app/observability.py",

    # guardrails (L3)
    "app/guardrails/__init__.py",
    "app/guardrails/colang_rules.py",
    "app/guardrails/rails.py",
    "app/guardrails/injection.py",
    "app/guardrails/config/config.yml",
    "app/guardrails/config/rails.co",

    # gateway (L7, L8)
    "app/gateway/__init__.py",
    "app/gateway/gateway.py",
    "app/gateway/router.py",

    # cache (L4)
    "app/cache/__init__.py",
    "app/cache/semantic_cache.py",

    # rag (L5)
    "app/rag/__init__.py",
    "app/rag/ingest.py",
    "app/rag/chunking/__init__.py",
    "app/rag/chunking/splitter.py",
    "app/rag/loader/__init__.py",
    "app/rag/loader/loader.py",

    # human in the loop (L6)
    "app/hitl/__init__.py",
    "app/hitl/review_queue.py",

    # security (L1, L2)
    "app/security/__init__.py",
    "app/security/auth.py",
    "app/security/rate_limiter.py",

    # agent (LangGraph)
    "app/agent/__init__.py",
    "app/agent/state.py",
    "app/agent/graph.py",
    "app/agent/nodes/__init__.py",
    "app/agent/nodes/planner.py",
    "app/agent/nodes/retriever.py",
    "app/agent/nodes/responder.py",

    # shared services
    "services/__init__.py",
    "services/embedding.py",
    "services/pinecone_store.py",
    "services/reranking.py",

    # UI
    "UI/streamlit_UI.py",

    # evals (L11)
    "evals/golden.jsonl",
    "evals/run_evals.py",

    # scripts
    "scripts/ingest.py",

    # data
    "data/docs/goa_beaches.md",
    "data/users.json",

    # tests
    "tests/__init__.py",
    "tests/test_injection.py",
]

FOLDERS = [
    "data/docs",
]

for folder in FOLDERS:
    (root / folder).mkdir(parents=True, exist_ok=True)

for f in FILES:
    path = root / f
    path.parent.mkdir(parents=True, exist_ok=True)  # create parent folders first
    path.touch(exist_ok=True)

print("✅ Project structure created successfully.")