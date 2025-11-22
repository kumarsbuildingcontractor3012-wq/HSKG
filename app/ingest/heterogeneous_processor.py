"""Heterogeneous data processor: unified extraction of text + images.

This module orchestrates extraction of both text (PDF chunks, CSV feedbacks)
and images (extracted from PDF) into a single concept graph. It implements
the paper's requirement to "organize heterogeneous structures" from multiple
sources into a unified knowledge system.

The output is a list of "items" (concept candidates), each tagged with
source type (text or image) and metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import io
from pathlib import Path

import numpy as np

from app.ingest.csv_loader import load_feedback_from_csv
from app.ingest.pdf_loader import extract_pdf_chunks
from app.ingest.image_extractor import extract_images_from_pdf
from app.ingest.egfe_loader import load_egfe_as_design_texts
from app.nlp.concept_extractor import extract_concepts


@dataclass
class HeterogeneousItem:
    """Represents a concept candidate from any modality (text or image)."""
    text: str  # description or image filename
    modality: str  # "text" or "image"
    source: str  # "ux", "design"
    category: Optional[str] = None
    embedding: Optional[np.ndarray] = None
    raw_data: Optional[bytes] = None  # for images: raw PNG bytes


def extract_heterogeneous_data(
    csv_path: str,
    pdf_path: str,
    extract_images: bool = True,
    image_output_dir: Optional[str] = None,
) -> List[HeterogeneousItem]:
    """
    Unified extraction from UX_data.csv and 100_websites_compressed_11zon.pdf.

    Returns:
        A list of HeterogeneousItem objects (text concepts + image references).
    """
    items: List[HeterogeneousItem] = []

    # Resolve paths with sensible fallbacks so tests can run from different CWDs
    csv_p = Path(csv_path).resolve()
    pdf_p = Path(pdf_path).resolve()
    
    # If paths don't exist, try fixtures/ subdirectory
    if not csv_p.is_file():
        fixture_csv = csv_p.parent / "tests" / "fixtures" / csv_p.name
        if fixture_csv.is_file():
            csv_p = fixture_csv
        else:
            # Try from current working directory + fixtures
            cwd = Path.cwd()
            fixture_csv = cwd / "tests" / "fixtures" / csv_p.name
            if fixture_csv.is_file():
                csv_p = fixture_csv
    
    if not pdf_p.is_file():
        fixture_pdf = pdf_p.parent / "tests" / "fixtures" / pdf_p.name
        if fixture_pdf.is_file():
            pdf_p = fixture_pdf
        else:
            # Try from current working directory + fixtures
            cwd = Path.cwd()
            fixture_pdf = cwd / "tests" / "fixtures" / pdf_p.name
            if fixture_pdf.is_file():
                pdf_p = fixture_pdf

    # 1. Extract UX feedback texts (modality=text, source=ux)
    feedbacks = load_feedback_from_csv(str(csv_p))
    ux_concepts = extract_concepts(feedbacks, source="ux")
    for c in ux_concepts:
        items.append(
            HeterogeneousItem(
                text=c.text,
                modality="text",
                source="ux",
                category=c.category,
            )
        )

    # 2. Extract design texts from PDF (modality=text, source=design)
    pdf_chunks = extract_pdf_chunks(str(pdf_p))
    design_concepts = extract_concepts(pdf_chunks, source="design")
    for c in design_concepts:
        items.append(
            HeterogeneousItem(
                text=c.text,
                modality="text",
                source="design",
                category=c.category,
            )
        )

    # 2b. Extract design texts from EGFE-dataset (UI element metadata)
    try:
        egfe_dir = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "EGFE-dataset"
        if egfe_dir.exists():
            egfe_texts = load_egfe_as_design_texts(str(egfe_dir))
            egfe_concepts = extract_concepts(egfe_texts, source="design")
            for c in egfe_concepts:
                items.append(
                    HeterogeneousItem(
                        text=c.text,
                        modality="text",
                        source="design",
                        category=c.category,
                    )
                )
    except Exception as e:
        print(f"Note: EGFE-dataset extraction skipped ({e})")


    # 3. Extract images from PDF (modality=image, source=design)
    if extract_images:
        try:
            images = extract_images_from_pdf(str(pdf_p), output_dir=image_output_dir)
            for filename, img_bytes in images:
                items.append(
                    HeterogeneousItem(
                        text=filename,  # use filename as description
                        modality="image",
                        source="design",
                        category=None,  # no category for images yet
                        raw_data=img_bytes,
                    )
                )
        except Exception as e:
            print(f"Warning: image extraction failed ({e}); continuing with text only")

    return items


def summarize_heterogeneous_extraction(items: List[HeterogeneousItem]) -> dict:
    """Return summary statistics of the extraction."""
    text_items = [i for i in items if i.modality == "text"]
    image_items = [i for i in items if i.modality == "image"]
    ux_items = [i for i in items if i.source == "ux"]
    design_items = [i for i in items if i.source == "design"]

    return {
        "total_items": len(items),
        "text_count": len(text_items),
        "image_count": len(image_items),
        "ux_count": len(ux_items),
        "design_count": len(design_items),
        "breakdown": {
            "ux_text": len([i for i in ux_items if i.modality == "text"]),
            "ux_images": len([i for i in ux_items if i.modality == "image"]),
            "design_text": len([i for i in design_items if i.modality == "text"]),
            "design_images": len([i for i in design_items if i.modality == "image"]),
        },
    }
