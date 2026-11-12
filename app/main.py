import sys

from app.observability import setup_observability

def run_ingest() -> None:
    from app.rag.ingest import ingest_docs

    setup_observability()
    print(ingest_docs())


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "ingest":
        run_ingest()
    else:
        print("Usage: python -m app.main ingest")