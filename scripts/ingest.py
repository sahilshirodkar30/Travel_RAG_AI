"""Optional wrapper so you can run: python scripts/ingest.py"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import run_ingest  # noqa: E402

if __name__ == "__main__":
    run_ingest()