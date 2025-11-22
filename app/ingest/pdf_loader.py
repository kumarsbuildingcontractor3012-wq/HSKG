"""PDF loader using PyMuPDF with sliding-window chunking.

Produces deterministic, overlapping chunks for downstream embedding.
This module intentionally keeps logic small and offline-only.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import fitz  # PyMuPDF


def extract_pdf_text(path: str) -> str:
    """Return full document text for *path* (raises FileNotFoundError if missing)."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")
    doc = fitz.open(str(p))
    parts: list[str] = []
    for page in doc:
        parts.append(page.get_text())
    return "\n".join(parts)


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 128) -> List[str]:
    """Sliding-window chunking by characters (simple, deterministic).

    Args:
        text: raw document text.
        chunk_size: size of returned chunks (chars).
        overlap: overlap between successive chunks (chars).
    """
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")
    chunks: list[str] = []
    start = 0
    text_len = len(text)
    step = chunk_size - overlap
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(text[start:end].strip())
        if end == text_len:
            break
        start += step
    return [c for c in chunks if c]


def extract_pdf_chunks(path: str, chunk_size: int = 512, overlap: int = 128) -> List[str]:
    """Convenience: read PDF and return list of overlapping chunks."""
    text = extract_pdf_text(path)
    return chunk_text(text, chunk_size=chunk_size, overlap=overlap)
