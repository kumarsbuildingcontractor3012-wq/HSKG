"""
NLP module for HSKG.
Handles concept extraction, semantic analysis, and other NLP tasks.
"""

from .concept_extractor import ConceptExtractor
from .embedding import EmbeddingGenerator

__all__ = ['ConceptExtractor', 'EmbeddingGenerator']
