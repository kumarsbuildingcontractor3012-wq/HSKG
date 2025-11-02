""
Graph storage interface and implementations for HSKG.
Defines the storage backend interface and factory methods.
"""
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Type, TypeVar, Generic, Union
import json

from hskg.graph import KnowledgeGraph, Node, Relation

T = TypeVar('T', bound='StorageBackend')


class StorageType(Enum):
    """Supported storage backends."""
    POSTGRES = auto()
    NEO4J = auto()
    IN_MEMORY = auto()
    # Add more storage types as needed


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def save_graph(self, graph: KnowledgeGraph, name: str = None) -> str:
        """
        Save a knowledge graph to the storage backend.
        
        Args:
            graph: The knowledge graph to save
            name: Optional name for the graph
            
        Returns:
            ID of the saved graph
        """
        pass
    
    @abstractmethod
    def load_graph(self, graph_id: str) -> KnowledgeGraph:
        """
        Load a knowledge graph from the storage backend.
        
        Args:
            graph_id: ID of the graph to load
            
        Returns:
            The loaded knowledge graph
        """
        pass
    
    @abstractmethod
    def delete_graph(self, graph_id: str) -> bool:
        """
        Delete a knowledge graph from the storage backend.
        
        Args:
            graph_id: ID of the graph to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def list_graphs(self) -> List[Dict[str, Any]]:
        """
        List all stored knowledge graphs.
        
        Returns:
            List of graph metadata dictionaries
        """
        pass


class GraphStorage:
    """
    Factory class for creating and managing storage backends.
    Provides a unified interface to different storage implementations.
    """
    _backends: Dict[StorageType, Type[StorageBackend]] = {}
    
    @classmethod
    def register_backend(cls, storage_type: StorageType, backend_class: Type[StorageBackend]):
        """Register a storage backend implementation."""
        cls._backends[storage_type] = backend_class
    
    @classmethod
    def create_storage(cls, 
                      storage_type: Union[StorageType, str],
                      **kwargs) -> StorageBackend:
        """
        Create a storage backend instance.
        
        Args:
            storage_type: Type of storage backend to create
            **kwargs: Additional arguments for the storage backend
            
        Returns:
            An instance of the requested storage backend
            
        Raises:
            ValueError: If the storage type is not supported
        """
        if isinstance(storage_type, str):
            try:
                storage_type = StorageType[storage_type.upper()]
            except KeyError:
                raise ValueError(f"Unknown storage type: {storage_type}")
        
        if storage_type not in cls._backends:
            raise ValueError(f"No backend registered for storage type: {storage_type}")
        
        return cls._backends[storage_type](**kwargs)
    
    @classmethod
    def get_available_backends(cls) -> List[StorageType]:
        """Get a list of available storage backends."""
        return list(cls._backends.keys())


# Register built-in backends
from hskg.db.postgres_storage import PostgresStorage
from hskg.db.in_memory_storage import InMemoryStorage

GraphStorage.register_backend(StorageType.POSTGRES, PostgresStorage)
GraphStorage.register_backend(StorageType.IN_MEMORY, InMemoryStorage)
