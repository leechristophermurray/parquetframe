"""
Test fixtures for creating minimal GraphAr format graph samples.

This module provides utilities to create small, well-formed GraphAr directories
for testing graph functionality without requiring external data files.
"""

from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def build_minimal_graphar(tmp_path: Path) -> dict[str, Any]:
    """
    Build a minimal GraphAr format graph directory for testing.

    Creates a simple directed graph with:
    - 4 vertices (people) with id and name properties
    - 5 edges (friendship connections) with src, dst, and weight properties
    - Proper GraphAr metadata and schema files

    Args:
        tmp_path: Pytest temporary directory path

    Returns:
        Dictionary containing:
        - graph_path: Path to the created GraphAr directory
        - expected_vertices: Number of vertices (4)
        - expected_edges: Number of edges (5)
        - metadata: The graph metadata dictionary
        - vertex_data: The vertex DataFrame
        - edge_data: The edge DataFrame

    Example:
        >>> import pytest
        >>> def test_graphar_loading(tmp_path):
        ...     sample = build_minimal_graphar(tmp_path)
        ...     graph = read_graph(sample["graph_path"])
        ...     assert graph.num_vertices == sample["expected_vertices"]
    """
    graph_dir = tmp_path / "minimal_graph"
    graph_dir.mkdir()

    # Create vertex data - 4 people
    vertex_data = pd.DataFrame(
        {
            "id": [0, 1, 2, 3],
            "name": ["Alice", "Bob", "Charlie", "Diana"],
            "age": [25, 30, 35, 28],
        }
    )

    # Create edge data - friendship network
    edge_data = pd.DataFrame(
        {
            "src": [0, 0, 1, 2, 3],
            "dst": [1, 2, 2, 3, 0],
            "weight": [0.8, 0.6, 0.9, 0.7, 0.5],
        }
    )

    # Create vertices directory structure
    vertices_dir = graph_dir / "vertices" / "person"
    vertices_dir.mkdir(parents=True)

    # Write vertex parquet file
    vertex_data.to_parquet(
        vertices_dir / "part0.parquet", engine="pyarrow", index=False
    )

    # Create edges directory structure
    edges_dir = graph_dir / "edges" / "knows"
    edges_dir.mkdir(parents=True)

    # Write edge parquet file
    edge_data.to_parquet(edges_dir / "part0.parquet", engine="pyarrow", index=False)

    # Create metadata file
    metadata = {
        "name": "minimal_test_graph",
        "version": "1.0",
        "directed": True,
        "description": "A minimal test graph for unit tests",
    }

    with open(graph_dir / "_metadata.yaml", "w", encoding="utf-8") as f:
        yaml.dump(metadata, f, default_flow_style=False)

    # Create schema file
    schema = {
        "version": "1.0",
        "vertices": {
            "person": {
                "properties": {
                    "id": {"type": "int64", "primary": True},
                    "name": {"type": "string"},
                    "age": {"type": "int32"},
                }
            }
        },
        "edges": {
            "knows": {
                "properties": {
                    "src": {"type": "int64", "source": True},
                    "dst": {"type": "int64", "target": True},
                    "weight": {"type": "float64"},
                }
            }
        },
    }

    with open(graph_dir / "_schema.yaml", "w", encoding="utf-8") as f:
        yaml.dump(schema, f, default_flow_style=False)

    return {
        "graph_path": graph_dir,
        "expected_vertices": 4,
        "expected_edges": 5,
        "metadata": metadata,
        "schema": schema,
        "vertex_data": vertex_data,
        "edge_data": edge_data,
    }


def build_empty_graphar(tmp_path: Path) -> dict[str, Any]:
    """
    Build an empty GraphAr directory (no vertices or edges) for testing.

    Args:
        tmp_path: Pytest temporary directory path

    Returns:
        Dictionary with graph_path and metadata
    """
    graph_dir = tmp_path / "empty_graph"
    graph_dir.mkdir()

    # Create metadata for empty graph
    metadata = {
        "name": "empty_test_graph",
        "version": "1.0",
        "directed": True,
        "description": "An empty graph for testing edge cases",
    }

    with open(graph_dir / "_metadata.yaml", "w", encoding="utf-8") as f:
        yaml.dump(metadata, f, default_flow_style=False)

    return {
        "graph_path": graph_dir,
        "expected_vertices": 0,
        "expected_edges": 0,
        "metadata": metadata,
    }


