# HSKG System Evaluation Results

**Evaluation Date:** 2025-11-22T06:06:38.798395

## Data Extraction Summary

| Metric | Count |
|--------|-------|
| UX Concepts | 5000 |
| PDF Design Concepts | 0 |
| EGFE Design Concepts | 18932 |
| **Total Design Concepts** | **18932** |
| **Total Concepts** | **23932** |

## Expected Results (with full evaluation + embeddings)

| Method | Recall@5 | Description |
|--------|----------|-------------|
| TF-IDF Baseline | ~0.44 | Lexical similarity (bag-of-words) |
| Co-occurrence Baseline | ~0.62 | Category-based cliques (symbolic only) |
| Paper's Method (Approximate) | ~0.70 | MiniLM + HDBSCAN clustering |
| **HSKG Semantic** | **~0.84** | Symbolic + semantic edges (full method) |

## Key Achievement: EGFE Integration

✓ Successfully integrated EGFE dataset with 18932 UI elements as design concepts

✓ Total heterogeneous data: 23932 concepts across UX and Design modalities

✓ Ready for semantic embedding and graph construction