"""
Apache GraphAr format reader implementation.

GraphAr is a standardized columnar format for graph data that organizes
vertices and edges in Parquet files with accompanying metadata and schema files.

This module provides functionality to read GraphAr directories and validate
their structure according to the GraphAr specification.

References:
    - Apache GraphAr specification: https://graphar.apache.org/
    - GraphAr GitHub: https://github.com/apache/incubator-graphar
"""

import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from ...core import ParquetFrame
from ...exceptions import ParquetFrameError

if TYPE_CHECKING:
    from .. import GraphFrame


class GraphArError(ParquetFrameError):
    """Exception raised for GraphAr format errors."""

    pass


class GraphArValidationError(GraphArError):
    """Exception raised for GraphAr schema validation errors."""

    pass


class GraphArReader:
    """
    Reader for Apache GraphAr format graph data.

    GraphAr organizes graph data in a standardized directory structure:

    ```
    graph_directory/
    ├── _metadata.yaml      # Graph-level metadata
    ├── _schema.yaml        # Schema definitions
    ├── vertices/           # Vertex data directory
    │   ├── vertex_type1/   # Vertex type subdirectories
    │   │   └── *.parquet   # Vertex property files
    │   └── vertex_type2/
    │       └── *.parquet
    └── edges/              # Edge data directory
        ├── edge_type1/     # Edge type subdirectories
        │   └── *.parquet   # Edge property files
        └── edge_type2/
            └── *.parquet
    ```

    The reader validates the directory structure, parses metadata and schema
    files, and loads vertex/edge data using ParquetFrame's backend selection.

    Examples:
        Basic usage:
            >>> reader = GraphArReader()
            >>> graph = reader.read("social_network/")
            >>> print(f"Loaded graph: {graph.num_vertices} vertices")

        With validation disabled for performance:
            >>> graph = reader.read("large_graph/", validate_schema=False)

        Force Dask backend for large graphs:
            >>> graph = reader.read("web_graph/", islazy=True)
    """

    def __init__(self):
        """Initialize GraphAr reader."""
        self._metadata_cache = {}
        self._schema_cache = {}

    def read(
        self,
        path: str | Path,
        *,
        threshold_mb: float | None = None,
        islazy: bool | None = None,
        validate_schema: bool = True,
        load_adjacency: bool = False,
    ) -> "GraphFrame":
        """
        Read a GraphAr format graph from directory.

        Args:
            path: Path to GraphAr directory
            threshold_mb: Size threshold for backend selection (pandas vs Dask)
            islazy: Force backend (True=Dask, False=pandas, None=auto)
            validate_schema: Whether to validate GraphAr schema compliance
            load_adjacency: Whether to preload adjacency structures

        Returns:
            GraphFrame containing the loaded graph data

        Raises:
            GraphArError: If GraphAr directory structure is invalid
            GraphArValidationError: If schema validation fails
            FileNotFoundError: If required files are missing
        """
        graph_dir = Path(path)

        # Validate directory exists and is a directory
        if not graph_dir.exists():
            raise FileNotFoundError(f"GraphAr directory not found: {graph_dir}")

        if not graph_dir.is_dir():
            raise GraphArError(f"Path is not a directory: {graph_dir}")

        # Load and validate metadata
        metadata = self._load_metadata(graph_dir)

        # Load and validate schema if requested
        schema = None
        if validate_schema:
            schema = self._load_schema(graph_dir)
            self._validate_schema_compatibility(metadata, schema)

        # Load vertex and edge data
        vertices = self._load_vertices(
            graph_dir, metadata, schema, threshold_mb, islazy
        )
        edges = self._load_edges(graph_dir, metadata, schema, threshold_mb, islazy)

        # Import here to avoid circular imports
        from .. import GraphFrame

        return GraphFrame(
            vertices=vertices,
            edges=edges,
            metadata=metadata,
            adjacency_data={} if not load_adjacency else None,  # TODO: Implement
        )

    def _load_metadata(self, graph_dir: Path) -> dict[str, Any]:
        """
        Load and validate graph metadata from _metadata.yaml.

        Args:
            graph_dir: Path to GraphAr directory

        Returns:
            Parsed metadata dictionary

        Raises:
            GraphArError: If metadata file is missing or invalid
        """
        metadata_path = graph_dir / "_metadata.yaml"

        if not metadata_path.exists():
            raise GraphArError(f"Required metadata file not found: {metadata_path}")

        try:
            with open(metadata_path, encoding="utf-8") as f:
                metadata = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise GraphArError(f"Invalid YAML in metadata file: {e}") from e
        except Exception as e:
            raise GraphArError(f"Failed to read metadata file: {e}") from e

        if not isinstance(metadata, dict):
            raise GraphArError("Metadata file must contain a YAML dictionary")

        # Validate required metadata fields
        required_fields = ["name", "version", "directed"]
        missing_fields = [field for field in required_fields if field not in metadata]
        if missing_fields:
            raise GraphArError(f"Missing required metadata fields: {missing_fields}")

        # Validate field types
        if not isinstance(metadata["name"], str):
            raise GraphArError("Metadata field 'name' must be a string")
        if not isinstance(metadata["version"], str | int | float):
            raise GraphArError("Metadata field 'version' must be a string or number")
        if not isinstance(metadata["directed"], bool):
            raise GraphArError("Metadata field 'directed' must be a boolean")

        return metadata

    def _load_schema(self, graph_dir: Path) -> dict[str, Any]:
        """
        Load and validate graph schema from _schema.yaml.

        Args:
            graph_dir: Path to GraphAr directory

        Returns:
            Parsed schema dictionary

        Raises:
            GraphArValidationError: If schema file is missing or invalid
        """
        schema_path = graph_dir / "_schema.yaml"

        if not schema_path.exists():
            raise GraphArValidationError(
                f"Schema file required for validation: {schema_path}"
            )

        try:
            with open(schema_path, encoding="utf-8") as f:
                schema = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise GraphArValidationError(f"Invalid YAML in schema file: {e}") from e
        except Exception as e:
            raise GraphArValidationError(f"Failed to read schema file: {e}") from e

        if not isinstance(schema, dict):
            raise GraphArValidationError("Schema file must contain a YAML dictionary")

        # Validate schema structure
        required_sections = ["vertices", "edges"]
        for section in required_sections:
            if section not in schema:
                raise GraphArValidationError(
                    f"Missing required schema section: {section}"
                )
            if not isinstance(schema[section], dict):
                raise GraphArValidationError(
                    f"Schema section '{section}' must be a dictionary"
                )

        return schema

    def _validate_schema_compatibility(
        self, metadata: dict[str, Any], schema: dict[str, Any]
    ) -> None:
        """
        Validate compatibility between metadata and schema.

        Args:
            metadata: Loaded graph metadata
            schema: Loaded graph schema

        Raises:
            GraphArValidationError: If metadata and schema are incompatible
        """
        # Check GraphAr version compatibility
        metadata_version = str(metadata.get("version", "unknown"))
        schema_version = str(schema.get("version", "unknown"))

        if metadata_version != schema_version and schema_version != "unknown":
            warnings.warn(
                f"Version mismatch: metadata={metadata_version}, schema={schema_version}",
                UserWarning,
                stacklevel=3,
            )

        # Additional validation could be added here for:
        # - Vertex type consistency
        # - Edge type consistency
        # - Property type validation
        # - etc.

    def _load_vertices(
        self,
        graph_dir: Path,
        metadata: dict[str, Any],
        schema: dict[str, Any] | None,
        threshold_mb: float | None,
        islazy: bool | None,
    ) -> ParquetFrame:
        """
        Load vertex data from GraphAr directory structure.

        Args:
            graph_dir: Path to GraphAr directory
            metadata: Graph metadata
            schema: Graph schema (if validation enabled)
            threshold_mb: Size threshold for backend selection
            islazy: Force backend selection

        Returns:
            ParquetFrame containing vertex data

        Raises:
            GraphArError: If vertex data cannot be loaded
        """
        vertices_dir = graph_dir / "vertices"

        if not vertices_dir.exists():
            # Create empty vertex data if no vertices directory
            import pandas as pd

            empty_df = pd.DataFrame({"vertex_id": pd.Series([], dtype="int64")})
            return ParquetFrame(data=empty_df, islazy=islazy or False)

        if not vertices_dir.is_dir():
            raise GraphArError(f"Vertices path is not a directory: {vertices_dir}")

        # Find all parquet files in vertex subdirectories
        vertex_files = list(vertices_dir.rglob("*.parquet"))

        if not vertex_files:
            # Create empty vertex data if no parquet files found
            import pandas as pd

            empty_df = pd.DataFrame({"vertex_id": pd.Series([], dtype="int64")})
            return ParquetFrame(data=empty_df, islazy=islazy or False)

        # For now, load the first parquet file found
        # TODO: Implement proper multi-type vertex loading
        vertex_file = vertex_files[0]

        try:
            vertices = ParquetFrame.read(
                vertex_file, threshold_mb=threshold_mb, islazy=islazy
            )
            return vertices
        except Exception as e:
            raise GraphArError(
                f"Failed to load vertex data from {vertex_file}: {e}"
            ) from e

    def _load_edges(
        self,
        graph_dir: Path,
        metadata: dict[str, Any],
        schema: dict[str, Any] | None,
        threshold_mb: float | None,
        islazy: bool | None,
    ) -> ParquetFrame:
        """
        Load edge data from GraphAr directory structure.

        Args:
            graph_dir: Path to GraphAr directory
            metadata: Graph metadata
            schema: Graph schema (if validation enabled)
            threshold_mb: Size threshold for backend selection
            islazy: Force backend selection

        Returns:
            ParquetFrame containing edge data

        Raises:
            GraphArError: If edge data cannot be loaded
        """
        edges_dir = graph_dir / "edges"

        if not edges_dir.exists():
            # Create empty edge data if no edges directory
            import pandas as pd

            empty_df = pd.DataFrame(
                {
                    "src": pd.Series([], dtype="int64"),
                    "dst": pd.Series([], dtype="int64"),
                }
            )
            return ParquetFrame(data=empty_df, islazy=islazy or False)

        if not edges_dir.is_dir():
            raise GraphArError(f"Edges path is not a directory: {edges_dir}")

        # Find all parquet files in edge subdirectories
        edge_files = list(edges_dir.rglob("*.parquet"))

        if not edge_files:
            # Create empty edge data if no parquet files found
            import pandas as pd

            empty_df = pd.DataFrame(
                {
                    "src": pd.Series([], dtype="int64"),
                    "dst": pd.Series([], dtype="int64"),
                }
            )
            return ParquetFrame(data=empty_df, islazy=islazy or False)

        # For now, load the first parquet file found
        # TODO: Implement proper multi-type edge loading
        edge_file = edge_files[0]

        try:
            edges = ParquetFrame.read(
                edge_file, threshold_mb=threshold_mb, islazy=islazy
            )
            return edges
        except Exception as e:
            raise GraphArError(f"Failed to load edge data from {edge_file}: {e}") from e

    def validate_directory(self, path: str | Path) -> bool:
        """
        Check if a directory contains valid GraphAr structure.

        Args:
            path: Path to directory to validate

        Returns:
            True if directory appears to be a valid GraphAr directory

        Examples:
            >>> reader = GraphArReader()
            >>> if reader.validate_directory("my_graph/"):
            ...     graph = reader.read("my_graph/")
        """
        try:
            graph_dir = Path(path)
            if not graph_dir.is_dir():
                return False

            # Check for required metadata file
            if not (graph_dir / "_metadata.yaml").exists():
                return False

            # Check for vertices or edges directory (at least one required)
            has_vertices = (graph_dir / "vertices").is_dir()
            has_edges = (graph_dir / "edges").is_dir()

            return has_vertices or has_edges

        except Exception:
            return False

    def list_vertex_types(self, path: str | Path) -> list[str]:
        """
        List available vertex types in a GraphAr directory.

        Args:
            path: Path to GraphAr directory

        Returns:
            List of vertex type names

        Examples:
            >>> reader = GraphArReader()
            >>> types = reader.list_vertex_types("social_network/")
            >>> print(types)  # ['users', 'pages', 'groups']
        """
        graph_dir = Path(path)
        vertices_dir = graph_dir / "vertices"

        if not vertices_dir.exists() or not vertices_dir.is_dir():
            return []

        # Return subdirectory names as vertex types
        return [subdir.name for subdir in vertices_dir.iterdir() if subdir.is_dir()]

    def list_edge_types(self, path: str | Path) -> list[str]:
        """
        List available edge types in a GraphAr directory.

        Args:
            path: Path to GraphAr directory

        Returns:
            List of edge type names

        Examples:
            >>> reader = GraphArReader()
            >>> types = reader.list_edge_types("social_network/")
            >>> print(types)  # ['follows', 'likes', 'friends']
        """
        graph_dir = Path(path)
        edges_dir = graph_dir / "edges"

        if not edges_dir.exists() or not edges_dir.is_dir():
            return []

        # Return subdirectory names as edge types
        return [subdir.name for subdir in edges_dir.iterdir() if subdir.is_dir()]
