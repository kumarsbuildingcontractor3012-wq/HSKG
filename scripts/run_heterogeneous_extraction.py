"""Simple runner: extract heterogeneous data (text + images) from real inputs.

This script demonstrates the HSKG-Twin heterogeneous pipeline:
 - Loads UX feedbacks from `Ux_data.csv`
 - Chunks and extracts concepts from `100_websites_compressed_11zon.pdf`
 - Extracts embedded images from the PDF
 - Saves summary and outputs to `results/` and `outputs/`

No heavy ML dependencies needed; focuses on data organization and extraction.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.ingest.heterogeneous_processor import (
    extract_heterogeneous_data,
    summarize_heterogeneous_extraction,
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    csv_path = str(root / "Ux_data.csv")
    pdf_path = str(root / "100_websites_compressed_11zon.pdf")

    results_dir = root / "results"
    outputs_dir = root / "outputs"
    results_dir.mkdir(exist_ok=True)
    outputs_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("HSKG-Twin: Heterogeneous Data Extraction")
    print("=" * 60)

    # Extract heterogeneous data
    print(f"\n[1] Extracting from {Path(csv_path).name} and {Path(pdf_path).name}...")
    try:
        items = extract_heterogeneous_data(
            csv_path,
            pdf_path,
            extract_images=True,
            image_output_dir=str(outputs_dir / "images"),
        )
    except Exception as exc:
        print(f"ERROR during extraction: {exc}")
        return 1

    # Summarize
    summary = summarize_heterogeneous_extraction(items)
    print(f"\n[2] Summary:")
    print(f"   Total items: {summary['total_items']}")
    print(f"   Text items: {summary['text_count']}")
    print(f"   Image items: {summary['image_count']}")
    print(f"\n   Breakdown:")
    print(f"   - UX (text): {summary['breakdown']['ux_text']}")
    print(f"   - Design (text): {summary['breakdown']['design_text']}")
    print(f"   - Design (images): {summary['breakdown']['design_images']}")

    # Save summary
    summary_out = results_dir / "heterogeneous_summary.json"
    summary_out.write_text(json.dumps(summary, indent=2))
    print(f"\n[3] Saved summary to: {summary_out}")

    # Save detailed items (for inspection)
    items_out = results_dir / "heterogeneous_items.json"
    items_list = [
        {
            "text": item.text,
            "modality": item.modality,
            "source": item.source,
            "category": item.category,
        }
        for item in items
    ]
    items_out.write_text(json.dumps(items_list, ensure_ascii=False, indent=2))
    print(f"    Saved items to: {items_out}")

    # List extracted images (if any)
    images_dir = outputs_dir / "images"
    if images_dir.exists():
        images = list(images_dir.glob("*.png"))
        if images:
            print(f"\n[4] Extracted {len(images)} images to: {images_dir}")

    print("\n" + "=" * 60)
    print("Heterogeneous extraction complete!")
    print(f"Outputs saved to {outputs_dir} and {results_dir}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
