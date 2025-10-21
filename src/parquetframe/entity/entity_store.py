"""
Entity storage and persistence.

Handles reading and writing entities using DataFrameProxy.
"""

from dataclasses import asdict
from typing import Any

import pandas as pd
import yaml

from ..core.reader import read_avro, read_parquet


class EntityStore:
    """Storage manager for entity persistence."""

    def __init__(self, metadata):
        """
        Initialize entity store.

        Args:
            metadata: EntityMetadata instance
        """
        self.metadata = metadata
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        """Ensure storage directory exists."""
        self.metadata.storage_path.mkdir(parents=True, exist_ok=True)

    def _load_dataframe(self) -> pd.DataFrame:
        """Load entity data as pandas DataFrame."""
        storage_file = self.metadata.storage_file

        if not storage_file.exists():
            # Return empty DataFrame with correct schema
            return pd.DataFrame(columns=list(self.metadata.fields.keys()))

        # Read using Phase 2 reader
        if self.metadata.format == "parquet":
            proxy = read_parquet(storage_file, engine="pandas")
        elif self.metadata.format == "avro":
            proxy = read_avro(storage_file, engine="pandas")
        else:
            raise ValueError(f"Unsupported format: {self.metadata.format}")

        # Return native pandas DataFrame
        return proxy.native

    def _save_dataframe(self, df: pd.DataFrame) -> None:
        """Save DataFrame to storage."""
        storage_file = self.metadata.storage_file

        if self.metadata.format == "parquet":
            df.to_parquet(storage_file, index=False)
        elif self.metadata.format == "avro":
            # Use Avro writer if available
            try:
                from ..io_new.avro import AvroWriter

                writer = AvroWriter()
                writer.write(df, storage_file)
            except ImportError as e:
                raise ImportError("fastavro required for Avro format") from e
        else:
            raise ValueError(f"Unsupported format: {self.metadata.format}")

        # Generate GraphAr metadata files
        self._write_graphar_metadata(df)

    def _write_graphar_metadata(self, df: pd.DataFrame) -> None:
        """Write GraphAr-compliant metadata files."""
        storage_path = self.metadata.storage_path

        # Generate _metadata.yaml
        metadata_content = {
            "name": self.metadata.name,
            "version": "0.1.0",
            "format": "graphar",
            "vertices": [
                {
                    "label": self.metadata.name,
                    "prefix": f"vertices/{self.metadata.name}/",
                    "count": len(df),
                }
            ],
            "edges": [],  # Entities don't have edges by default
        }

        metadata_file = storage_path / "_metadata.yaml"
        with open(metadata_file, "w") as f:
            yaml.dump(metadata_content, f, default_flow_style=False, sort_keys=False)

        # Generate _schema.yaml
        schema_content = self._generate_schema(df)
        schema_file = storage_path / "_schema.yaml"
        with open(schema_file, "w") as f:
            yaml.dump(schema_content, f, default_flow_style=False, sort_keys=False)

    def _generate_schema(self, df: pd.DataFrame) -> dict:
        """Generate GraphAr schema from DataFrame."""
        # Map pandas dtypes to GraphAr types
        type_mapping = {
            "int64": "int64",
            "int32": "int32",
            "float64": "double",
            "float32": "float",
            "object": "string",
            "bool": "bool",
            "datetime64[ns]": "timestamp",
        }

        properties = []
        for col_name, dtype in df.dtypes.items():
            dtype_str = str(dtype)
            graphar_type = type_mapping.get(dtype_str, "string")
            properties.append(
                {
                    "name": col_name,
                    "type": graphar_type,
                    "nullable": bool(df[col_name].isnull().any()),
                }
            )

        schema = {
            "vertices": [
                {
                    "label": self.metadata.name,
                    "properties": properties,
                    "primary_key": self.metadata.primary_key,
                }
            ],
            "edges": [],
        }

        return schema

    def save(self, instance: Any) -> None:
        """
        Save an entity instance.

        Args:
            instance: Entity instance to save
        """
        # Convert instance to dict
        data = asdict(instance)

        # Load existing data
        df = self._load_dataframe()

        # Check if entity already exists (update vs insert)
        pk_value = data[self.metadata.primary_key]
        pk_col = self.metadata.primary_key

        if len(df) > 0 and pk_col in df.columns:
            # Update existing or append new
            mask = df[pk_col] == pk_value
            if mask.any():
                # Update existing row
                for col, value in data.items():
                    df.loc[mask, col] = value
            else:
                # Append new row
                df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        else:
            # First record
            df = pd.DataFrame([data])

        # Save back to storage
        self._save_dataframe(df)

    def delete(self, pk_value: Any) -> None:
        """
        Delete an entity by primary key.

        Args:
            pk_value: Primary key value
        """
        df = self._load_dataframe()

        if len(df) == 0:
            return

        # Filter out the entity
        pk_col = self.metadata.primary_key
        df = df[df[pk_col] != pk_value]

        # Save back
        self._save_dataframe(df)

    def find(self, pk_value: Any) -> Any | None:
        """
        Find entity by primary key.

        Args:
            pk_value: Primary key value

        Returns:
            Entity instance or None
        """
        df = self._load_dataframe()

        if len(df) == 0:
            return None

        # Filter by primary key
        pk_col = self.metadata.primary_key
        result_df = df[df[pk_col] == pk_value]

        if len(result_df) == 0:
            return None

        # Convert first row to entity instance
        row_dict = result_df.iloc[0].to_dict()
        return self.metadata.cls(**row_dict)

    def find_all(self) -> list[Any]:
        """
        Find all entities.

        Returns:
            List of entity instances
        """
        df = self._load_dataframe()

        if len(df) == 0:
            return []

        # Convert all rows to entity instances
        instances = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            instances.append(self.metadata.cls(**row_dict))

        return instances

    def find_by(self, **filters: Any) -> list[Any]:
        """
        Find entities matching filters.

        Args:
            **filters: Column name and value pairs

        Returns:
            List of matching entity instances
        """
        df = self._load_dataframe()

        if len(df) == 0:
            return []

        # Apply filters
        mask = pd.Series([True] * len(df))
        for col, value in filters.items():
            if col in df.columns:
                mask &= df[col] == value

        result_df = df[mask]

        # Convert to entity instances
        instances = []
        for _, row in result_df.iterrows():
            row_dict = row.to_dict()
            instances.append(self.metadata.cls(**row_dict))

        return instances

    def count(self) -> int:
        """
        Count total entities.

        Returns:
            Number of entities
        """
        df = self._load_dataframe()
        return len(df)

    def delete_all(self) -> None:
        """Delete all entities."""
        storage_file = self.metadata.storage_file

        if storage_file.exists():
            storage_file.unlink()
