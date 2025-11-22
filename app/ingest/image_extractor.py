"""Extract images from PDF documents.

Uses PyMuPDF to extract embedded images. This enables heterogeneous data
processing: text chunks + images from the same source, as required by the
HSKG-Twin pipeline for organizing heterogeneous design information.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import fitz  # PyMuPDF


def extract_images_from_pdf(path: str, output_dir: str | None = None) -> List[Tuple[str, bytes]]:
    """Extract all images from a PDF document.

    Args:
        path: Path to the PDF file.
        output_dir: Optional directory to save extracted images (in addition to returning bytes).

    Returns:
        A list of (filename, image_bytes) tuples. Each image is named based on
        page number and occurrence (e.g., "page_0_img_0.png").
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(p))
    images: list[Tuple[str, bytes]] = []

    for page_num, page in enumerate(doc):
        image_list = page.get_images(full=True)
        for img_idx, img_ref in enumerate(image_list):
            xref = img_ref[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                img_bytes = pix.tobytes("png")
                filename = f"page_{page_num}_img_{img_idx}.png"
                images.append((filename, img_bytes))
                if output_dir:
                    (out / filename).write_bytes(img_bytes)
            except Exception:
                # Skip images that fail to extract
                continue

    return images


def count_images_in_pdf(path: str) -> int:
    """Return total number of images in the PDF."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)
    doc = fitz.open(str(p))
    count = 0
    for page in doc:
        count += len(page.get_images(full=True))
    return count
