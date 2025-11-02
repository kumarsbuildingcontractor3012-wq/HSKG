"""
Node module for HSKG knowledge graph.
Defines the Node class and NodeType enum for the knowledge graph.
"""
from enum import Enum, auto
from typing import Dict, Any, Optional, List
import uuid
import numpy as np
from datetime import datetime


class NodeType(Enum):
    """Types of nodes in the knowledge graph."""
    ENTITY = auto()
    CONCEPT = auto()
    DOCUMENT = auto()
    USER = auto()
    PRODUCT = auto()
    REVIEW = auto()
    FEATURE = auto()
    CATEGORY = auto()
    INTENT = auto()
    TOPIC = auto()
    CUSTOM = auto()


class Node:
    """Represents a node in the knowledge graph."""
    
    def __init__(self, 
                 node_type: NodeType, 
                 name: str, 
                 properties: Optional[Dict[str, Any]] = None,
                 embedding: Optional[np.ndarray] = None):
        """
        Initialize a knowledge graph node.
        
        Args:
            node_type: Type of the node
            name: Name/identifier of the node
            properties: Additional properties as key-value pairs
            embedding: Optional vector embedding of the node
        """
        self.id = str(uuid.uuid4())
        self.type = node_type
        self.name = name
        self.properties = properties or {}
        self.embedding = embedding
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at
        self.labels = [node_type.name]
    
    def add_property(self, key: str, value: Any) -> None:
        """Add or update a property."""
        self.properties[key] = value
        self.updated_at = datetime.utcnow()
    
    def add_label(self, label: str) -> None:
        """Add a label to the node."""
        if label not in self.labels:
            self.labels.append(label)
    
    def update_embedding(self, embedding: np.ndarray) -> None:
        """Update the node's embedding."""
        self.embedding = embedding
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the node to a dictionary."""
        return {
            'id': self.id,
            'type': self.type.name,
            'name': self.name,
            'properties': self.properties,
            'labels': self.labels,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'has_embedding': self.embedding is not None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """Create a Node from a dictionary."""
        node = cls(
            node_type=NodeType[data['type']],
            name=data['name'],
            properties=data.get('properties', {})
        )
        node.id = data['id']
        node.labels = data.get('labels', [])
        node.created_at = datetime.fromisoformat(data['created_at'])
        node.updated_at = datetime.fromisoformat(data['updated_at'])
        return node
    
    def __repr__(self) -> str:
        return f"<Node(id='{self.id}', type={self.type.name}, name='{self.name}')>"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
