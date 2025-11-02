"""
Knowledge Graph implementation for HSKG.
Manages nodes and relationships with hybrid semantic capabilities.
"""
from typing import Dict, List, Optional, Tuple, Any, Set
import numpy as np
from datetime import datetime
import networkx as nx
import json

from .node import Node, NodeType
from .relation import Relation, RelationType


class KnowledgeGraph:
    """
    A hybrid semantic knowledge graph that combines symbolic and vector representations.
    """
    
    def __init__(self, name: str = "HSKG"):
        """
        Initialize the knowledge graph.
        
        Args:
            name: Name of the knowledge graph
        """
        self.name = name
        self.nodes: Dict[str, Node] = {}
        self.relations: Dict[str, Relation] = {}
        self.node_name_index: Dict[str, List[Node]] = {}
        self.node_type_index: Dict[NodeType, List[Node]] = {}
        self.graph = nx.MultiDiGraph()
        
        # Initialize indices
        for node_type in NodeType:
            self.node_type_index[node_type] = []
    
    def add_node(self, node: Node) -> Node:
        """
        Add a node to the knowledge graph.
        
        Args:
            node: Node to add
            
        Returns:
            The added node (with updated ID if it was None)
        """
        # If node already exists, update it
        if node.id in self.nodes:
            return self.update_node(node)
        
        # Add to main storage
        self.nodes[node.id] = node
        
        # Update indices
        if node.name not in self.node_name_index:
            self.node_name_index[node.name] = []
        self.node_name_index[node.name].append(node)
        self.node_type_index[node.type].append(node)
        
        # Add to NetworkX graph
        self.graph.add_node(node.id, **node.to_dict())
        
        return node
    
    def update_node(self, node: Node) -> Node:
        """
        Update an existing node in the knowledge graph.
        
        Args:
            node: Node with updated properties
            
        Returns:
            The updated node
        """
        if node.id not in self.nodes:
            raise ValueError(f"Node with ID {node.id} does not exist")
        
        old_node = self.nodes[node.id]
        
        # Remove from indices
        self.node_name_index[old_node.name].remove(old_node)
        if not self.node_name_index[old_node.name]:
            del self.node_name_index[old_node.name]
        self.node_type_index[old_node.type].remove(old_node)
        
        # Update the node
        node.updated_at = datetime.utcnow()
        self.nodes[node.id] = node
        
        # Update indices
        if node.name not in self.node_name_index:
            self.node_name_index[node.name] = []
        self.node_name_index[node.name].append(node)
        self.node_type_index[node.type].append(node)
        
        # Update NetworkX graph
        self.graph.remove_node(node.id)
        self.graph.add_node(node.id, **node.to_dict())
        
        return node
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by its ID."""
        return self.nodes.get(node_id)
    
    def find_nodes(self, 
                  name: Optional[str] = None, 
                  node_type: Optional[NodeType] = None,
                  properties: Optional[Dict[str, Any]] = None) -> List[Node]:
        """
        Find nodes by name, type, and/or properties.
        
        Args:
            name: Node name (partial match)
            node_type: Node type
            properties: Dictionary of property key-value pairs to match
            
        Returns:
            List of matching nodes
        """
        # Start with all nodes
        if node_type is not None:
            candidates = list(self.node_type_index.get(node_type, []))
        else:
            candidates = list(self.nodes.values())
        
        # Filter by name if provided
        if name is not None:
            name = name.lower()
            candidates = [n for n in candidates if name in n.name.lower()]
        
        # Filter by properties if provided
        if properties:
            filtered = []
            for node in candidates:
                match = True
                for key, value in properties.items():
                    if key not in node.properties or node.properties[key] != value:
                        match = False
                        break
                if match:
                    filtered.append(node)
            candidates = filtered
        
        return candidates
    
    def add_relation(self, relation: Relation) -> Relation:
        """
        Add a relation to the knowledge graph.
        
        Args:
            relation: Relation to add
            
        Returns:
            The added relation (with updated ID if it was None)
        """
        # Ensure source and target nodes exist
        if relation.source.id not in self.nodes:
            raise ValueError(f"Source node {relation.source.id} does not exist")
        if relation.target.id not in self.nodes:
            raise ValueError(f"Target node {relation.target.id} does not exist")
        
        # If relation already exists, update it
        if relation.id in self.relations:
            return self.update_relation(relation)
        
        # Add to main storage
        self.relations[relation.id] = relation
        
        # Add to NetworkX graph
        self.graph.add_edge(
            relation.source.id,
            relation.target.id,
            key=relation.id,
            **relation.to_dict()
        )
        
        return relation
    
    def update_relation(self, relation: Relation) -> Relation:
        """
        Update an existing relation in the knowledge graph.
        
        Args:
            relation: Relation with updated properties
            
        Returns:
            The updated relation
        """
        if relation.id not in self.relations:
            raise ValueError(f"Relation with ID {relation.id} does not exist")
        
        # Update the relation
        relation.updated_at = datetime.utcnow()
        self.relations[relation.id] = relation
        
        # Update NetworkX graph
        self.graph.remove_edge(relation.source.id, relation.target.id, key=relation.id)
        self.graph.add_edge(
            relation.source.id,
            relation.target.id,
            key=relation.id,
            **relation.to_dict()
        )
        
        return relation
    
    def get_relation(self, relation_id: str) -> Optional[Relation]:
        """Get a relation by its ID."""
        return self.relations.get(relation_id)
    
    def find_relations(self, 
                      source_id: Optional[str] = None,
                      target_id: Optional[str] = None,
                      rel_type: Optional[RelationType] = None) -> List[Relation]:
        """
        Find relations by source, target, and/or type.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            rel_type: Type of relation
            
        Returns:
            List of matching relations
        """
        results = []
        
        for rel in self.relations.values():
            if source_id is not None and rel.source.id != source_id:
                continue
            if target_id is not None and rel.target.id != target_id:
                continue
            if rel_type is not None and rel.type != rel_type:
                continue
            results.append(rel)
        
        return results
    
    def get_neighbors(self, 
                     node_id: str, 
                     direction: str = 'both',
                     rel_types: Optional[List[RelationType]] = None) -> List[Tuple[Node, Relation, Node]]:
        """
        Get neighboring nodes and the relationships connecting them.
        
        Args:
            node_id: ID of the node to get neighbors for
            direction: 'in', 'out', or 'both'
            rel_types: Optional list of relation types to filter by
            
        Returns:
            List of (source, relation, target) tuples
        """
        if node_id not in self.nodes:
            return []
        
        neighbors = []
        
        if direction in ('in', 'both'):
            for rel in self.find_relations(target_id=node_id):
                if rel_types is None or rel.type in rel_types:
                    neighbors.append((rel.source, rel, self.nodes[node_id]))
        
        if direction in ('out', 'both'):
            for rel in self.find_relations(source_id=node_id):
                if rel_types is None or rel.type in rel_types:
                    neighbors.append((self.nodes[node_id], rel, rel.target))
        
        return neighbors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the knowledge graph to a dictionary."""
        return {
            'name': self.name,
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'relations': [rel.to_dict() for rel in self.relations.values()]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeGraph':
        """
        Create a KnowledgeGraph from a dictionary.
        
        Args:
            data: Dictionary containing nodes and relations
            
        Returns:
            A new KnowledgeGraph instance
        """
        kg = cls(name=data.get('name', 'HSKG'))
        
        # First, create all nodes
        node_lookup = {}
        for node_data in data.get('nodes', []):
            node = Node.from_dict(node_data)
            kg.add_node(node)
            node_lookup[node.id] = node
        
        # Then, create all relations
        for rel_data in data.get('relations', []):
            rel = Relation.from_dict(rel_data, node_lookup)
            kg.add_relation(rel)
        
        return kg
    
    def to_json(self, file_path: str) -> None:
        """Save the knowledge graph to a JSON file."""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def from_json(cls, file_path: str) -> 'KnowledgeGraph':
        """Load a knowledge graph from a JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def __repr__(self) -> str:
        return f"<KnowledgeGraph(name='{self.name}', nodes={len(self.nodes)}, relations={len(self.relations)})>"
