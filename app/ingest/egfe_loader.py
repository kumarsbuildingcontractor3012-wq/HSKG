"""EGFE Dataset loader: Parse UI element metadata as design concepts.

The EGFE-dataset (tests/fixtures/EGFE-dataset/) contains JSON files with
UI element properties (type, name, role, bounding box, style, etc.).

This loader extracts textual descriptions from UI elements to create
"design concepts" for the heterogeneous system.

Reference: https://github.com/google/UI2Code
"""

import json
from pathlib import Path
from typing import List, Optional


def load_ui_element_descriptions(egfe_dir: str) -> List[str]:
    """
    Parse EGFE JSON files and extract UI element text descriptions.
    
    EGFE format: each JSON file has "layers" array with UI elements.
    We extract element name, class, label, and position to create descriptions.
    
    Args:
        egfe_dir: Path to EGFE-dataset folder (e.g., tests/fixtures/EGFE-dataset)
        
    Returns:
        List of text descriptions (one per UI element)
    """
    descriptions = []
    egfe_path = Path(egfe_dir)
    
    if not egfe_path.exists():
        return descriptions
    
    # Find all .json files in EGFE-dataset
    json_files = sorted(egfe_path.glob("*.json"))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        
        # EGFE structure: {"layers": [...]}
        layers = []
        if isinstance(data, dict):
            layers = data.get("layers", [])
        elif isinstance(data, list):
            layers = data
        
        # Extract text from each layer/element
        for elem in layers:
            if not isinstance(elem, dict):
                continue
            
            parts = []
            
            # Collect textual fields from EGFE structure
            name = elem.get("name", "")
            elem_class = elem.get("_class", "")
            label = elem.get("label", None)
            
            if name:
                parts.append(name)
            if elem_class:
                parts.append(elem_class)
            if label is not None:
                parts.append(f"label_{label}")
            
            # Also try generic fields
            for key in ["type", "text", "role", "id", "placeholder", "title"]:
                val = elem.get(key, "")
                if val and isinstance(val, str):
                    parts.append(val.strip())
            
            # Create combined description
            if parts:
                desc = " ".join(parts)
                if desc and len(desc) > 5:
                    descriptions.append(desc)
    
    return descriptions


def load_egfe_as_design_texts(egfe_dir: str, sample_size: Optional[int] = None) -> List[str]:
    """
    Convenience: load EGFE-dataset and return UI descriptions (design source).
    
    Args:
        egfe_dir: Path to EGFE-dataset folder
        sample_size: If set, return only first N items (for quick testing)
        
    Returns:
        List of UI element descriptions
    """
    items = load_ui_element_descriptions(egfe_dir)
    
    # Deduplicate
    items = list(dict.fromkeys(items))
    
    if sample_size and len(items) > sample_size:
        items = items[:sample_size]
    
    return items
