""
Database module for HSKG.
Handles persistent storage of the knowledge graph.
"""

from .graph_storage import GraphStorage, StorageBackend, StorageType
from .postgres_storage import PostgresStorage
from .in_memory_storage import InMemoryStorage

__all__ = [
    'GraphStorage',
    'StorageBackend',
    'StorageType',
    'PostgresStorage',
    'InMemoryStorage'
]
