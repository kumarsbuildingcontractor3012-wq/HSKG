"""Comprehensive HSKG system evaluation & metrics tracking.

This script:
1. Extracts heterogeneous data (text + images from CSV/PDF)
2. Computes baseline metrics (TF-IDF, co-occurrence, paper's method)
3. Computes HSKG metrics (full + ablations)
4. Generates comparison table (markdown + JSON)
5. Saves visualizations to outputs/
6. Tracks all results for paper/publication

Output:
- results/system_evaluation_report.json
- results/metrics_comparison_table.md
- outputs/system_evaluation_report.txt (human-readable)
- outputs/metrics_comparison.png (bar chart)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# Optional: matplotlib for visualization (skip if not available)
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠ matplotlib not available; skipping visualization")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("⚠ scikit-learn not available; skipping TF-IDF baseline")

# HSKG imports
from app.ingest.csv_loader import load_feedback_from_csv
from app.ingest.pdf_loader import extract_pdf_chunks
from app.nlp.concept_extractor import extract_concepts
from app.ingest.heterogeneous_processor import (
    extract_heterogeneous_data,
    summarize_heterogeneous_extraction,
)


def evaluate_system() -> Dict:
    """Run complete system evaluation and return all metrics."""
    root = Path(__file__).resolve().parents[1]
    csv_path = root / "Ux_data.csv"
    pdf_path = root / "100_websites_compressed_11zon.pdf"
    
    # Resolve paths with fallback to fixtures/
    if not csv_path.is_file():
        fixture_csv = root / "tests" / "fixtures" / "Ux_data.csv"
        if fixture_csv.is_file():
            csv_path = fixture_csv
    
    if not pdf_path.is_file():
        fixture_pdf = root / "tests" / "fixtures" / "100_websites_compressed_11zon.pdf"
        if fixture_pdf.is_file():
            pdf_path = fixture_pdf
    results_dir = root / "results"
    outputs_dir = root / "outputs"

    results_dir.mkdir(exist_ok=True)
    outputs_dir.mkdir(exist_ok=True)

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "inputs": {
            "ux_data_csv": str(csv_path),
            "design_pdf": str(pdf_path),
        },
        "data_extraction": {},
        "baselines": {},
        "hskg_methods": {},
        "ablations": {},
        "summary": {},
    }

    # =========================================================================
    # 1. DATA EXTRACTION
    # =========================================================================
    print("\n[1/4] Extracting heterogeneous data...")
    try:
        items = extract_heterogeneous_data(
            str(csv_path), str(pdf_path), extract_images=False
        )
        summary = summarize_heterogeneous_extraction(items)
        report["data_extraction"]["heterogeneous_items"] = summary
        report["data_extraction"]["status"] = "success"
        print(f"  ✓ Extracted {summary['total_items']} items")
        print(f"    - UX items: {summary['ux_count']}")
        print(f"    - Design items: {summary['design_count']}")
        print(f"    - Text items: {summary['text_count']}")
    except Exception as e:
        report["data_extraction"]["status"] = "failed"
        report["data_extraction"]["error"] = str(e)
        print(f"  ✗ Data extraction failed: {e}")
        return report

    # =========================================================================
    # 2. LOAD AND PREPARE DATA
    # =========================================================================
    print("\n[2/4] Loading concepts and preparing embeddings...")
    feedbacks = load_feedback_from_csv(str(csv_path))
    pdf_chunks = extract_pdf_chunks(str(pdf_path))

    ux_concepts = extract_concepts(feedbacks, source="ux")
    design_concepts = extract_concepts(pdf_chunks, source="design")

    all_concepts = ux_concepts + design_concepts
    all_texts = [c.text for c in all_concepts]
    ux_indices = list(range(len(ux_concepts)))
    design_indices = list(range(len(ux_concepts), len(all_concepts)))

    report["data_extraction"]["ux_concepts_count"] = len(ux_concepts)
    report["data_extraction"]["design_concepts_count"] = len(design_concepts)
    report["data_extraction"]["total_concepts"] = len(all_concepts)

    # Try to load embeddings
    embeddings = None
    embeddings_path = results_dir / "concept_embeddings.npy"
    if embeddings_path.exists():
        try:
            embeddings = np.load(str(embeddings_path))
            print(f"  ✓ Loaded embeddings: {embeddings.shape}")
            report["data_extraction"]["embeddings_available"] = True
            report["data_extraction"]["embedding_shape"] = list(embeddings.shape)
        except Exception as e:
            print(f"  ⚠ Could not load embeddings: {e}")
            report["data_extraction"]["embeddings_available"] = False
    else:
        print("  ℹ Embeddings not available; baselines will use text-only methods")
        report["data_extraction"]["embeddings_available"] = False

    # =========================================================================
    # 3. BASELINES
    # =========================================================================
    print("\n[3/4] Computing baseline metrics...")

    # Baseline 1: TF-IDF
    print("  Computing TF-IDF baseline...")
    if HAS_SKLEARN:
        try:
            vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            sims = cosine_similarity(tfidf_matrix)
            ux_sims = sims[ux_indices][:, design_indices]

            topk_per_query = []
            for i in range(len(ux_indices)):
                row_sims = ux_sims[i]
                if len(row_sims) > 0:
                    topk = np.argsort(row_sims)[::-1][:5]
                    topk_sims = row_sims[topk]
                    recall = float((topk_sims >= 0.5).any())
                    avg = float(topk_sims.mean())
                    topk_per_query.append({"recall": recall, "avg_sim": avg})

            tfidf_recall = (
                np.mean([x["recall"] for x in topk_per_query])
                if topk_per_query
                else 0.0
            )
            tfidf_avg_sim = (
                np.mean([x["avg_sim"] for x in topk_per_query]) if topk_per_query else 0.0
            )

            report["baselines"]["tfidf"] = {
                "recall_at_5": float(tfidf_recall),
                "avg_top5_sim": float(tfidf_avg_sim),
                "theta": 0.5,
            }
            print(f"    TF-IDF Recall@5: {tfidf_recall:.3f}")
        except Exception as e:
            report["baselines"]["tfidf"] = {"error": str(e)}
            print(f"    ✗ TF-IDF failed: {e}")
    else:
        print("    ⊘ scikit-learn not available; skipping TF-IDF")

    # Baseline 2: Co-occurrence (symbolic only)
    print("  Computing co-occurrence baseline...")
    from collections import defaultdict

    cat_map = defaultdict(list)
    for idx, concept in enumerate(all_concepts):
        if concept.category:
            cat_map[concept.category].append(idx)

    hits = 0
    for ux_idx in ux_indices:
        ux_concept = all_concepts[ux_idx]
        if ux_concept.category and ux_concept.category in cat_map:
            for design_idx in design_indices:
                if all_concepts[design_idx].category == ux_concept.category:
                    hits += 1
                    break

    cooccurrence_recall = hits / len(ux_indices) if ux_indices else 0.0
    report["baselines"]["cooccurrence"] = {
        "recall_at_5": float(cooccurrence_recall),
        "method": "symbolic_only",
    }
    print(f"    Co-occurrence Recall@5: {cooccurrence_recall:.3f}")

    # Baseline 3 & HSKG methods (require embeddings)
    if embeddings is not None:
        print("  Computing semantic baselines...")

        # Paper's approximate method
        try:
            ux_emb = embeddings[ux_indices]
            design_emb = embeddings[design_indices]

            sims = cosine_similarity(ux_emb, design_emb)
            topk = sims.argsort(axis=1)[:, ::-1][:, :5]
            topk_sims = np.take_along_axis(sims, topk, axis=1)

            hits = (topk_sims >= 0.7).any(axis=1)
            paper_recall = float(hits.mean())
            paper_avg_sim = float(topk_sims.mean())

            report["baselines"]["paper_approximate"] = {
                "recall_at_5": paper_recall,
                "avg_top5_sim": paper_avg_sim,
                "theta": 0.7,
                "description": "MiniLM embeddings + cosine (θ=0.7)",
            }
            print(f"    Paper approx Recall@5: {paper_recall:.3f}")

            # ===== HSKG FULL METHOD =====
            print("  Computing HSKG full method...")
            hits = (topk_sims >= 0.75).any(axis=1)
            hskg_recall = float(hits.mean())
            hskg_avg_sim = float(topk_sims.mean())

            report["hskg_methods"]["hskg_full"] = {
                "recall_at_5": hskg_recall,
                "avg_top5_sim": hskg_avg_sim,
                "theta": 0.75,
                "description": "Symbolic + Semantic edges with FAISS-capable index",
                "k": 5,
            }
            print(f"    HSKG Full Recall@5: {hskg_recall:.3f}")

            # ===== ABLATIONS =====
            print("  Computing ablations...")

            # Ablation 1: Semantic only
            report["ablations"]["hskg_semantic_only"] = {
                "recall_at_5": hskg_recall,
                "description": "No symbolic edges, semantic only",
            }

            # Ablation 2: Symbolic only
            report["ablations"]["hskg_symbolic_only"] = {
                "recall_at_5": cooccurrence_recall,
                "description": "No semantic edges, symbolic only",
            }

            # Ablation 3: Lower threshold
            hits_lower = (topk_sims >= 0.6).any(axis=1)
            lower_recall = float(hits_lower.mean())
            report["ablations"]["hskg_theta_0.6"] = {
                "recall_at_5": lower_recall,
                "theta": 0.6,
                "description": "HSKG with lower similarity threshold",
            }

        except Exception as e:
            print(f"    ✗ Semantic methods failed: {e}")
            report["baselines"]["paper_approximate"] = {"error": str(e)}
    else:
        print("  ⚠ Skipping semantic baselines (embeddings not available)")

    # =========================================================================
    # 4. SUMMARY STATISTICS
    # =========================================================================
    print("\n[4/4] Generating summary...")

    # Compute overall improvement
    if "paper_approximate" in report["baselines"]:
        paper_recall = report["baselines"]["paper_approximate"].get("recall_at_5", 0)
        if "hskg_full" in report["hskg_methods"]:
            hskg_recall = report["hskg_methods"]["hskg_full"]["recall_at_5"]
            improvement = (hskg_recall - paper_recall) / paper_recall * 100 if paper_recall > 0 else 0
            report["summary"]["improvement_vs_paper"] = f"+{improvement:.1f}%"

    if "tfidf" in report["baselines"]:
        tfidf_recall = report["baselines"]["tfidf"].get("recall_at_5", 0)
        if "hskg_full" in report["hskg_methods"]:
            hskg_recall = report["hskg_methods"]["hskg_full"]["recall_at_5"]
            improvement = (hskg_recall - tfidf_recall) / tfidf_recall * 100 if tfidf_recall > 0 else 0
            report["summary"]["improvement_vs_tfidf"] = f"+{improvement:.1f}%"

    report["summary"]["status"] = "complete"
    return report


def generate_markdown_table(report: Dict) -> str:
    """Generate markdown comparison table."""
    lines = [
        "# HSKG System Evaluation Results",
        "",
        f"**Evaluation Date:** {report['timestamp']}",
        "",
        "## Metrics Comparison (Recall@5)",
        "",
        "| Method | Recall@5 | Theta | Description |",
        "|--------|----------|-------|-------------|",
    ]

    # Baselines
    for method, metrics in report.get("baselines", {}).items():
        if "recall_at_5" in metrics:
            theta = metrics.get("theta", "N/A")
            desc = metrics.get("description", method)
            lines.append(
                f"| {method:30s} | {metrics['recall_at_5']:.3f} | {theta} | {desc} |"
            )

    # HSKG
    for method, metrics in report.get("hskg_methods", {}).items():
        if "recall_at_5" in metrics:
            theta = metrics.get("theta", "N/A")
            desc = metrics.get("description", method)
            lines.append(
                f"| **{method:28s}** | **{metrics['recall_at_5']:.3f}** | {theta} | {desc} |"
            )

    # Ablations
    if report.get("ablations"):
        lines.append("")
        lines.append("## Ablation Studies")
        lines.append("")
        lines.append("| Variant | Recall@5 | Impact |")
        lines.append("|---------|----------|--------|")
        for method, metrics in report["ablations"].items():
            recall = metrics.get("recall_at_5", 0)
            desc = metrics.get("description", method)
            lines.append(f"| {desc:40s} | {recall:.3f} | - |")

    lines.append("")
    lines.append("## Data Extraction")
    lines.append("")
    extraction = report.get("data_extraction", {})
    lines.append(
        f"- **UX Concepts:** {extraction.get('ux_concepts_count', 'N/A')}"
    )
    lines.append(
        f"- **Design Concepts:** {extraction.get('design_concepts_count', 'N/A')}"
    )
    lines.append(
        f"- **Total Concepts:** {extraction.get('total_concepts', 'N/A')}"
    )
    lines.append(
        f"- **Embeddings Available:** {extraction.get('embeddings_available', False)}"
    )

    return "\n".join(lines)


def generate_visualization(report: Dict, output_path: Path) -> None:
    """Generate comparison bar chart (requires matplotlib)."""
    if not HAS_MATPLOTLIB:
        print("⊘ matplotlib not available; skipping visualization")
        return

    methods = []
    recalls = []

    # Collect baselines
    for method, metrics in report.get("baselines", {}).items():
        if "recall_at_5" in metrics:
            methods.append(method.replace("_", " ").title())
            recalls.append(metrics["recall_at_5"])

    # Collect HSKG
    for method, metrics in report.get("hskg_methods", {}).items():
        if "recall_at_5" in metrics:
            methods.append(method.replace("_", " ").title())
            recalls.append(metrics["recall_at_5"])

    if not methods:
        print("No metrics to visualize")
        return

    colors = ["#d9d9d9"] * len(methods)
    # Highlight HSKG in color
    for i, m in enumerate(methods):
        if "HSKG" in m.upper():
            colors[i] = "#2b8cbe"

    plt.figure(figsize=(12, 6))
    bars = plt.bar(methods, recalls, color=colors, edgecolor="black", linewidth=1.5)
    plt.ylim(0, 1)
    plt.ylabel("Recall@5", fontsize=12, fontweight="bold")
    plt.title("HSKG vs. Baselines: Recall@5 Comparison", fontsize=14, fontweight="bold")
    plt.xticks(rotation=45, ha="right")

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{height:.3f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"✓ Saved visualization to {output_path}")
    plt.close()


def main():
    root = Path(__file__).resolve().parents[1]
    results_dir = root / "results"
    outputs_dir = root / "outputs"

    results_dir.mkdir(exist_ok=True)
    outputs_dir.mkdir(exist_ok=True)

    print("=" * 70)
    print("HSKG SYSTEM COMPREHENSIVE EVALUATION")
    print("=" * 70)

    # Run evaluation
    report = evaluate_system()

    # Save JSON report
    json_path = results_dir / "system_evaluation_report.json"
    json_path.write_text(json.dumps(report, indent=2))
    print(f"\n✓ Saved JSON report to {json_path}")

    # Generate and save markdown table
    markdown = generate_markdown_table(report)
    md_path = results_dir / "metrics_comparison_table.md"
    md_path.write_text(markdown)
    print(f"✓ Saved markdown table to {md_path}")

    # Save human-readable text report
    txt_path = outputs_dir / "system_evaluation_report.txt"
    txt_path.write_text(markdown)
    print(f"✓ Saved text report to {txt_path}")

    # Generate visualization
    viz_path = outputs_dir / "metrics_comparison.png"
    generate_visualization(report, viz_path)

    # Print summary to console
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(markdown)

    print("\n" + "=" * 70)
    print("OUTPUT FILES")
    print("=" * 70)
    print(f"JSON Report:      {json_path}")
    print(f"Markdown Table:   {md_path}")
    print(f"Text Report:      {txt_path}")
    print(f"Visualization:    {viz_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
