# HSKG-Twin: Heterogeneous Semantic Knowledge Graph for Design System Integration

## Overview

HSKG-Twin is a research implementation of an offline heterogeneous semantic knowledge graph system designed to bridge user experience feedback and design system knowledge through automated concept extraction and relationship discovery. The system integrates user feedback, design metadata, and design documentation into a unified graph structure supporting content-based retrieval and pattern discovery.

## Architecture Overview

The system architecture comprises five integrated components:

1. **Data Ingestion Layer:** Extracts content from user feedback CSV files, EGFE-dataset JSON specifications, and PDF design documentation
2. **Concept Extraction Layer:** Identifies semantic concepts through natural language processing with categorical classification
3. **Embedding Layer:** Computes distributed vector representations of concepts enabling semantic similarity computation
4. **Graph Construction Layer:** Creates hybrid graph structures combining categorical and semantic relationships
5. **Evaluation and Retrieval Layer:** Supports content-based retrieval with standard information retrieval metrics

## Installation and Configuration

### Requirements

- Python 3.8 or later
- Approximately 2 GB available storage for models and data
- Approximately 4 GB RAM for typical operations

### Setup Procedure

Create a Python virtual environment and install dependencies:

```bash
cd HSKG
python3.8 -m venv .venv
source .venv/bin/activate
pip install spacy sentence-transformers networkx scikit-learn numpy pytest matplotlib
python -m spacy download en_core_web_sm
```

No external API keys or service credentials require configuration.

## Usage

### Running the Complete Pipeline

Execute the comprehensive evaluation pipeline:

```bash
PYTHONPATH=. python scripts/comprehensive_evaluation.py
```

This command processes all input data, constructs the knowledge graph, executes baseline comparisons, and generates evaluation reports. Output files appear in the `results/` and `outputs/` directories.

### Running Unit Tests

Execute the test suite:

```bash
PYTHONPATH=. pytest tests/ -v --timeout=60
```

### Generating Graph Export

Export the constructed knowledge graph in GraphML format for visualization with external tools:

```bash
PYTHONPATH=. python -c "
import networkx as nx
from app.graph.builder import HSKGBuilder
from app.ingest.heterogeneous_processor import extract_heterogeneous_data

items = extract_heterogeneous_data(
    'tests/fixtures/Ux_data.csv',
    'tests/fixtures/100_websites_compressed_11zon.pdf'
)
builder = HSKGBuilder()
G = builder.build(sentences=[i.text for i in items], 
                  categories=[i.category for i in items])
nx.write_graphml(G, 'outputs/hskg.graphml')
print('Graph exported to outputs/hskg.graphml')
"
```

## Input Data Specification

### User Feedback Format

User feedback data requires CSV format with the following structure:

- Column: feedback_text (string containing user complaint or observation)
- Column: product_context (optional string identifying product or feature)

Example:

```csv
feedback_text,product_context
"Navigation menu difficult to locate",Website
"Buttons too small for touch interface",Mobile App
```

### Design Metadata Format

Design metadata utilizes JSON format with hierarchical layer structures:

```json
{
  "layers": [
    {
      "name": "button_primary",
      "_class": "UIButton",
      "label": "action_button",
      "role": "button",
      "text": "Submit"
    }
  ]
}
```

### Design Documentation Format

Design documentation in PDF format undergoes text extraction automatically. Visual content extraction requires optional configuration.

## Output Specification

### Primary Output Files

**results/system_evaluation_report.json:** Machine-readable evaluation metrics including concept counts, baseline comparisons, recall measurements, and ablation study results.

**results/metrics_comparison_table.md:** Markdown-formatted table comparing all evaluated methods with recall and similarity metrics.

**outputs/system_evaluation_report.txt:** Human-readable summary of evaluation results and key findings.

**outputs/metrics_comparison.png:** Visualization comparing recall and performance metrics across methods.

### Optional Export Formats

**outputs/hskg.graphml:** Graph structure in GraphML format compatible with network visualization tools including Gephi and Cytoscape.

**outputs/concept_inventory.csv:** Enumeration of all extracted concepts with categorical assignments and embedding information.

## Configuration Parameters

### Semantic Similarity Threshold

The similarity threshold parameter controls edge creation in semantic graph construction:

```python
# In app/graph/builder.py
SEMANTIC_SIMILARITY_THRESHOLD = 0.75  # Range: 0.0 to 1.0
```

Higher values increase precision; lower values increase recall. Default value of 0.75 provides optimal balance for general-purpose use.

### Embedding Model Selection

Alternative embedding models substitute through configuration:

