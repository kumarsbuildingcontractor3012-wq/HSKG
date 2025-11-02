"""
In-memory storage backend for HSKG knowledge graph.
"""
import json
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime

from hskg.graph import KnowledgeGraph, Node, Relation, NodeType, RelationType
from .graph_storage import StorageBackend, StorageType

class InMemoryStorage(StorageBackend):
    """
    In-memory storage backend for the knowledge graph.
    
    This is useful for testing and development, but not suitable for production
    as it doesn't persist data between application restarts.
    """
    
    def __init__(self):
        """Initialize the in-memory storage."""
        self.graphs: Dict[str, Dict[str, Any]] = {}
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.relations: Dict[str, Dict[str, Any]] = {}
    
    def save_graph(self, graph: KnowledgeGraph, name: str = None) -> str:
        """Save a knowledge graph to memory."""
        graph_id = str(uuid.uuid4())
        graph_data = graph.to_dict()
        
        # Store graph metadata
        self.graphs[graph_id] = {
            'id': graph_id,
            'name': name or graph.name,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'metadata': {
                'node_count': len(graph_data['nodes']),
                'relation_count': len(graph_data['relations'])
            }
        }
        
        # Store nodes
        for node_data in graph_data['nodes']:
            node_id = node_data['id']
            self.nodes[node_id] = {
                **node_data,
                'graph_id': graph_id
            }
        
        # Store relations
        for rel_data in graph_data['relations']:
            rel_id = str(uuid.uuid4())
            self.relations[rel_id] = {
                **rel_data,
                'id': rel_id,
                'graph_id': graph_id
            }
        
        return graph_id
    
    def load_graph(self, graph_id: str) -> KnowledgeGraph:
        """Load a knowledge graph from memory."""
        if graph_id not in self.graphs:
            raise ValueError(f"Graph with ID {graph_id} not found")
        
        graph_info = self.graphs[graph_id]
        kg = KnowledgeGraph(name=graph_info['name'])
        
        # Load nodes
        node_lookup = {}
        for node_id, node_data in self.nodes.items():
            if node_data['graph_id'] == graph_id:
                node = Node(
                    node_type=NodeType[node_data['type']],
                    name=node_data['name'],
                    properties=node_data.get('properties', {})
                )
                node.id = node_data['id']
                node.labels = node_data.get('labels', [])
                node.created_at = datetime.fromisoformat(node_data['created_at'])
                node.updated_at = datetime.fromisoformat(node_data['updated_at'])
                kg.add_node(node)
                node_lookup[node_id] = node
        
        # Load relations
        for rel_data in self.relations.values():
            if rel_data['graph_id'] == graph_id:
                source_id = rel_data['source_id']
                target_id = rel_data['target_id']
                
                source_node = node_lookup.get(source_id)
                target_node = node_lookup.get(target_id)
                
                if not source_node or not target_node:
                    continue
                
                rel = Relation(
                    source=source_node,
                    target=target_node,
                    rel_type=RelationType[rel_data['type']],
                    properties=rel_data.get('properties', {})
                )
                rel.id = rel_data['id']
                rel.created_at = datetime.fromisoformat(rel_data['created_at'])
                rel.updated_at = datetime.fromisoformat(rel_data['updated_at'])
                kg.add_relation(rel)
        
        return kg
    
    def delete_graph(self, graph_id: str) -> bool:
        """Delete a knowledge graph from memory."""
        if graph_id not in self.graphs:
            return False
        
        # Remove graph metadata
        del self.graphs[graph_id]
        
        # Remove nodes
        nodes_to_remove = [
            node_id for node_id, node_data in self.nodes.items()
            if node_data.get('graph_id') == graph_id
        ]
        for node_id in nodes_to_remove:
            del self.nodes[node_id]
        
        # Remove relations
        rels_to_remove = [
            rel_id for rel_id, rel_data in self.relations.items()
            if rel_data.get('graph_id') == graph_id
        ]
        for rel_id in rels_to_remove:
            del self.relations[rel_id]
        
        return True
    
    def list_graphs(self) -> List[Dict[str, Any]]:
        """List all stored knowledge graphs."""
        return [
            {
                'id': graph_id,
                'name': graph_data['name'],
                'created_at': graph_data['created_at'],
                'updated_at': graph_data['updated_at'],
                'metadata': graph_data.get('metadata', {})
            }
            for graph_id, graph_data in self.graphs.items()
        ]
    
    def clear(self):
        """Clear all stored data."""
        self.graphs.clear()
        self.nodes.clear()
        self.relations.clear()
