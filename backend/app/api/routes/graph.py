"""API routes for knowledge graph visualization."""

import json
from uuid import UUID
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
import pandas as pd

from app.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/graph", tags=["graph"])


def get_entity_color(entity_type: str) -> str:
    """Get color based on entity type."""
    colors = {
        "PERSON": "#48bb78",
        "ORGANIZATION": "#4299e1",
        "LOCATION": "#ed8936",
        "DATE": "#f56565",
        "MONEY": "#ecc94b",
        "LAW": "#9f7aea",
        "DOCUMENT": "#38b2ac",
        "CLAUSE": "#667eea",
        "OBLIGATION": "#ed64a6",
        "RIGHT": "#68d391",
        "TERM": "#fc8181",
        "CONDITION": "#f6ad55",
        "EVENT": "#4fd1c5",
        "CONCEPT": "#b794f4",
    }
    return colors.get(str(entity_type).upper(), "#a0aec0")


@router.get("/{conversation_id}/data")
async def get_graph_data(conversation_id: UUID):
    """Get knowledge graph data as JSON for a conversation."""
    
    artifacts_path = Path(settings.graphrag_data_dir) / str(conversation_id) / "output" 
    
    if not artifacts_path.exists():
        raise HTTPException(
            status_code=404, 
            detail="Knowledge graph not found. Please build the index first."
        )
    
    # Load entities
    entities_file = artifacts_path / "create_final_entities.parquet"
    if not entities_file.exists():
        raise HTTPException(status_code=404, detail="Entities file not found")
    
    entities_df = pd.read_parquet(entities_file)
    
    # Load relationships
    relationships_file = artifacts_path / "create_final_relationships.parquet"
    relationships_df = pd.DataFrame()
    if relationships_file.exists():
        relationships_df = pd.read_parquet(relationships_file)
    
    # Prepare nodes
    nodes = []
    entity_id_map = {}
    
    for idx, row in entities_df.iterrows():
        entity_id = str(row.get('id', idx))
        entity_name = str(row.get('name', row.get('title', f'Entity_{idx}')))
        entity_type = str(row.get('type', 'UNKNOWN'))
        entity_desc = str(row.get('description', ''))
        
        entity_id_map[entity_name.lower()] = entity_id
        
        nodes.append({
            "id": entity_id,
            "label": entity_name[:40],
            "fullName": entity_name,
            "type": entity_type,
            "description": entity_desc,
            "color": get_entity_color(entity_type),
        })
    
    # Prepare edges
    edges = []
    for idx, row in relationships_df.iterrows():
        source = str(row.get('source', '')).lower()
        target = str(row.get('target', '')).lower()
        rel_type = str(row.get('type', row.get('description', 'RELATED')))
        weight = row.get('weight', 1)
        
        source_id = entity_id_map.get(source)
        target_id = entity_id_map.get(target)
        
        if source_id and target_id:
            edges.append({
                "source": source_id,
                "target": target_id,
                "type": rel_type,
                "weight": float(weight) if weight else 1.0
            })
    
    # Get entity type counts
    type_counts = {}
    if 'type' in entities_df.columns:
        type_counts = entities_df['type'].value_counts().to_dict()
    
    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_entities": len(nodes),
            "total_relationships": len(edges),
            "entity_types": type_counts
        }
    }


@router.get("/{conversation_id}/summary")
async def get_graph_summary(conversation_id: UUID):
    """Get a text summary of the knowledge graph."""
    
    artifacts_path = Path(settings.graphrag_data_dir) / str(conversation_id) / "output" / "artifacts"
    
    if not artifacts_path.exists():
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    entities_file = artifacts_path / "create_final_entities.parquet"
    relationships_file = artifacts_path / "create_final_relationships.parquet"
    
    entities_df = pd.read_parquet(entities_file) if entities_file.exists() else pd.DataFrame()
    relationships_df = pd.read_parquet(relationships_file) if relationships_file.exists() else pd.DataFrame()
    
    summary = {
        "total_entities": len(entities_df),
        "total_relationships": len(relationships_df),
        "entity_types": {},
        "top_entities": [],
        "sample_relationships": []
    }
    
    if 'type' in entities_df.columns:
        summary["entity_types"] = entities_df['type'].value_counts().to_dict()
    
    if 'description' in entities_df.columns:
        entities_df['desc_len'] = entities_df['description'].str.len()
        top = entities_df.nlargest(10, 'desc_len')
        summary["top_entities"] = [
            {"name": row.get('name', row.get('title', '')), "type": row.get('type', 'UNKNOWN'), "description": str(row.get('description', ''))[:200]}
            for _, row in top.iterrows()
        ]
    
    if len(relationships_df) > 0:
        summary["sample_relationships"] = [
            {"source": row.get('source', ''), "target": row.get('target', ''), "type": row.get('type', row.get('description', 'RELATED'))}
            for _, row in relationships_df.head(15).iterrows()
        ]
    
    return summary
