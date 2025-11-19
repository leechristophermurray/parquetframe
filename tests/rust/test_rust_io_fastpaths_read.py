"""Tests for Rust fast-path CSV/Parquet readers.

These tests validate that the Rust layer returns Arrow IPC bytes which we
reconstruct into pyarrow.Table on the Python side.
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

try:
    from parquetframe import _rustic
    from parquetframe.io_rust import RustIOEngine

    RUST_AVAILABLE = bool(getattr(_rustic, "io_fastpaths_available", lambda: False)())
except Exception:  # pragma: no cover
    RUST_AVAILABLE = False


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust I/O fast-paths not available")
class TestRustFastReaders:
    def test_parquet_read_fast_returns_pyarrow_table(self):
        df = pd.DataFrame({"id": [1, 2, 3], "x": [10.0, 11.5, 12.25]})
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
            df.to_parquet(f.name, index=False)
            p = Path(f.name)
        try:
            eng = RustIOEngine()
            table = eng.read_parquet(p)
            assert hasattr(table, "num_rows")
            assert table.num_rows == 3
            assert table.schema.names == ["id", "x"]
        finally:
            p.unlink(missing_ok=True)

    def test_parquet_projection_and_row_groups(self):
        import numpy as np
        import pyarrow as pa
        import pyarrow.parquet as pq

        # Create a table with two columns and enough rows for multiple row groups
        tbl = pa.table(
            {
                "c1": np.arange(0, 1000, dtype=np.int64),
                "c2": np.arange(1000, 2000, dtype=np.int64),
            }
        )
        tmp = tempfile.NamedTemporaryFile(suffix=".parquet", delete=False)
        p = Path(tmp.name)
        tmp.close()
        try:
            # Write with small row_group_size to create multiple row groups
            pq.write_table(tbl, p, row_group_size=200)
            eng = RustIOEngine()
            # Project only c2, and select first two row groups
            table = eng.read_parquet(p, columns=["c2"], row_groups=[0, 1])
            assert table.num_columns == 1
            assert table.schema.names == ["c2"]
            # Expect 400 rows (2 row groups of size 200)
            assert table.num_rows == 400
        finally:
            p.unlink(missing_ok=True)

    @pytest.mark.skip(
        reason="CSV fast-path temporarily disabled on Arrow 57; awaiting API migration"
    )
    def test_csv_read_fast_returns_pyarrow_table(self):
        df = pd.DataFrame({"a": ["u", "v", "w"], "b": [1, 2, 3]})
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
            df.to_csv(f, index=False)
            p = Path(f.name)
        try:
            eng = RustIOEngine()
            table = eng.read_csv(p, delimiter=",", has_header=True)
            assert table.num_rows == 3
            assert table.schema.names == ["a", "b"]
        finally:
            p.unlink(missing_ok=True)
