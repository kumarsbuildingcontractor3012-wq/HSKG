"""Test image extraction and processing from real PDF input."""

import numpy as np
from pathlib import Path

from app.ingest.image_extractor import extract_images_from_pdf, count_images_in_pdf


def test_extract_images_from_real_pdf():
    """Extract images from the actual 100_websites_compressed_11zon.pdf."""
    root = Path(__file__).resolve().parents[1]
    pdf_path = root / "100_websites_compressed_11zon.pdf"
    
    # Try fixtures if not in root
    if not pdf_path.is_file():
        pdf_path = root / "tests" / "fixtures" / "100_websites_compressed_11zon.pdf"
    
    assert pdf_path.exists(), f"PDF not found at {pdf_path}"
    
    # Count images
    count = count_images_in_pdf(str(pdf_path))
    assert isinstance(count, int) and count >= 0, "Image count should be non-negative"
    
    # Extract images
    images = extract_images_from_pdf(str(pdf_path))
    assert isinstance(images, list)
    # PDF may have 0 or more images; we just verify the extraction succeeds
    for filename, img_bytes in images:
        assert isinstance(filename, str)
        assert isinstance(img_bytes, bytes)
        assert len(img_bytes) > 0, "Image bytes should not be empty"


def test_image_extraction_with_save():
    """Extract images and verify they can be saved to disk."""
    root = Path(__file__).resolve().parents[1]
    pdf_path = root / "100_websites_compressed_11zon.pdf"
    
    # Try fixtures if not in root
    if not pdf_path.is_file():
        pdf_path = root / "tests" / "fixtures" / "100_websites_compressed_11zon.pdf"
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        images = extract_images_from_pdf(str(pdf_path), output_dir=tmpdir)
        # Verify saved files exist
        for filename, _ in images:
            saved_path = Path(tmpdir) / filename
            assert saved_path.exists(), f"Saved image {filename} should exist"
            assert saved_path.stat().st_size > 0, "Saved image should have content"
