"""Create embeddings for extracted concepts and optionally build FAISS index.

This script:
 - loads UX feedbacks from `Ux_data.csv`
 - chunks the provided PDF (`100_websites_compressed_11zon.pdf`)
 - extracts concept candidates (entities + noun-chunks)
 - deduplicates concept texts and batches them through `SentenceEmbedder`
 - saves `results/concept_texts.json` and `results/concept_embeddings.npy`
 - optionally builds a FAISS index (if `faiss` is installed)

The script is defensive: if model downloads or heavy libs are missing it
prints clear instructions rather than crashing.
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path
from typing import List

import numpy as np

from app.ingest.csv_loader import load_feedback_from_csv
from app.ingest.pdf_loader import extract_pdf_chunks
from app.nlp.concept_extractor import extract_concepts

try:
    from app.models.embedding import SentenceEmbedder
except Exception as exc:  # pragma: no cover - surface helpful error
    SentenceEmbedder = None  # type: ignore


def batch(iterable: List[str], size: int):
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    csv_path = root / "Ux_data.csv"
    pdf_path = root / "100_websites_compressed_11zon.pdf"
    out_dir = root / "results"
    out_dir.mkdir(exist_ok=True)

    # Load data
    try:
        feedbacks = load_feedback_from_csv(str(csv_path))
    except Exception as exc:
        print(f"Failed to load CSV: {exc}")
        return 2

    try:
        pdf_chunks = extract_pdf_chunks(str(pdf_path))
    except Exception as exc:
        print(f"Failed to extract PDF: {exc}")
        return 3

    # Extract concepts
    ux_concepts = extract_concepts(feedbacks, source="ux")
    design_concepts = extract_concepts(pdf_chunks, source="design")

    all_concepts = ux_concepts + design_concepts
    texts = [c.text.strip() for c in all_concepts if c.text and c.text.strip()]

    # Deduplicate while preserving order
    seen = set()
    unique_texts: list[str] = []
    for t in texts:
        k = t.lower()
        if k in seen:
            continue
        seen.add(k)
        unique_texts.append(t)

    if not unique_texts:
        print("No concept texts found to embed.")
        return 4

    # Ensure embedder available
    if SentenceEmbedder is None:
        print("Embedding module not available. Ensure `app.models.embedding` can be imported.")
        print("Install transformers and torch, and ensure the model can be downloaded or is cached locally.")
        return 5

    embedder = SentenceEmbedder()
    batch_size = 64
    vectors: list[np.ndarray] = []

    print(f"Embedding {len(unique_texts)} unique concept texts in batches of {batch_size}...")
    for i, b in enumerate(batch(unique_texts, batch_size)):
        try:
            embs = embedder.encode(b)
        except Exception as exc:
            print(f"Failed to encode batch {i}: {exc}")
            return 6
        arr = embs.numpy() if hasattr(embs, "numpy") else np.asarray(embs)
        vectors.append(arr)

    embeddings = np.vstack(vectors)
    # Save outputs
    txt_out = out_dir / "concept_texts.json"
    emb_out = out_dir / "concept_embeddings.npy"
    mapping_out = out_dir / "concepts_mapping.json"

    txt_out.write_text(json.dumps(unique_texts, ensure_ascii=False, indent=2))
    np.save(str(emb_out), embeddings)

    # Save mapping: index -> source info (from all_concepts first occurrence)
    mapping = {}
    lower_to_info = {}
    for c in all_concepts:
        k = c.text.strip().lower()
        if k not in lower_to_info:
            lower_to_info[k] = {"category": c.category, "source": c.source}
    for idx, t in enumerate(unique_texts):
        k = t.lower()
        mapping[idx] = {"text": t, **(lower_to_info.get(k) or {})}

    mapping_out.write_text(json.dumps(mapping, ensure_ascii=False, indent=2))

    print(f"Wrote {len(unique_texts)} texts and embeddings to {out_dir}")

    # optional: build simple FAISS index if faiss available
    try:
        import faiss  # type: ignore

        d = embeddings.shape[1]
        index = faiss.IndexFlatIP(d) if faiss.get_num_gpus() == 0 else faiss.IndexFlatIP(d)
        # normalize for inner-product = cosine if vectors not normalized
        faiss.normalize_L2(embeddings)
        index.add(embeddings)
        faiss.write_index(index, str(out_dir / "concepts.faiss"))
        print("Built FAISS index and wrote to results/concepts.faiss")
    except Exception:
        print("FAISS not available or failed; skipping index build.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
