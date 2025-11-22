"""OCR and image-to-text processor for extracting design descriptions from PDF images.

This module converts visual design elements (screenshots, mockups, UI patterns)
into textual descriptions that can be processed as "design concepts" alongside
UX feedback. Implements heterogeneous modality bridge: image → text → concept.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import io

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False

try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

import fitz  # PyMuPDF


@dataclass
class OCRResult:
    """Represents OCR extraction from a single image."""
    image_id: str  # e.g., "page_5_img_2.png"
    page_num: int
    text: str  # extracted text
    confidence: float  # average confidence score
    source_type: str  # "design" (from PDF images)


def extract_images_with_ocr(
    pdf_path: str,
    use_tesseract: bool = False,
    confidence_threshold: float = 0.3,
) -> Tuple[List[OCRResult], dict]:
    """Extract images from PDF and apply OCR to generate text descriptions.

    Args:
        pdf_path: path to PDF file.
        use_tesseract: if True, use Tesseract; else use EasyOCR.
        confidence_threshold: minimum confidence to include OCR text.

    Returns:
        (list of OCRResult, summary dict with extraction stats)
    """
    results: List[OCRResult] = []
    summary = {
        "total_images": 0,
        "successful_ocr": 0,
        "failed_ocr": 0,
        "avg_confidence": 0.0,
        "backend": "tesseract" if use_tesseract else "easyocr",
    }

    if not Path(pdf_path).is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Initialize OCR engine
    if use_tesseract and HAS_TESSERACT:
        ocr_fn = _ocr_with_tesseract
    elif HAS_EASYOCR:
        ocr_fn = _ocr_with_easyocr
    else:
        raise RuntimeError(
            "No OCR backend available. Install easyocr or pytesseract+tesseract."
        )

    # Extract images from PDF
    doc = fitz.open(pdf_path)
    confidences = []

    for page_num, page in enumerate(doc):
        image_list = page.get_images()
        summary["total_images"] += len(image_list)

        for img_index, img_ref in enumerate(image_list):
            try:
                # Extract image bytes
                xref = img_ref[0]
                pix = fitz.Pixmap(doc, xref)
                img_bytes = pix.tobytes("png") if pix.n < 5 else pix.tobytes("ppm")

                # Run OCR
                text, conf = ocr_fn(img_bytes, page_num, img_index)

                if conf >= confidence_threshold and text.strip():
                    image_id = f"page_{page_num}_img_{img_index}"
                    result = OCRResult(
                        image_id=image_id,
                        page_num=page_num,
                        text=text,
                        confidence=conf,
                        source_type="design",
                    )
                    results.append(result)
                    confidences.append(conf)
                    summary["successful_ocr"] += 1
                else:
                    summary["failed_ocr"] += 1

            except Exception as e:
                print(f"Warning: OCR failed on page {page_num} image {img_index}: {e}")
                summary["failed_ocr"] += 1

    summary["avg_confidence"] = sum(confidences) / len(confidences) if confidences else 0.0
    return results, summary


def _ocr_with_easyocr(
    img_bytes: bytes,
    page_num: int,
    img_index: int,
) -> Tuple[str, float]:
    """Apply EasyOCR to image bytes. Returns (text, avg_confidence)."""
    if not HAS_EASYOCR:
        raise RuntimeError("EasyOCR not installed. Install with: pip install easyocr")

    # Load image from bytes
    img_array = io.BytesIO(img_bytes)
    from PIL import Image
    img = Image.open(img_array)

    # Initialize reader (cached on first call)
    if not hasattr(_ocr_with_easyocr, "_reader"):
        _ocr_with_easyocr._reader = easyocr.Reader(["en"], gpu=False)

    reader = _ocr_with_easyocr._reader
    results = reader.readtext(img, detail=1)  # detail=1 returns confidence

    if not results:
        return "", 0.0

    texts = [r[1] for r in results]
    confidences = [r[2] for r in results]
    combined_text = " ".join(texts)
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    return combined_text, avg_conf


def _ocr_with_tesseract(
    img_bytes: bytes,
    page_num: int,
    img_index: int,
) -> Tuple[str, float]:
    """Apply Tesseract OCR to image bytes. Returns (text, confidence)."""
    if not HAS_TESSERACT:
        raise RuntimeError(
            "Tesseract not installed. Install with: sudo apt-get install tesseract-ocr && pip install pytesseract"
        )

    from PIL import Image
    img = Image.open(io.BytesIO(img_bytes))

    # Tesseract doesn't return per-word confidence easily; use average
    text = pytesseract.image_to_string(img)
    # Approximate confidence: assume 0.8 if text extracted, else 0
    confidence = 0.8 if text.strip() else 0.0

    return text, confidence


def summarize_ocr_extraction(results: List[OCRResult]) -> dict:
    """Summarize OCR extraction results."""
    return {
        "total_ocr_items": len(results),
        "avg_confidence": sum(r.confidence for r in results) / len(results)
        if results
        else 0.0,
        "text_coverage": f"{len([r for r in results if r.text.strip()])} items with text",
        "pages_represented": len(set(r.page_num for r in results)),
    }
