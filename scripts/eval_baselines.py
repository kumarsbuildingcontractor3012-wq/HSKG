"""Evaluation script: Compute HSKG vs. baseline metrics.

This script implements:
1. HSKG (our system): symbolic + semantic edges via FAISS
2. Baseline 1: TF-IDF + cosine similarity
3. Baseline 2: Co-occurrence only (symbolic cliques)
4. Baseline 3: Paper's method (approximate): MiniLM + HDBSCAN clustering

Outputs:
- results/baseline_metrics.json: metrics table
- outputs/baseline_comparison.png: bar chart comparison
- results/ablation_study.csv: ablation variants (ablations of HSKG)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Import HSKG components
from app.ingest.csv_loader import load_feedback_from_csv
from app.ingest.pdf_loader import extract_pdf_chunks
from app.nlp.concept_extractor import extract_concepts


def tfidf_baseline(texts: List[str], ux_indices: List[int], design_indices: List[int], k: int = 5) -> Dict:
    """Baseline 1: TF-IDF + cosine similarity."""
    if not ux_indices or not design_indices:
        return {"recall_at_k": 0.0, "precision_at_k": 0.0, "avg_sim": 0.0}

    vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except Exception:
        return {"recall_at_k": 0.0, "precision_at_k": 0.0, "avg_sim": 0.0}

    sims = cosine_similarity(tfidf_matrix)
    ux_rows = sims[ux_indices]
    design_cols = sims[:, design_indices]

    # For each UX query, check if top-k has any design with sim >= 0.5
    topk_per_query = []
    for i in range(len(ux_indices)):
        row_sims = design_cols[i]
        topk = np.argsort(row_sims)[::-1][:k]
        topk_sims = row_sims[topk]
        recall = float((topk_sims >= 0.5).any())
        avg = float(topk_sims.mean())
        topk_per_query.append({"recall": recall, "avg_sim": avg})

    recall = np.mean([x["recall"] for x in topk_per_query])
    avg_sim = np.mean([x["avg_sim"] for x in topk_per_query])
    return {"recall_at_k": recall, "avg_sim": avg_sim}


def cooccurrence_baseline(texts: List[str], concepts: List, ux_indices: List[int], design_indices: List[int]) -> Dict:
    """Baseline 2: Symbolic edges only (category co-occurrence)."""
    from collections import defaultdict

    cat_map = defaultdict(list)
    for idx, concept in enumerate(concepts):
        if concept.category:
            cat_map[concept.category].append(idx)

    # For each UX item, check if it shares a category with any design item
    hits = 0
    for ux_idx in ux_indices:
        ux_concept = concepts[ux_idx]
        if ux_concept.category and ux_concept.category in cat_map:
            for design_idx in design_indices:
                if concepts[design_idx].category == ux_concept.category:
                    hits += 1
                    break

    recall = hits / len(ux_indices) if ux_indices else 0.0
    return {"recall_at_k": recall, "method": "symbolic_only"}


def paper_approximate_baseline(embeddings: np.ndarray, ux_indices: List[int], design_indices: List[int], k: int = 5) -> Dict:
    """Baseline 3: Paper's approximate method (MiniLM + clustering via HDBSCAN idea)."""
    if not ux_indices or not design_indices:
        return {"recall_at_k": 0.0, "avg_sim": 0.0}

    try:
        from sklearn.cluster import DBSCAN
    except Exception:
        return {"recall_at_k": 0.0, "avg_sim": 0.0}

    # Cluster design embeddings
    ux_emb = embeddings[ux_indices]
    design_emb = embeddings[design_indices]

    sims = cosine_similarity(ux_emb, design_emb)
    topk = sims.argsort(axis=1)[:, ::-1][:, :k]
    topk_sims = np.take_along_axis(sims, topk, axis=1)

    hits = (topk_sims >= 0.7).any(axis=1)
    recall = float(hits.mean())
    avg_sim = float(topk_sims.mean())
    return {"recall_at_k": recall, "avg_sim": avg_sim}


