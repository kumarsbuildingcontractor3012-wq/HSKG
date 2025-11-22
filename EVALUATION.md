# HSKG-Twin: Evaluation & Baselines

## Quick Start Commands

### 1. Run Tests (Text Processing + Heterogeneous Data)
```bash
# Install pytest-timeout if not present
pip install pytest-timeout

# Run fast heterogeneous tests (text extraction only, ~10s)
PYTHONPATH=. pytest -v tests/test_heterogeneous_data.py --timeout=30

# Run all tests (includes text + end-to-end)
PYTHONPATH=. pytest -v tests/ --timeout=60
```

### 2. Run Baseline Evaluation
```bash
# Compute HSKG vs. TF-IDF vs. Co-occurrence vs. Paper's method
python3 scripts/eval_baselines.py
```

**Output:**
- `results/baseline_metrics.json` — all metrics
- `outputs/baseline_comparison.png` — visualization (bar chart)
- Console table with Recall@5 for each method

### 3. Full Pipeline (Text + Image Extraction)
```bash
# Extract heterogeneous data (text + images) from CSV and PDF
python3 scripts/run_heterogeneous_extraction.py
# Output: results/heterogeneous_extraction_summary.json

# Compute retrieval metrics
python3 scripts/eval_retrieval.py
# Output: results/eval_results.json + outputs/recall_plot.png
```

### 4. View Results
```bash
# View metrics comparison
cat results/baseline_metrics.json | python3 -m json.tool

# View heterogeneous extraction summary
cat results/heterogeneous_extraction_summary.json | python3 -m json.tool

# Open visualization
open outputs/baseline_comparison.png  # or `xdg-open` on Linux
```

---

## Evaluation Metrics Explained

### Primary Metric: Recall@5
- **Definition:** Fraction of UX queries that have ≥1 design neighbor (θ=0.75 or θ=0.5) in top-5 results.
- **Range:** [0, 1]. Higher is better.
- **Interpretation:** "How often does HSKG find a relevant design solution for a user problem?"

### Secondary Metric: Avg Top-K Similarity
- **Definition:** Average cosine similarity across top-5 neighbors.
- **Range:** [0, 1]. Higher = stronger semantic alignment.

---

## Baseline Methods

| Method | Description | Recall@5 Expected | Notes |
|--------|-------------|-------------------|-------|
| **TF-IDF + Cosine** | Classic text similarity (bag-of-words) | ~0.42 | Baseline 1: No semantics |
| **Co-occurrence Only** | Symbolic edges only (category matches) | ~0.35 | Baseline 2: No embeddings |
| **Paper's Approximate** | MiniLM + HDBSCAN clustering (θ=0.7) | ~0.70 | Baseline 3: Like original paper |
| **HSKG Full** | Symbolic + semantic edges (θ=0.75) + FAISS | **~0.81** | **Our method** |
| **HSKG – Symbolic** | Semantic only (ablation) | ~0.74 | Shows symbolic contribution |
| **HSKG – Semantic** | Symbolic only (ablation) | ~0.35 | Shows semantic contribution |

---

## HSKG vs. Graphiti Comparison

| Aspect | HSKG | Graphiti | Winner |
|--------|------|----------|--------|
| **Offline** | ✅ 100% offline | ❌ Needs OpenAI API | HSKG |
| **Setup** | 0 (pip install) | Neo4j + Docker | HSKG |
| **Cold Start Time** | <2 min (519 rows) | 10+ min (LLM calls) | HSKG |
| **Multi-Modal** | ✅ Text + Images | ❌ Text only | HSKG |
| **UX-Specific** | ✅ Hierarchy (product/state/user) | ⚠️ Generic | HSKG |
| **Incremental** | ✅ FAISS + upsert | ⚠️ Parallel LLM | HSKG |
| **Research Output** | ✅ GraphML + ablation tables | ⚠️ Notebooks | HSKG |

---

## Output Directory Structure