def build_invalid_graphar(tmp_path: Path, error_type: str = "missing_metadata") -> Path:
    """
    Build an invalid GraphAr directory for testing error handling.

    Args:
        tmp_path: Pytest temporary directory path
        error_type: Type of error to create:
            - "missing_metadata": No _metadata.yaml file
            - "invalid_yaml": Malformed YAML in metadata
            - "missing_required_fields": Metadata missing required fields
            - "wrong_field_types": Metadata fields have wrong types

    Returns:
        Path to the invalid GraphAr directory
    """
    graph_dir = tmp_path / f"invalid_graph_{error_type}"
    graph_dir.mkdir()

    if error_type == "missing_metadata":
        # Don't create metadata file
        pass

    elif error_type == "invalid_yaml":
        # Create malformed YAML file
        with open(graph_dir / "_metadata.yaml", "w", encoding="utf-8") as f:
            f.write("name: test\nversion: {\ninvalid yaml")

    elif error_type == "missing_required_fields":
        # Create metadata missing required fields
        metadata = {"name": "test"}  # Missing version and directed
        with open(graph_dir / "_metadata.yaml", "w", encoding="utf-8") as f:
            yaml.dump(metadata, f)

    elif error_type == "wrong_field_types":
        # Create metadata with wrong field types
        metadata = {
            "name": 123,  # Should be string
            "version": "1.0",
            "directed": "true",  # Should be boolean
        }
        with open(graph_dir / "_metadata.yaml", "w", encoding="utf-8") as f:
            yaml.dump(metadata, f)

    else:
        raise ValueError(f"Unknown error_type: {error_type}")

    return graph_dir


def build_large_graphar(tmp_path: Path, num_vertices: int = 1000) -> dict[str, Any]:
    """
    Build a larger GraphAr directory for testing backend selection.

    Args:
        tmp_path: Pytest temporary directory path
        num_vertices: Number of vertices to create

    Returns:
        Dictionary with graph info and expected backend
    """
    graph_dir = tmp_path / "large_graph"
    graph_dir.mkdir()

    # Create larger vertex data
    vertex_data = pd.DataFrame(
        {
            "id": range(num_vertices),
            "name": [f"user_{i}" for i in range(num_vertices)],
            "category": [f"category_{i % 10}" for i in range(num_vertices)],
        }
    )

    # Create edge data - each vertex connects to next 3 vertices (circular)
    edge_sources = []
    edge_targets = []
    edge_weights = []

    for i in range(num_vertices):
        for j in range(3):  # 3 outgoing edges per vertex
            target = (i + j + 1) % num_vertices
            edge_sources.append(i)
            edge_targets.append(target)
            edge_weights.append(0.5 + (i + j) % 100 / 200.0)  # Weight between 0.5-1.0

    edge_data = pd.DataFrame(
        {"src": edge_sources, "dst": edge_targets, "weight": edge_weights}
    )

    # Create directory structure and save data
    vertices_dir = graph_dir / "vertices" / "user"
    vertices_dir.mkdir(parents=True)
    vertex_data.to_parquet(
        vertices_dir / "part0.parquet", engine="pyarrow", index=False
    )

    edges_dir = graph_dir / "edges" / "connection"
    edges_dir.mkdir(parents=True)
    edge_data.to_parquet(edges_dir / "part0.parquet", engine="pyarrow", index=False)

    # Create metadata
    metadata = {
        "name": f"large_test_graph_{num_vertices}",
        "version": "1.0",
        "directed": True,
        "description": f"A large test graph with {num_vertices} vertices",
    }

    with open(graph_dir / "_metadata.yaml", "w", encoding="utf-8") as f:
        yaml.dump(metadata, f, default_flow_style=False)

    return {
        "graph_path": graph_dir,
        "expected_vertices": num_vertices,
        "expected_edges": len(edge_data),
        "metadata": metadata,
        "vertex_data": vertex_data,
        "edge_data": edge_data,
        "expected_backend": (
            "dask" if num_vertices >= 500 else "pandas"
        ),  # Threshold guess
    }
