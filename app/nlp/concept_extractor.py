"""Concept extraction and categorization using spaCy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

# Try to import spaCy; if not available, fall back to a lightweight extractor
try:
    import spacy  # type: ignore

    HAS_SPACY = True
except Exception:
    spacy = None  # type: ignore
    HAS_SPACY = False

# Categories from research paper (kept deliberately small and interpretable)
UX_CATEGORIES = {"product", "setting", "state", "user"}
DESIGN_CATEGORIES = {"goal", "fix", "item"}

if HAS_SPACY:
    try:
        NLP = spacy.load("en_core_web_sm")
    except OSError:  # pragma: no cover - model will be downloaded at runtime if missing
        from spacy.cli import download  # type: ignore

        download("en_core_web_sm")
        NLP = spacy.load("en_core_web_sm")
else:
    NLP = None


@dataclass
class Concept:
    text: str
    category: Optional[str]
    start_char: int
    end_char: int
    source: Optional[str] = None


def _assign_category(token_text: str) -> Optional[str]:
    """Assign category by fuzzy/substring match to known category keywords.

    This improves over exact-match entity texts by matching tokens or
    substrings (e.g., 'user experience' -> 'user'). Keep the rule simple and
    deterministic for reproducibility.
    """
    lower = token_text.lower()
    # direct membership
    if lower in UX_CATEGORIES:
        return lower
    if lower in DESIGN_CATEGORIES:
        return lower

    # substring / token match
    for cat in UX_CATEGORIES:
        if cat in lower.split():
            return cat
    for cat in DESIGN_CATEGORIES:
        if cat in lower.split():
            return cat

    # fallback: any keyword present as substring
    for cat in UX_CATEGORIES | DESIGN_CATEGORIES:
        if cat in lower:
            return cat

    return None


def _collect_spans(doc) -> List[tuple]:
    """Collect entity spans and noun-chunk spans, return (start, end, text).

    Supports either a spaCy `Doc` (when spaCy present) or a raw string (fallback).
    """
    spans: list[tuple[int, int, str]] = []
    if HAS_SPACY and hasattr(doc, "ents"):
        for ent in doc.ents:
            spans.append((ent.start_char, ent.end_char, ent.text))
        # include noun chunks as lightweight concepts
        for chunk in doc.noun_chunks:
            spans.append((chunk.start_char, chunk.end_char, chunk.text))
    else:
        # Fallback: simple sentence/token-based spans (no character-accurate positions)
        txt = doc if isinstance(doc, str) else str(doc)
        for sent in txt.split("."):
            s = sent.strip()
            if not s:
                continue
            # take entire sentence as one span for simplicity
            spans.append((0, len(s), s))

    # remove duplicates, prefer earlier/larger spans
    seen = set()
    uniq: list[tuple[int, int, str]] = []
    for s, e, t in sorted(spans, key=lambda x: (x[0], -(x[1] - x[0]))):
        key = (s, e, t)
        if key in seen:
            continue
        seen.add(key)
        uniq.append((s, e, t))
    return uniq


def _merge_overlapping(spans: List[tuple]) -> List[tuple]:
    """Merge overlapping spans preferring longer spans."""
    if not spans:
        return []
    merged: list[tuple[int, int, str]] = []
    current = list(spans[0])
    for s, e, t in spans[1:]:
        if s <= current[1]:
            # overlap — extend end to the max and prefer longer text
            if e > current[1]:
                current[1] = e
                current[2] = (
                    current[2] if len(current[2]) >= len(t) else t
                )
        else:
            merged.append((current[0], current[1], current[2]))
            current = [s, e, t]
    merged.append((current[0], current[1], current[2]))
    return merged


def extract_concepts(texts: List[str], source: Optional[str] = None, max_per_doc: int = 50) -> List[Concept]:
    """Extract concept candidates from a list of texts.

    - Uses spaCy entities and noun-chunks.
    - Merges overlapping spans and assigns a simple category via
      substring/token matching.
    - Returns deterministic ordering (document order then span start).
    """
    concepts: list[Concept] = []
    for doc_text in texts:
        if HAS_SPACY and NLP is not None:
            doc = NLP(doc_text)
        else:
            doc = doc_text  # fallback: pass raw text to _collect_spans
        spans = _collect_spans(doc)
        spans = _merge_overlapping(spans)
        # limit per document for stability
        for start_char, end_char, text in spans[:max_per_doc]:
            cat = _assign_category(text)
            concepts.append(
                Concept(
                    text=text,
                    category=cat,
                    start_char=start_char,
                    end_char=end_char,
                    source=source,
                )
            )
    return concepts
