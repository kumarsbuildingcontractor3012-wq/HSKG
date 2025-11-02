"""
Concept extraction module for HSKG.
Extracts key concepts and relationships from text.
"""
from typing import List, Dict, Any, Tuple, Set
import re
import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Span, Doc
import pandas as pd
from collections import defaultdict, Counter

class ConceptExtractor:
    """
    Extracts concepts and relationships from text using rule-based and statistical methods.
    """
    
    def __init__(self, nlp_model: Any = None, custom_patterns: Dict[str, List[str]] = None):
        """
        Initialize the concept extractor.
        
        Args:
            nlp_model: A loaded spaCy language model
            custom_patterns: Dictionary of custom patterns for concept extraction
        """
        self.nlp = nlp_model or spacy.load("en_core_web_sm")
        self.matcher = PhraseMatcher(self.nlp.vocab)
        self.patterns = custom_patterns or {}
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Set up the phrase matcher with custom patterns."""
        for label, patterns in self.patterns.items():
            self.matcher.add(label, [self.nlp(text) for text in patterns])
    
    def extract_concepts(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract concepts from text.
        
        Args:
            text: Input text to extract concepts from
            
        Returns:
            Dictionary of extracted concepts grouped by type
        """
        doc = self.nlp(text)
        matches = self.matcher(doc)
        
        concepts = defaultdict(list)
        for match_id, start, end in matches:
            span = doc[start:end]
            label = self.nlp.vocab.strings[match_id]
            concepts[label].append({
                'text': span.text,
                'start': start,
                'end': end,
                'span': span
            })
        
        # Add noun chunks as additional concepts
        for chunk in doc.noun_chunks:
            concepts['NOUN_CHUNK'].append({
                'text': chunk.text,
                'start': chunk.start,
                'end': chunk.end,
                'span': chunk
            })
        
        return dict(concepts)
    
    def extract_relations(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract relationships between concepts in text.
        
        Args:
            text: Input text to extract relationships from
            
        Returns:
            List of extracted relationships
        """
        doc = self.nlp(text)
        relations = []
        
        # Simple rule: look for verb-object and subject-verb patterns
        for sent in doc.sents:
            for token in sent:
                if token.dep_ in ('ROOT', 'VERB'):
                    subject = next((w for w in token.lefts if w.dep_ in ('nsubj', 'nsubjpass')), None)
                    obj = next((w for w in token.rights if w.dep_ in ('dobj', 'pobj', 'attr')), None)
                    
                    if subject and obj:
                        relations.append({
                            'subject': subject.text,
                            'relation': token.lemma_,
                            'object': obj.text,
                            'sentence': sent.text
                        })
        
        return relations
    
    def extract_key_phrases(self, text: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        Extract key phrases from text using TF-IDF like scoring.
        
        Args:
            text: Input text
            top_n: Number of top key phrases to return
            
        Returns:
            List of (phrase, score) tuples, sorted by score in descending order
        """
        doc = self.nlp(text)
        
        # Count word frequencies
        word_freq = Counter()
        for token in doc:
            if not token.is_stop and not token.is_punct and not token.is_space:
                word_freq[token.lemma_.lower()] += 1
        
        # Calculate phrase scores
        phrase_scores = {}
        for chunk in doc.noun_chunks:
            phrase = ' '.join(token.lemma_.lower() for token in chunk if not token.is_stop)
            if len(phrase.split()) > 1:  # Only consider multi-word phrases
                score = sum(word_freq.get(word, 0) for word in phrase.split()) / len(phrase.split())
                phrase_scores[phrase] = score
        
        # Sort by score and return top N
        return sorted(phrase_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
