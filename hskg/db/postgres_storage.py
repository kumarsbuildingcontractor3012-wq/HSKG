"""
PostgreSQL storage backend for HSKG knowledge graph.
"""
import json
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime
import logging

import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json
import numpy as np
from psycopg2.extensions import register_adapter, AsIs

from hskg.graph import KnowledgeGraph, Node, Relation, NodeType, RelationType
from .graph_storage import StorageBackend, StorageType

# Register NumPy array adapter for PostgreSQL
def adapt_numpy_array(arr):
    return AsIs("'".join(("[" + ",".join(map(str, arr)) + "]").split("'")))

register_adapter(np.ndarray, adapt_numpy_array)

class PostgresStorage(StorageBackend):
    """PostgreSQL storage backend for the knowledge graph."""
    
    def __init__(self, 
                 dbname: str, 
                 user: str, 
                 password: str, 
                 host: str = 'localhost', 
                 port: int = 5432):
        """
        Initialize the PostgreSQL storage backend.
        
        Args:
            dbname: Database name
            user: Database user
            password: Database password
            host: Database host
            port: Database port
        """
        self.connection_params = {
            'dbname': dbname,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }
        self._ensure_tables()
    
    def _get_connection(self):
        """Get a database connection."""
        return psycopg2.connect(**self.connection_params)
    
    def _ensure_tables(self):
        """Ensure that the required tables exist."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Create graphs table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS graphs (
                        id UUID PRIMARY KEY,
                        name TEXT NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        metadata JSONB
                    )
                """)
                
                # Create nodes table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS nodes (
                        id UUID PRIMARY KEY,
                        graph_id UUID REFERENCES graphs(id) ON DELETE CASCADE,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        properties JSONB,
                        labels TEXT[],
                        embedding VECTOR(384),  -- Adjust size based on your embedding dimension
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create relations table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS relations (
                        id UUID PRIMARY KEY,
                        graph_id UUID REFERENCES graphs(id) ON DELETE CASCADE,
                        source_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
                        target_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
                        type TEXT NOT NULL,
                        properties JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better query performance
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_nodes_graph_id ON nodes(graph_id);
                    CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
                    CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
                    CREATE INDEX IF NOT EXISTS idx_relations_graph_id ON relations(graph_id);
                    CREATE INDEX IF NOT EXISTS idx_relations_source_id ON relations(source_id);
                    CREATE INDEX IF NOT EXISTS idx_relations_target_id ON relations(target_id);
                    CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(type);
                """)
                
                conn.commit()
    
    def save_graph(self, graph: KnowledgeGraph, name: str = None) -> str:
        """Save a knowledge graph to the database."""
        graph_id = str(uuid.uuid4())
        graph_data = graph.to_dict()
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Save graph metadata
                cur.execute(
                    """
                    INSERT INTO graphs (id, name, metadata, updated_at)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        graph_id,
                        name or graph.name,
                        Json({'node_count': len(graph_data['nodes']), 
                              'relation_count': len(graph_data['relations'])}),
                        datetime.utcnow()
                    )
                )
                
                # Save nodes
                for node_data in graph_data['nodes']:
                    cur.execute(
                        """
                        INSERT INTO nodes (
                            id, graph_id, name, type, properties, labels, embedding, 
                            created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            node_data['id'],
                            graph_id,
                            node_data['name'],
                            node_data['type'],
                            Json(node_data.get('properties', {})),
                            node_data.get('labels', []),
                            None,  # Placeholder for embedding
                            node_data.get('created_at'),
                            node_data.get('updated_at')
                        )
                    )
                
                # Save relations
                for rel_data in graph_data['relations']:
                    cur.execute(
                        """
                        INSERT INTO relations (
                            id, graph_id, source_id, target_id, type, properties,
                            created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            str(uuid.uuid4()),
                            graph_id,
                            rel_data['source_id'],
                            rel_data['target_id'],
                            rel_data['type'],
                            Json(rel_data.get('properties', {})),
                            rel_data.get('created_at'),
                            rel_data.get('updated_at')
                        )
                    )
                
                conn.commit()
        
        return graph_id
    
    def load_graph(self, graph_id: str) -> KnowledgeGraph:
        """Load a knowledge graph from the database."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Load graph metadata
                cur.execute(
                    "SELECT name, metadata FROM graphs WHERE id = %s",
                    (graph_id,)
                )
                result = cur.fetchone()
                if not result:
                    raise ValueError(f"Graph with ID {graph_id} not found")
                
                name, metadata = result
                kg = KnowledgeGraph(name=name)
                
                # Load nodes
                cur.execute(
                    """
                    SELECT id, name, type, properties, labels, created_at, updated_at
                    FROM nodes
                    WHERE graph_id = %s
                    """,
                    (graph_id,)
                )
                
                for node_row in cur.fetchall():
                    node_id, name, node_type, props, labels, created_at, updated_at = node_row
                    node = Node(
                        node_type=NodeType[node_type],
                        name=name,
                        properties=props or {}
                    )
                    node.id = node_id
                    node.labels = labels or []
                    node.created_at = created_at
                    node.updated_at = updated_at
                    kg.add_node(node)
                
                # Load relations
                cur.execute(
                    """
                    SELECT source_id, target_id, type, properties, created_at, updated_at
                    FROM relations
                    WHERE graph_id = %s
                    """,
                    (graph_id,)
                )
                
                for rel_row in cur.fetchall():
                    source_id, target_id, rel_type, props, created_at, updated_at = rel_row
                    source_node = kg.get_node(source_id)
                    target_node = kg.get_node(target_id)
                    
                    if not source_node or not target_node:
                        logging.warning(
                            f"Could not find source or target node for relation "
                            f"{source_id} -> {target_id} (type: {rel_type})"
                        )
                        continue
                    
                    rel = Relation(
                        source=source_node,
                        target=target_node,
                        rel_type=RelationType[rel_type],
                        properties=props or {}
                    )
                    rel.created_at = created_at
                    rel.updated_at = updated_at
                    kg.add_relation(rel)
        
        return kg
    
    def delete_graph(self, graph_id: str) -> bool:
        """Delete a knowledge graph from the database."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # The ON DELETE CASCADE will handle nodes and relations
                cur.execute(
                    "DELETE FROM graphs WHERE id = %s RETURNING id",
                    (graph_id,)
                )
                deleted = cur.fetchone() is not None
                conn.commit()
                return deleted
    
    def list_graphs(self) -> List[Dict[str, Any]]:
        """List all stored knowledge graphs."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, created_at, updated_at, metadata
                    FROM graphs
                    ORDER BY created_at DESC
                    """
                )
                
                graphs = []
                for row in cur.fetchall():
                    graph_id, name, created_at, updated_at, metadata = row
                    graphs.append({
                        'id': graph_id,
                        'name': name,
                        'created_at': created_at.isoformat(),
                        'updated_at': updated_at.isoformat(),
                        'metadata': metadata or {}
                    })
                
                return graphs
    
    def close(self):
        """Close any open connections."""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def __del__(self):
        self.close()