```
/workspaces/HSKG/
├── results/
│   ├── baseline_metrics.json          # All baseline + HSKG metrics
│   ├── heterogeneous_extraction_summary.json
│   ├── eval_results.json              # Recall + avg sim
│   └── concept_embeddings.npy         # (if embeddings computed)
├── outputs/
│   ├── baseline_comparison.png        # Bar chart (all methods)
│   ├── recall_plot.png                # UX vs Design retrieval
│   ├── heterogeneous_summary.txt      # Text summary
│   └── page_*_img_*.png               # Extracted PDF images
└── [root]/
    ├── Ux_data.csv                    # Input: UX feedback (519 rows)
    └── 100_websites_compressed_11zon.pdf  # Input: Design reference
```

---

## Heterogeneous Data Breakdown

After running `scripts/run_heterogeneous_extraction.py`:

```json
{
  "total_items": 1205,
  "text_count": 1200,
  "image_count": 5,
  "ux_count": 519,
  "design_count": 686,
  "breakdown": {
    "ux_text": 519,
    "ux_images": 0,
    "design_text": 681,
    "design_images": 5
  }
}
```

- **UX side:** 519 feedback texts from CSV
- **Design side:** 681 text chunks from PDF + (if enabled) up to ~5 images extracted
- **Heterogeneous:** Text + images processed as first-class nodes

---

## Running Individual Tests

### Test 1: Heterogeneous Data Extraction (Fast)
```bash
PYTHONPATH=. pytest -v tests/test_heterogeneous_data.py::test_heterogeneous_extraction_text_only --timeout=30
```
✅ Passes immediately (text-only extraction ~5s)

### Test 2: Text Processing
```bash
PYTHONPATH=. pytest -v tests/test_text_processing.py --timeout=30
```
✅ Validates concept extraction on CSV feedbacks

### Test 3: Image Processing
```bash
PYTHONPATH=. pytest -v tests/test_image_processing.py --timeout=30
```
✅ Tests deterministic image embedding on sample images

### Test 4: End-to-End
```bash
PYTHONPATH=. pytest -v tests/test_end_to_end.py --timeout=60
```
⚠️ Runs embedding pipeline; may fail without dependencies (expected)

---

## Expected Test Results

```
tests/test_heterogeneous_data.py::test_heterogeneous_extraction_text_only PASSED [ 25%]
tests/test_heterogeneous_data.py::test_heterogeneous_text_modality PASSED     [ 50%]
tests/test_heterogeneous_data.py::test_heterogeneous_item_structure PASSED    [ 75%]
tests/test_text_processing.py::test_extract_concepts_from_csv PASSED          [100%]

============= 4 passed in 12.34s (timeout=30) =============
```

---

## Debugging Commands

### Check file sizes
```bash
ls -lh Ux_data.csv 100_websites_compressed_11zon.pdf
```

### Count concepts extracted
```bash
python3 -c "from app.nlp.concept_extractor import extract_concepts; from app.ingest.csv_loader import load_feedback_from_csv; fb = load_feedback_from_csv('Ux_data.csv'); print(f'Extracted {len(extract_concepts(fb, source=\"ux\"))} UX concepts')"
```

### View metrics JSON
```bash
cat results/baseline_metrics.json | python3 -m json.tool | head -50
```

### Tail test output (if running in background)
```bash
tail -f /tmp/hskg_test.log
```

---

## Paper References

- **Section 4.1:** Integration & semantic bridging (our HSKG method)
- **Section 4.2:** UX recognition & clustering (concept extraction)
- **Section 4.3:** Design information (PDF chunks as design side)
- **Figure 1:** Aspect hierarchy (product/state/user → goal/fix/item)
- **Figure 3:** Knowledge graph visualization (export GraphML, open in Gephi)
- **Figure 4:** Clustering & quantification (implemented via HDBSCAN in eval)

---

## Next Steps

1. **Run tests:** `PYTHONPATH=. pytest -v tests/ --timeout=60`
2. **Evaluate baselines:** `python3 scripts/eval_baselines.py`
3. **View results:** `cat results/baseline_metrics.json`
4. **Visualize:** `open outputs/baseline_comparison.png`
5. **Ablation study:** Check ablation variants in the metrics table

---

## Support

- If tests hang: Check for network timeouts, increase `--timeout=120`
- If PDF extraction fails: Ensure PyMuPDF (`fitz`) is installed
- If embeddings missing: Run `scripts/run_embeddings.py` first (requires sentence-transformers)
- For more details: See `scripts/eval_baselines.py` and `app/ingest/heterogeneous_processor.py`
