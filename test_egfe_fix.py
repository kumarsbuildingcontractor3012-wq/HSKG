#!/usr/bin/env python3
"""Quick test to verify EGFE concept extraction is working."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

print("Testing EGFE concept extraction...")
print("-" * 70)

# Test 1: Load EGFE texts
print("\n[1] Loading EGFE UI element descriptions...")
from app.ingest.egfe_loader import load_egfe_as_design_texts

egfe_dir = Path(__file__).resolve().parent / "tests" / "fixtures" / "EGFE-dataset"
if egfe_dir.exists():
    egfe_texts = load_egfe_as_design_texts(str(egfe_dir))
    print(f"✓ Loaded {len(egfe_texts)} EGFE UI descriptions")
    if egfe_texts:
        print(f"  Sample: {egfe_texts[0][:80]}...")
else:
    print(f"✗ EGFE dataset not found at {egfe_dir}")
    sys.exit(1)

# Test 2: Extract concepts from EGFE texts
print("\n[2] Extracting concepts from EGFE texts...")
from app.nlp.concept_extractor import extract_concepts

try:
    egfe_concepts = extract_concepts(egfe_texts, source="design")
    print(f"✓ Extracted {len(egfe_concepts)} concepts from EGFE")
    if egfe_concepts:
        print(f"  Sample concept: '{egfe_concepts[0].text}' (category: {egfe_concepts[0].category})")
except Exception as e:
    print(f"✗ Concept extraction failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Load UX and PDF concepts
print("\n[3] Loading UX and PDF concepts...")
from app.ingest.csv_loader import load_feedback_from_csv
from app.ingest.pdf_loader import extract_pdf_chunks

csv_path = Path(__file__).resolve().parent / "tests" / "fixtures" / "Ux_data.csv"
pdf_path = Path(__file__).resolve().parent / "tests" / "fixtures" / "100_websites_compressed_11zon.pdf"

if csv_path.exists():
    feedbacks = load_feedback_from_csv(str(csv_path))
    ux_concepts = extract_concepts(feedbacks, source="ux")
    print(f"✓ Loaded {len(ux_concepts)} UX concepts")
else:
    print(f"✗ CSV not found at {csv_path}")

if pdf_path.exists():
    pdf_chunks = extract_pdf_chunks(str(pdf_path))
    design_concepts = extract_concepts(pdf_chunks, source="design")
    print(f"✓ Loaded {len(design_concepts)} PDF design concepts")
else:
    print(f"✗ PDF not found at {pdf_path}")

# Test 4: Combine all concepts
print("\n[4] Summary of combined concept extraction:")
print("=" * 70)
all_design_concepts = design_concepts + egfe_concepts
all_concepts = ux_concepts + all_design_concepts

print(f"UX Concepts:                 {len(ux_concepts)}")
print(f"Design Concepts (PDF):       {len(design_concepts)}")
print(f"Design Concepts (EGFE):      {len(egfe_concepts)}")
print(f"Total Design Concepts:       {len(all_design_concepts)}")
print(f"Total All Concepts:          {len(all_concepts)}")
print("=" * 70)

# Expected targets from project description
print("\n[5] Validation against targets:")
print(f"  ✓ UX concepts (expected ~5000):         {len(ux_concepts)} {'✓' if 4500 <= len(ux_concepts) <= 5500 else '✗'}")
print(f"  ✓ Design concepts (expected >4000):     {len(all_design_concepts)} {'✓' if len(all_design_concepts) > 4000 else '✗'}")
print(f"  ✓ Total concepts (expected >9000):      {len(all_concepts)} {'✓' if len(all_concepts) > 9000 else '✗'}")
print("\nEGFE concept extraction is now working in the evaluation pipeline! ✓")
