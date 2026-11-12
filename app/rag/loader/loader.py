""" Read a supported file and return text """

import csv
import json
from pathlib import Path

from docx import Document
from openpyxl import load_workbook
from pypdf import PdfReader

SUPPORTED = {".json",".csv",".txt",".md",".docx",".pdf",".xlsx"}

def read_chunks(path:Path) -> list[str]:

    ext = path.suffix.lower()
    if ext not in SUPPORTED:
        raise ValueError(f"unsupported file type: {ext}")

    if ext == ".json":
        return _read_json(path)
    if ext == ".csv":
        return _read_csv(path)
    if ext in (".txt",".md"):
        return _read_text(path)
    if ext == ".docx":
        return _read_docx(path)
    if ext == ".pdf":
        return _read_pdf(path)

    return _read_xlxs(path)


def _read_json(path:Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    items = data if isinstance(data,list) else [data]
    out = []
    for item in items:
        text = item.get("text") if isinstance(item,dict) else None
        out.append(str(text) if text else json.dumps(item,ensure_ascii=False))

    return out

def _read_csv(path:Path) -> list[str]:
    with path.open(encoding="utf-8-sig",newline="") as f:
        rows = [
            "; ".join(f"{k} : {v}" for k,v in row.items() if k and v)
            for row in csv.DictReader(f)
        ]

    return [ r for r in rows if r.strip()]

def _read_text(path:Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig")
    return [ p.strip() for p in text.split("\n\n") if p.strip()]

def _read_docx(path:Path) -> list[str]:
    heading,out ="",[]
    for p in Document(str(path)).paragraphs:
        text = p.text.strip()
        if not text:
            continue

        if _is_heading(p):
            heading = text
        else:
            out.append(f"{heading}:{text}" if heading else text)

    return out

def _is_heading(paragraph) -> bool:
    style = (paragraph.style.name or "").lower() if paragraph.style else ""
    return style.startswith(("heading","title"))


def _read_pdf(path:Path) -> list[str]:
    out = []
    for n,page in enumerate(PdfReader(str(path)).pages,1):
        text = (page.extract_text() or "").strip()
        if text:
            out.append(f"{text} (page {n})")

    return out


def _read_xlxs(path:Path) -> list[str]:
    wb = load_workbook(str(path),read_only=True,data_only=True)
    out = []
    for sheet in wb.worksheets:
        rows = sheet.iter_rows(values_only=True)
        header = next(rows,None)
        if not header:
            continue
        names = [ str(h) for h in header]
        for row in rows:
            pairs = [f"{k}:{v}" for k,v in zip(names,row) if v not in (None,"")]
            if pairs:
                out.append(f"{sheet.title} | "+"; ".join(pairs))

    wb.close()
    return out