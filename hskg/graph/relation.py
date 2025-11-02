"""
Relation module for HSKG knowledge graph.
Defines the Relation class and RelationType enum for the knowledge graph.
"""
from enum import Enum, auto
from typing import Dict, Any, Optional, TYPE_CHECKING
import uuid
from datetime import datetime

if TYPE_CHECKING:
    from .node import Node


class RelationType(Enum):
    """Types of relations in the knowledge graph."""
    # Hierarchical relations
    IS_A = auto()           # A is a B (subclass)
    PART_OF = auto()        # A is part of B
    HAS_PART = auto()       # A has part B (inverse of PART_OF)
    
    # Semantic relations
    RELATED_TO = auto()     # A is related to B
    SIMILAR_TO = auto()    # A is similar to B
    
    # Causal relations
    CAUSES = auto()        # A causes B
    PRECEDES = auto()      # A happens before B
    
    # User-related relations
    LIKES = auto()         # User likes something
    PREFERS = auto()       # User prefers something
    RATED = auto()         # User rated something (with a property for the rating)
    
    # Content relations
    MENTIONS = auto()      # Document mentions concept
    DESCRIBES = auto()     # Document describes concept
    
    # Custom relation type
    CUSTOM = auto()


class Relation:
    """Represents a directed relationship between two nodes in the knowledge graph."""
    
    def __init__(self, 
                 source: 'Node', 
                 target: 'Node', 
                 rel_type: RelationType,
                 properties: Optional[Dict[str, Any]] = None):
        """
        Initialize a knowledge graph relation.
        
        Args:
            source: Source node of the relation
            target: Target node of the relation
            rel_type: Type of the relation
            properties: Additional properties of the relation
        """
        self.id = str(uuid.uuid4())
        self.source = source
        self.target = target
        self.type = rel_type
        self.properties = properties or {}
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at
    
    def add_property(self, key: str, value: Any) -> None:
        """Add or update a property."""
        self.properties[key] = value
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the relation to a dictionary."""
        return {
            'id': self.id,
            'source_id': self.source.id,
            'target_id': self.target.id,
            'type': self.type.name,
            'properties': self.properties,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, 
                  data: Dict[str, Any], 
                  node_lookup: Dict[str, 'Node']) -> 'Relation':
        """
        Create a Relation from a dictionary.
        
        Args:
            data: Dictionary containing relation data
            node_lookup: Dictionary mapping node IDs to Node objects
            
        Returns:
            A new Relation instance
        """
        source = node_lookup.get(data['source_id'])
        target = node_lookup.get(data['target_id'])
        
        if not source or not target:
            raise ValueError("Could not find source or target node in node_lookup")
        
        rel = cls(
            source=source,
            target=target,
            rel_type=RelationType[data['type']],
            properties=data.get('properties', {})
        )
        rel.id = data['id']
        rel.created_at = datetime.fromisoformat(data['created_at'])
        rel.updated_at = datetime.fromisoformat(data['updated_at'])
        return rel
    
    def __repr__(self) -> str:
        return (f"<Relation(id='{self.id}', "
                f"source='{self.source.name}', "
                f"type={self.type.name}, "
                f"target='{self.target.name}')>")
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Relation):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
