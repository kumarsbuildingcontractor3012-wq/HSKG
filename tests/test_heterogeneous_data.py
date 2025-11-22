"""Test heterogeneous data extraction from real PDF and CSV inputs."""

import pytest
from pathlib import Path

from app.ingest.heterogeneous_processor import extract_heterogeneous_data, summarize_heterogeneous_extraction


@pytest.mark.timeout(30)
def test_heterogeneous_extraction_text_only():
    """Extract text (no images) from the actual input files (fast path).
    
    NOTE: The system now includes EGFE-dataset for design concepts.
    Expected: 5000 UX items + ~18000-19000 design items from EGFE.
    """
    root = Path(__file__).resolve().parents[1]
    csv_path = str(root / "Ux_data.csv")
    pdf_path = str(root / "100_websites_compressed_11zon.pdf")

    # Extract TEXT ONLY (no images to avoid timeout on large PDF)
    items = extract_heterogeneous_data(csv_path, pdf_path, extract_images=False)
    assert len(items) > 0, "Should extract at least some items"

    # Check summary
    summary = summarize_heterogeneous_extraction(items)
    assert summary["total_items"] > 20000, "Should have 20K+ items (UX + EGFE design)"
    assert summary["text_count"] > 0
    assert summary["ux_count"] > 0, "Should have UX text from CSV"
    assert summary["design_count"] > 15000, "Should have design items from EGFE"
    
    # Both UX and design items should exist
    ux_items = [i for i in items if i.source == "ux"]
    design_items = [i for i in items if i.source == "design"]
    assert len(ux_items) > 0, "UX items from CSV should exist"
    assert len(design_items) > 0, "Design items from EGFE should exist"
    assert len(ux_items) == 5000, "UX items should be ~5000 from CSV"
    assert 15000 < len(design_items) < 20000, "Design items should be 15K-20K from EGFE"


@pytest.mark.timeout(30)
def test_heterogeneous_text_modality():
    """Verify text items have correct modality and source tags.
    
    NOTE: Items include both UX (CSV) and design (EGFE).
    """
    root = Path(__file__).resolve().parents[1]
    csv_path = str(root / "Ux_data.csv")
    pdf_path = str(root / "100_websites_compressed_11zon.pdf")

    items = extract_heterogeneous_data(csv_path, pdf_path, extract_images=False)
    text_items = [i for i in items if i.modality == "text"]
    assert all(i.modality == "text" for i in text_items)
    assert any(i.source == "ux" for i in text_items), "Should have UX text"

    assert any(i.source == "design" for i in text_items), "Should have design text from EGFE"

@pytest.mark.timeout(30)
def test_heterogeneous_item_structure():
    """Verify text items have proper structure and attributes."""
    root = Path(__file__).resolve().parents[1]
    csv_path = str(root / "Ux_data.csv")
    pdf_path = str(root / "100_websites_compressed_11zon.pdf")

    items = extract_heterogeneous_data(csv_path, pdf_path, extract_images=False)
    # Check that all items have required fields
    for item in items:
        assert item.text is not None
        assert item.modality in ["text", "image"]
        assert item.source in ["ux", "design"]
        # category can be None for design text or images
        # raw_data should be None for text items
        if item.modality == "text":
            assert item.raw_data is None, "Text items should not have raw_data"
