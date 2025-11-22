"""Simple image processing utilities (deterministic stub).

This module provides a minimal, offline-capable image embedding function.
It's intentionally lightweight: it returns a fixed-size deterministic vector
derived from image pixels so unit tests and the pipeline can treat images as
first-class inputs without heavy ML dependencies. Replace with a CLIP/ResNet
extractor in later experiments for improved accuracy.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PIL import Image
import numpy as np


def image_to_embedding(path: str, dim: int = 128) -> np.ndarray:
    """Load an image and return a deterministic embedding (L2-normalized).

    The embedding is computed by resizing to a small fixed size, converting to
    grayscale, flattening, and then projecting to `dim` with a simple seeded
    PRNG. This is NOT a semantic embedding but suffices for integration tests
    and early visualization.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)
    img = Image.open(p).convert("L").resize((32, 32))
    arr = np.asarray(img, dtype=np.float32).flatten()
    # deterministic projection using seeded random matrix based on filename
    seed = abs(hash(str(p))) % (2 ** 32)
    rng = np.random.RandomState(seed)
    proj = rng.randn(arr.shape[0], dim).astype(np.float32)
    vec = arr @ proj
    # normalize
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec
