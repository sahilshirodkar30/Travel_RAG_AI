import hashlib
from pathlib import Path

import logfire

from app.config import get_settings
from app.guardrails.injection import find_document_injection
from app.rag.chunking.splitter import split_text
from app.rag.loader.loader import SUPPORTED, read_chunks
from services.embedding import embed_passages
from services.pinecone_store import get_index

NAMESPACE = "goa-guide-docs"
UPSERT_BATCH = 100


@logfire.instrument("ingest_docs")
def ingest_docs(folder: str | None = None) -> dict:
    folder = folder or get_settings().docs_dir
    report = {"chunks": 0, "files": 0, "quarantined": [], "skipped": []}
    records: list[dict] = []

    paths = [
        p for p in sorted(Path(folder).rglob("*"))
        if p.is_file() and p.suffix.lower() in SUPPORTED
    ]
    logfire.info("Found {count} supported files", count=len(paths), folder=folder)

    for path in paths:
        with logfire.span("ingest.file", file=path.name, file_type=path.suffix.lower()) as span:
            try:
                pieces = read_chunks(path)
            except Exception as e:
                report["skipped"].append(f"{path.name}: {e}")
                logfire.warn("File skipped: could not read", file=path.name, error=str(e))
                continue

            if find_document_injection("\n".join(pieces)):
                report["quarantined"].append(path.name)
                logfire.warn("File quarantined: possible prompt injection", file=path.name)
                continue

            chunks = [part for piece in pieces for part in split_text(piece)]

            if not chunks:
                report["skipped"].append(f"{path.name}: no text found")
                logfire.warn("File skipped: no text found", file=path.name)
                continue

            vectors = embed_passages(chunks)
            updated_at = path.stat().st_mtime
            for i, (text, vector) in enumerate(zip(chunks, vectors)):
                rid = hashlib.sha3_256(f"{path.name}:{i}".encode()).hexdigest()[:32]
                records.append({
                    "id": rid,
                    "values": vector,
                    "metadata": {
                        "text": text,
                        "source": path.name,
                        "updated_at": updated_at,
                    },
                })

            report["files"] += 1
            span.set_attribute("chunks", len(chunks))
            logfire.info("File embedded", file=path.name, chunks=len(chunks))

    index = get_index()

    with logfire.span("ingest.replace_namespace", namespace=NAMESPACE, records=len(records)):
        try:
            index.delete(delete_all=True, namespace=NAMESPACE)
        except Exception as e:
            # Usually means the namespace is empty on first run. Safe to continue.
            logfire.info("Namespace clear skipped", namespace=NAMESPACE, reason=str(e))

        for b in range(0, len(records), UPSERT_BATCH):
            batch = records[b:b + UPSERT_BATCH]
            index.upsert(vectors=batch, namespace=NAMESPACE)
            logfire.debug("Upserted batch", batch_start=b, batch_size=len(batch))

    report["chunks"] = len(records)
    logfire.info(
        "Ingestion finished",
        files=report["files"],
        chunks=report["chunks"],
        quarantined=len(report["quarantined"]),
        skipped=len(report["skipped"]),
    )
    return report