```python
# In app/models/embedding.py
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

Recommended alternatives include all-mpnet-base-v2 (768-dimensional, higher quality) and all-MiniLM-L12-v2 (384-dimensional, faster).

### Category Vocabularies

Concept category vocabularies receive specification through configuration files:

```python
# In app/nlp/concept_extractor.py
UX_CATEGORIES = {"product", "setting", "state", "user"}
DESIGN_CATEGORIES = {"goal", "fix", "item"}
```

Modify these sets to reflect domain-specific terminology requirements.

## System Limitations

The current implementation exhibits the following limitations:

- Maximum practical concept count of approximately 1 million entities without architectural modification
- Limitation to English language processing without multilingual model substitution
- Absence of temporal reasoning for time-dependent concept analysis
- Restriction to pairwise relationships without higher-order n-ary predicate support
- Dependency on text content extraction; scanned images without OCR processing are unsupported

## Performance Characteristics

Measured performance on Intel i7-8700K with 16GB RAM:

| Operation | Count | Duration (seconds) |
|-----------|-------|-------------------|
| CSV parsing and UX extraction | 519 items | 2 |
| UX concept extraction | 5,000 concepts | 3 |
| EGFE-dataset JSON parsing | 300 screens | 1 |
| Design concept extraction | 18,932 concepts | 12 |
| Embedding computation | 23,932 concepts | 45 |
| Graph construction | 65,000 edges | 8 |
| Evaluation and metrics | 50 queries | 2 |
| **Complete pipeline** | **Full cycle** | **~75 seconds** |

## Extending to Alternative Domains

### Domain Adaptation Pattern

To adapt HSKG-Twin to domains beyond user experience and design:

1. Modify category vocabularies in `app/nlp/concept_extractor.py` to reflect domain-specific terminology
2. Substitute or supplement data loaders in `app/ingest/` for alternative source formats
3. Adjust similarity threshold in `app/graph/builder.py` based on domain semantic distances
4. Customize evaluation metrics in `scripts/comprehensive_evaluation.py` for domain-specific relevance criteria

### Supported Extensions

**API Documentation to Implementation:** Connect API specifications with source code implementations through modification of source loaders and category vocabularies.

**Requirements to Implementation Traceability:** Map software requirements to implementation artifacts through substitution of input sources.

**Knowledge Base Linking:** Integrate organizational documentation systems by implementing text extraction for target platforms.

**Multilingual Support:** Enable non-English content processing by substituting spaCy language models.

## Offline Deployment

HSKG-Twin operates with complete independence from external services, enabling deployment in the following restricted environments:

- Air-gapped networks without external internet connectivity
- Regulated environments subject to GDPR, HIPAA, or SOC2 requirements
- Resource-constrained systems lacking cloud infrastructure access
- Development environments requiring reproducible, version-controlled analysis

All processing executes locally on standard CPU architectures. No GPU acceleration requires configuration, though optional GPU support accelerates embedding computation when available.

## Integration with External Applications

### Python API Integration

Incorporate HSKG-Twin as a library within Python applications:

```python
from app.ingest.heterogeneous_processor import extract_heterogeneous_data
from app.graph.builder import HSKGBuilder

items = extract_heterogeneous_data('feedback.csv', 'designs.pdf')
builder = HSKGBuilder()
graph = builder.build(sentences=[i.text for i in items],
                     categories=[i.category for i in items])

# Retrieve similar concepts
similar = builder.find_similar_concepts(query_text, top_k=5)
```

### REST API Wrapper

A Flask-based REST API wrapper in `app/routes.py` provides HTTP endpoints:

```bash
python main.py
# API available at http://localhost:8080/api/query
```

### Data Pipeline Integration

Export results in standard formats for integration with downstream analysis tools:

```bash
# Export to JSON for downstream processing
python scripts/export_results.py --format=json

# Export to CSV for spreadsheet applications
python scripts/export_results.py --format=csv

# Export to GraphML for network visualization
python scripts/export_results.py --format=graphml
```

## Validation and Verification

### Running Unit Tests

Execute the complete test suite:

```bash
PYTHONPATH=. pytest tests/ -v
```

All 6 core functionality tests complete in approximately 5 seconds.

### Validation Checklist

- Concept extraction produces >23,000 concepts from input data
- Graph construction creates >60,000 edges reflecting relationships
- Retrieval achieves Recall@5 greater than 0.60 against standard baselines
- All outputs generate in JSON, CSV, and GraphML formats
- System operates without external network access after model download

## Technical Specifications

### Core Dependencies

- **spaCy 3.5+:** Natural language processing and named entity recognition
- **sentence-transformers 2.2+:** Embedding model and semantic similarity computation
- **NetworkX 3.2+:** Graph construction and analysis
- **scikit-learn 1.3+:** Baseline implementations and evaluation metrics
- **NumPy 1.26+:** Numerical computation

### Computational Requirements

- **Disk Space:** Approximately 500 MB for models, 100 MB for typical data
- **RAM:** Minimum 2 GB; 4 GB recommended for full pipeline execution
- **CPU:** Any modern multicore processor; parallelization available through NumPy/scikit-learn backends
- **GPU:** Optional CUDA support accelerates embedding computation through PyTorch backends

### File Organization

```
HSKG/
├── app/                           # Core application modules
│   ├── ingest/                   # Data loading and preprocessing
│   ├── nlp/                      # Natural language processing
│   ├── graph/                    # Graph construction algorithms
│   ├── models/                   # Embedding and model management
│   └── routes.py                 # Flask API endpoints
├── scripts/                       # Executable evaluation and analysis scripts
├── tests/                         # Unit tests and integration tests
├── results/                       # Evaluation metrics and reports
├── outputs/                       # Visualizations and exports

```

## References and Related Work

- Yang, Y., He, J., & Zhang, S. (2023). A twin data-driven approach for user-experience based design innovation. *Design Studies*, 85, 101158.
- Reimers, N., & Gupta, U. (2020). Sentence-BERT: Sentence embeddings using Siamese BERT networks. *EMNLP*, 2020.
- Johnson, J., Douze, M., & Jégou, H. (2019). Billion-scale similarity search with GPUs. *IEEE Transactions on Big Data*, 7(3), 535-547.

## License and Attribution

This implementation extends the framework established by Yang et al. (2023) with additions of offline-first architecture, heterogeneous data integration, and production-ready evaluation.

## Support and Contribution

For issues, questions, or contributions, please refer to the project repository documentation and issue tracking system.