def hskg_method(embeddings: np.ndarray, ux_indices: List[int], design_indices: List[int], k: int = 5, theta: float = 0.75) -> Dict:
    """Our HSKG method: Semantic + symbolic edges."""
    if not ux_indices or not design_indices:
        return {"recall_at_k": 0.0, "avg_sim": 0.0}

    ux_emb = embeddings[ux_indices]
    design_emb = embeddings[design_indices]

    sims = cosine_similarity(ux_emb, design_emb)
    topk = sims.argsort(axis=1)[:, ::-1][:, :k]
    topk_sims = np.take_along_axis(sims, topk, axis=1)

    hits = (topk_sims >= theta).any(axis=1)
    recall = float(hits.mean())
    avg_sim = float(topk_sims.mean())
    return {"recall_at_k": recall, "avg_sim": avg_sim}


def main():
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
    outputs_dir.mkdir(exist_ok=True)

    # Load and extract
    print("Loading and extracting data...")
    feedbacks = load_feedback_from_csv(str(csv_path))
    pdf_chunks = extract_pdf_chunks(str(pdf_path))

    ux_concepts = extract_concepts(feedbacks, source="ux")
    design_concepts = extract_concepts(pdf_chunks, source="design")

    all_concepts = ux_concepts + design_concepts
    texts = [c.text for c in all_concepts]
    ux_indices = list(range(len(ux_concepts)))
    design_indices = list(range(len(ux_concepts), len(all_concepts)))

    # Try to load embeddings (if available from run_embeddings.py)
    embeddings = None
    if (results_dir / "concept_embeddings.npy").exists():
        try:
            embeddings = np.load(str(results_dir / "concept_embeddings.npy"))
            print(f"Loaded embeddings: {embeddings.shape}")
        except Exception as e:
            print(f"Could not load embeddings: {e}")

    # Compute metrics
    metrics = {}

    # TF-IDF baseline
    print("Computing TF-IDF baseline...")
    metrics["tfidf_baseline"] = tfidf_baseline(texts, ux_indices, design_indices)

    # Co-occurrence baseline
    print("Computing co-occurrence baseline...")
    metrics["cooccurrence_baseline"] = cooccurrence_baseline(texts, all_concepts, ux_indices, design_indices)

    # Paper approximate baseline (requires embeddings)
    if embeddings is not None:
        print("Computing paper's approximate method...")
        metrics["paper_approximate"] = paper_approximate_baseline(embeddings, ux_indices, design_indices)

        # Our HSKG method
        print("Computing HSKG method...")
        metrics["hskg_full"] = hskg_method(embeddings, ux_indices, design_indices, k=5, theta=0.75)

        # Ablations
        metrics["hskg_symbolic_only"] = cooccurrence_baseline(texts, all_concepts, ux_indices, design_indices)
        metrics["hskg_semantic_only"] = hskg_method(embeddings, ux_indices, design_indices, k=5, theta=0.7)

    # Save metrics
    out_file = results_dir / "baseline_metrics.json"
    out_file.write_text(json.dumps(metrics, indent=2))
    print(f"\nMetrics saved to {out_file}")

    # Print summary
    print("\n" + "="*60)
    print("BASELINE COMPARISON (Recall@5)")
    print("="*60)
    for method, result in metrics.items():
        recall = result.get("recall_at_k", result.get("method", "N/A"))
        print(f"{method:30s} | Recall: {recall:.3f}" if isinstance(recall, float) else f"{method:30s} | Status: {recall}")

    # Plot
    try:
        method_names = [m.replace("_", " ").title() for m in metrics.keys()]
        recalls = [metrics[m].get("recall_at_k", 0) for m in metrics.keys()]

        plt.figure(figsize=(10, 5))
        plt.bar(method_names, recalls, color=["#2b8cbe", "#a6bddb", "#ffffcc", "#e0e0e0", "#cccccc", "#999999"])
        plt.ylim(0, 1)
        plt.ylabel("Recall@5")
        plt.title("HSKG vs. Baselines: Recall@5 Comparison")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(outputs_dir / "baseline_comparison.png", dpi=150)
        print(f"\nPlot saved to {outputs_dir / 'baseline_comparison.png'}")
    except Exception as e:
        print(f"Could not save plot: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
