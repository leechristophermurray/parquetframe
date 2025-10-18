"""
Tests for Apache Avro integration with Phase 2.

Tests cover:
- Reading Avro files with multi-engine support
- Writing Avro files from different engines
- Schema inference
- Timestamp handling
- Compression codecs
"""

import pandas as pd
import pytest

try:
    import fastavro  # noqa: F401

    FASTAVRO_AVAILABLE = True
except ImportError:
    FASTAVRO_AVAILABLE = False

from parquetframe.core_v2 import DataFrameProxy, read_avro

# Skip all tests if fastavro not available
pytestmark = pytest.mark.skipif(not FASTAVRO_AVAILABLE, reason="fastavro not available")


@pytest.fixture
def sample_df():
    """Create sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "age": [25, 30, 35, 40, 45],
            "score": [85.5, 92.3, 78.1, 88.9, 95.0],
            "active": [True, True, False, True, False],
        }
    )


@pytest.fixture
def sample_avro_file(sample_df, tmp_path):
    """Create sample Avro file for testing."""
    from parquetframe.io_new.avro import AvroWriter

    file_path = tmp_path / "sample.avro"
    writer = AvroWriter()
    writer.write(sample_df, file_path)
    return file_path


class TestAvroReading:
    """Test reading Avro files."""

    def test_read_avro_pandas(self, sample_avro_file):
        """Test reading Avro file with pandas engine."""
        proxy = read_avro(sample_avro_file, engine="pandas")

        assert isinstance(proxy, DataFrameProxy)
        assert proxy.engine_name == "pandas"
        assert len(proxy) == 5
        assert list(proxy.columns) == ["id", "name", "age", "score", "active"]

    @pytest.mark.skipif(
        not pytest.importorskip("polars", reason="Polars not available"),
        reason="Polars not available",
    )
    def test_read_avro_polars(self, sample_avro_file):
        """Test reading Avro file with Polars engine."""
        proxy = read_avro(sample_avro_file, engine="polars")

        assert isinstance(proxy, DataFrameProxy)
        assert proxy.engine_name == "polars"
        assert len(proxy) == 5

    @pytest.mark.skipif(
        not pytest.importorskip("dask", reason="Dask not available"),
        reason="Dask not available",
    )
    def test_read_avro_dask(self, sample_avro_file):
        """Test reading Avro file with Dask engine."""
        proxy = read_avro(sample_avro_file, engine="dask")

        assert isinstance(proxy, DataFrameProxy)
        assert proxy.engine_name == "dask"

    def test_read_avro_auto_engine(self, sample_avro_file):
        """Test automatic engine selection for Avro."""
        proxy = read_avro(sample_avro_file)

        assert isinstance(proxy, DataFrameProxy)
        assert proxy.engine_name in ("pandas", "polars", "dask")

    def test_read_avro_nonexistent_file(self):
        """Test reading nonexistent Avro file raises error."""
        with pytest.raises(FileNotFoundError):
            read_avro("/nonexistent/file.avro")


class TestAvroWriting:
    """Test writing Avro files."""

    def test_write_avro_pandas(self, sample_df, tmp_path):
        """Test writing Avro from pandas DataFrame."""
        from parquetframe.core_v2 import DataFrameProxy

        proxy = DataFrameProxy(data=sample_df, engine="pandas")
        output_path = tmp_path / "output.avro"

        result = proxy.to_avro(output_path)

        # Check method chaining
        assert result is proxy

        # Verify file was created
        assert output_path.exists()

        # Read back and verify data
        read_proxy = read_avro(output_path, engine="pandas")
        pd.testing.assert_frame_equal(
            read_proxy.native.reset_index(drop=True),
            sample_df.reset_index(drop=True),
            check_dtype=False,  # Avro roundtrip may change dtypes slightly
        )

    def test_write_avro_with_compression(self, sample_df, tmp_path):
        """Test writing Avro with compression."""
        from parquetframe.core_v2 import DataFrameProxy

        proxy = DataFrameProxy(data=sample_df, engine="pandas")
        output_path = tmp_path / "compressed.avro"

        # Try snappy, fall back to deflate if snappy not available
        try:
            proxy.to_avro(output_path, codec="snappy")
        except ValueError as e:
            if "cramjam" in str(e):
                # Snappy requires cramjam, use deflate instead
                pytest.skip("cramjam not installed for snappy compression")
            else:
                raise

        assert output_path.exists()

        # Should be readable
        read_proxy = read_avro(output_path, engine="pandas")
        assert len(read_proxy) == 5

    def test_write_avro_empty_raises_error(self, tmp_path):
        """Test writing empty DataFrame raises error."""
        from parquetframe.core_v2 import DataFrameProxy

        proxy = DataFrameProxy()
        output_path = tmp_path / "empty.avro"

        with pytest.raises(ValueError, match="Cannot write empty DataFrameProxy"):
            proxy.to_avro(output_path)


class TestAvroSchemaInference:
    """Test Avro schema inference."""

    def test_schema_inference_basic_types(self, tmp_path):
        """Test schema inference for basic data types."""
        from parquetframe.io_new.avro import infer_avro_schema

        df = pd.DataFrame(
            {
                "int_col": [1, 2, 3],
                "float_col": [1.1, 2.2, 3.3],
                "string_col": ["a", "b", "c"],
                "bool_col": [True, False, True],
            }
        )

        schema = infer_avro_schema(df)

        # Check schema structure
        assert schema["type"] == "record"
        assert "fields" in schema
        assert len(schema["fields"]) == 4

        # Verify field types
        field_types = {field["name"]: field["type"] for field in schema["fields"]}
        assert field_types["int_col"] == "long"
        assert field_types["float_col"] == "double"
        assert field_types["string_col"] == "string"
        assert field_types["bool_col"] == "boolean"

    def test_schema_inference_with_nulls(self, tmp_path):
        """Test schema inference with nullable columns."""
        from parquetframe.io_new.avro import infer_avro_schema

        df = pd.DataFrame(
            {
                "col_with_nulls": [1, None, 3],
                "col_no_nulls": [1, 2, 3],
            }
        )

        schema = infer_avro_schema(df)

        field_types = {field["name"]: field["type"] for field in schema["fields"]}

        # Column with nulls should be union type
        assert isinstance(field_types["col_with_nulls"], list)
        assert "null" in field_types["col_with_nulls"]

        # Column without nulls should be simple type
        assert field_types["col_no_nulls"] == "long"


class TestAvroTimestampHandling:
    """Test timestamp handling in Avro."""

    def test_datetime_roundtrip(self, tmp_path):
        """Test datetime values survive roundtrip."""
        from parquetframe.core_v2 import DataFrameProxy

        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=5, freq="D"),
                "value": [1, 2, 3, 4, 5],
            }
        )

        proxy = DataFrameProxy(data=df, engine="pandas")
        output_path = tmp_path / "timestamps.avro"

        # Write
        proxy.to_avro(output_path)

        # Read back
        read_proxy = read_avro(output_path, engine="pandas")

        # Verify timestamp column
        assert "timestamp" in read_proxy.columns
        # Timestamps should be datetime objects
        assert pd.api.types.is_datetime64_any_dtype(read_proxy.native["timestamp"])


class TestAvroIntegration:
    """Test Avro integration with DataFrameProxy operations."""

    def test_read_avro_and_operations(self, sample_avro_file):
        """Test performing operations on Avro-read data."""
        proxy = read_avro(sample_avro_file, engine="pandas")

        # Perform operations
        result = proxy[proxy["age"] > 30]

        assert isinstance(result, DataFrameProxy)
        assert len(result) == 3  # 3 people over 30

    def test_read_avro_chaining(self, sample_avro_file):
        """Test chaining operations on Avro data."""
        proxy = read_avro(sample_avro_file, engine="pandas")

        # Chain operations
        result = proxy[proxy["active"]].head(2)

        assert isinstance(result, DataFrameProxy)
        assert len(result) <= 2

    def test_avro_engine_conversion(self, sample_avro_file):
        """Test converting engines after reading Avro."""
        proxy = read_avro(sample_avro_file, engine="pandas")

        # Convert to different engine
        if pytest.importorskip("polars", reason="Polars not available"):
            polars_proxy = proxy.to_polars()
            assert polars_proxy.engine_name == "polars"

    def test_read_write_roundtrip_multiple_engines(self, sample_df, tmp_path):
        """Test roundtrip with different engines."""
        from parquetframe.core_v2 import DataFrameProxy

        output_path = tmp_path / "roundtrip.avro"

        # Write with pandas
        pandas_proxy = DataFrameProxy(data=sample_df, engine="pandas")
        pandas_proxy.to_avro(output_path)

        # Read with pandas and verify
        read_pandas = read_avro(output_path, engine="pandas")
        assert len(read_pandas) == 5

        # Read with polars if available
        if pytest.importorskip("polars", reason="Polars not available"):
            read_polars = read_avro(output_path, engine="polars")
            assert len(read_polars) == 5
            assert read_polars.engine_name == "polars"


class TestAvroAutoDetection:
    """Test automatic Avro format detection."""

    def test_read_with_auto_detection(self, sample_avro_file):
        """Test read() function auto-detects .avro format."""
        from parquetframe.core_v2 import read

        proxy = read(sample_avro_file)

        assert isinstance(proxy, DataFrameProxy)
        assert len(proxy) == 5
