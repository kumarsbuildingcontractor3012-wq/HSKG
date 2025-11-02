"""
Data preprocessing module for HSKG.
Handles text cleaning, tokenization, and other preprocessing tasks.
"""
from typing import List, Dict, Any, Optional, Union
import re
import spacy
from spacy.language import Language
from spacy.tokens import Doc
import pandas as pd
import numpy as np

class DataPreprocessor:
    """Handles preprocessing of text data for the HSKG system."""
    
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        """
        Initialize the data preprocessor.
        
        Args:
            spacy_model: Name of the spaCy model to use for NLP tasks
        """
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            # If the model is not found, try to download it
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "spacy", "download", spacy_model])
            self.nlp = spacy.load(spacy_model)
        
        # Custom pipeline components
        self._add_custom_pipeline_components()
    
    def _add_custom_pipeline_components(self):
        """Add custom pipeline components if they don't exist."""
        if not self.nlp.has_pipe("custom_sentencizer"):
            self.nlp.add_pipe("sentencizer", name="custom_sentencizer")
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Input text to clean
            
        Returns:
            Cleaned text
        """
        if not isinstance(text, str):
            return ""
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', '', text, re.I|re.A)
        # Convert to lowercase
        text = text.lower()
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def tokenize(self, text: str, remove_stopwords: bool = True) -> List[str]:
        """
        Tokenize text into words.
        
        Args:
            text: Input text to tokenize
            remove_stopwords: Whether to remove stopwords
            
        Returns:
            List of tokens
        """
        doc = self.nlp(text)
        if remove_stopwords:
            tokens = [token.text for token in doc if not token.is_stop and not token.is_punct]
        else:
            tokens = [token.text for token in doc if not token.is_punct]
        return tokens
    
    def lemmatize(self, text: str) -> str:
        """
        Lemmatize text.
        
        Args:
            text: Input text to lemmatize
            
        Returns:
            Lemmatized text
        """
        doc = self.nlp(text)
        lemmas = [token.lemma_ for token in doc if not token.is_punct and not token.is_stop]
        return ' '.join(lemmas)
    
    def get_named_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.
        
        Args:
            text: Input text
            
        Returns:
            List of dictionaries containing entity text and label
        """
        doc = self.nlp(text)
        entities = []
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
        return entities
    
    def preprocess_dataframe(self, df: pd.DataFrame, text_column: str, 
                           clean_text: bool = True, lemmatize: bool = False,
                           add_entities: bool = False) -> pd.DataFrame:
        """
        Preprocess text data in a DataFrame.
        
        Args:
            df: Input DataFrame
            text_column: Name of the column containing text data
            clean_text: Whether to clean the text
            lemmatize: Whether to lemmatize the text
            add_entities: Whether to add named entities as a new column
            
        Returns:
            Preprocessed DataFrame
        """
        df = df.copy()
        
        # Clean text if requested
        if clean_text:
            df[f'{text_column}_cleaned'] = df[text_column].apply(self.clean_text)
            text_col = f'{text_column}_cleaned'
        else:
            text_col = text_column
        
        # Lemmatize if requested
        if lemmatize:
            df[f'{text_col}_lemmatized'] = df[text_col].apply(self.lemmatize)
        
        # Add named entities if requested
        if add_entities:
            df['named_entities'] = df[text_col].apply(self.get_named_entities)
        
        return df
