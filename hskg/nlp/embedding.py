"""
Embedding generation module for HSKG.
Handles text embedding generation using various models.
"""
from typing import List, Dict, Any, Union, Optional
import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer
from sentence_transformers import SentenceTransformer

class EmbeddingGenerator:
    """
    Generates embeddings for text using various models.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', device: str = None):
        """
        Initialize the embedding generator.
        
        Args:
            model_name: Name of the model to use for embeddings
            device: Device to run the model on ('cuda' or 'cpu')
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load the specified model and tokenizer."""
        try:
            # Try loading as a SentenceTransformer model first
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self.model_type = 'sentence_transformers'
        except:
            try:
                # Fall back to HuggingFace transformers
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
                self.model_type = 'transformers'
            except Exception as e:
                raise ValueError(f"Failed to load model {self.model_name}: {str(e)}")
    
    def get_embedding(self, text: Union[str, List[str]], 
                     batch_size: int = 32, 
                     convert_to_numpy: bool = True) -> Union[np.ndarray, torch.Tensor]:
        """
        Generate embeddings for the input text(s).
        
        Args:
            text: Input text or list of texts
            batch_size: Batch size for processing
            convert_to_numpy: Whether to convert the output to numpy array
            
        Returns:
            Embeddings as numpy array or PyTorch tensor
        """
        if isinstance(text, str):
            texts = [text]
        else:
            texts = text
        
        if self.model_type == 'sentence_transformers':
            embeddings = self.model.encode(texts, batch_size=batch_size, 
                                         convert_to_numpy=convert_to_numpy,
                                         show_progress_bar=False)
        else:  # transformers
            inputs = self.tokenizer(texts, padding=True, truncation=True, 
                                  return_tensors='pt', max_length=512).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs, return_dict=True)
                # Use mean pooling on token embeddings
                embeddings = self._mean_pooling(outputs, inputs['attention_mask'])
                if convert_to_numpy:
                    embeddings = embeddings.cpu().numpy()
        
        return embeddings[0] if isinstance(text, str) else embeddings
    
    def _mean_pooling(self, model_output, attention_mask):
        """Apply mean pooling to get sentence embeddings from token embeddings."""
        token_embeddings = model_output.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    def get_similarity(self, text1: Union[str, List[str]], 
                      text2: Union[str, List[str]], 
                      batch_size: int = 32) -> np.ndarray:
        """
        Calculate cosine similarity between two sets of texts.
        
        Args:
            text1: First text or list of texts
            text2: Second text or list of texts
            batch_size: Batch size for processing
            
        Returns:
            Array of similarity scores
        """
        from sklearn.metrics.pairwise import cosine_similarity
        
        emb1 = self.get_embedding(text1, batch_size=batch_size)
        emb2 = self.get_embedding(text2, batch_size=batch_size)
        
        if len(emb1.shape) == 1:
            emb1 = emb1.reshape(1, -1)
        if len(emb2.shape) == 1:
            emb2 = emb2.reshape(1, -1)
            
        return cosine_similarity(emb1, emb2)
