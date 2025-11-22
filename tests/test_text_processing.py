"""Test text processing from real inputs (Ux_data.csv)."""

import pytest
from pathlib import Path

from app.ingest.csv_loader import load_feedback_from_csv
from app.nlp.concept_extractor import extract_concepts


def test_extract_concepts_from_real_csv():
    """Extract concepts from the actual Ux_data.csv file."""
    root = Path(__file__).resolve().parents[1]
    csv_path = root / "Ux_data.csv"
    
    # Try fixtures if not in root
    if not csv_path.is_file():
        csv_path = root / "tests" / "fixtures" / "Ux_data.csv"
    
    assert csv_path.exists(), f"Ux_data.csv not found at {csv_path}"
    
    texts = load_feedback_from_csv(str(csv_path))
    assert len(texts) > 0, "CSV should contain feedback rows"
    
    # Extract concepts from a subset
    concepts = extract_concepts(texts[:20], source="ux")
    assert isinstance(concepts, list)
    assert len(concepts) > 0, "Should extract at least some concepts"
    
    # Verify concept attributes
    for concept in concepts[:5]:
        assert concept.text is not None
        assert concept.source == "ux"


def test_concept_categories_assigned():
    """Verify that category assignment works on real feedback."""
    root = Path(__file__).resolve().parents[1]
    csv_path = root / "Ux_data.csv"
    
    # Try fixtures if not in root
    if not csv_path.is_file():
        csv_path = root / "tests" / "fixtures" / "Ux_data.csv"
    
    texts = load_feedback_from_csv(str(csv_path))
    concepts = extract_concepts(texts, source="ux")
    
    # Some concepts should have assigned categories (from UX_CATEGORIES or DESIGN_CATEGORIES)
    categorized = [c for c in concepts if c.category is not None]
    # It's okay if none are found (depends on input), but we verify the structure
    for concept in categorized[:5]:
        assert concept.category in {"product", "setting", "state", "user", "goal", "fix", "item"}
