"""
DataFrameProxy: Unified DataFrame wrapper with Rust-first execution.

Provides:
- Narwhals-based backend compatibility (pandas/Polars/Dask)
- Rust-accelerated operations with GIL release
- Execution mode support (local/distributed/hybrid)
- Zero-overhead delegation
"""

from typing import Union

import pandas as pd

try:
    import polars as pl

    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False
    pl = None

try:
    import dask.dataframe as dd

    DASK_AVAILABLE = True
except ImportError:
    DASK_AVAILABLE = False
    dd = None

try:
    import narwhals as nw

    NARWHALS_AVAILABLE = True
except ImportError:
    NARWHALS_AVAILABLE = False
    nw = None

from .execution import ExecutionContext, ExecutionMode, get_execution_context


class DataFrameProxy:
    """
    Unified DataFrame wrapper with Rust-first design.

    Operations automatically choose between:
    - Rust parallel (PyO3 + Rayon)
    - Rust distributed (Ray workers + Rayon)
    - Narwhals backend-agnostic (fallback)

    Examples:
        # Auto-detect execution mode
        >>> proxy = DataFrameProxy(df)
        >>> result = proxy.filter(condition)

        # Explicit distributed mode
        >>> proxy = DataFrameProxy(df, execution_mode="distributed")
        >>> result = proxy.join(other, on="id")
    """

    def __init__(
        self,
        native_df: Union[pd.DataFrame, "pl.DataFrame", "dd.DataFrame"],
        execution_ctx: ExecutionContext | None = None,
        execution_mode: str | None = None,
    ):
        """
        Initialize DataFrameProxy.

        Args:
            native_df: Native DataFrame (pandas/Polars/Dask)
            execution_ctx: Optional execution context
            execution_mode: Optional mode override (auto/local/distributed/hybrid)
        """
        self._native = native_df
        self._backend = self._detect_backend(native_df)

        # Initialize narwhals wrapper if available
        if NARWHALS_AVAILABLE:
            self._nw = nw.from_native(native_df)
        else:
            self._nw = None

        # Setup execution context
        if execution_mode:
            self._exec_ctx = get_execution_context().resolve(execution_mode)
        elif execution_ctx:
            self._exec_ctx = execution_ctx
        else:
            # Auto-detect based on data size
            size_gb = self._estimate_size_gb()
            from .execution import ExecutionPlanner

            available, num_nodes = ExecutionPlanner.check_distributed_available()
            self._exec_ctx = ExecutionContext.auto_detect(size_gb, num_nodes)

        # Check if Rust backend available
        self._rust_available = self._check_rust_available()

    def _detect_backend(self, df) -> str:
        """Detect backend type."""
        if isinstance(df, pd.DataFrame):
            return "pandas"
        elif POLARS_AVAILABLE and isinstance(df, pl.DataFrame | pl.LazyFrame):
            return "polars"
        elif DASK_AVAILABLE and isinstance(df, dd.DataFrame):
            return "dask"
        else:
            raise TypeError(f"Unsupported DataFrame type: {type(df)}")

    def _check_rust_available(self) -> bool:
        """Check if Rust backend is available."""
        import importlib.util

        return importlib.util.find_spec("parquetframe.pf_py") is not None

    def _estimate_size_gb(self) -> float:
        """Estimate DataFrame size in GB."""
        try:
            if self._backend == "pandas":
                return self._native.memory_usage(deep=True).sum() / 1e9
            elif self._backend == "polars":
                return self._native.estimated_size() / 1e9
            elif self._backend == "dask":
                # Estimate from metadata
                return self._native.memory_usage(deep=True).sum().compute() / 1e9
        except Exception:
            return 0.1  # Conservative fallback

    # =========================================================================
    # Rust-Accelerated Operations (Bypass Narwhals)
    # =========================================================================

    def filter_rust(self, condition):
        """
        Rust-accelerated filter with execution mode support.

        Chooses between:
        - Local parallel (Rayon)
        - Distributed (Ray/Dask + Rayon)

        Args:
            condition: Filter condition

        Returns:
            New DataFrameProxy with filtered data
        """
        if not self._rust_available:
            return self.filter(condition)  # Fallback to narwhals

        if self._exec_ctx.mode == ExecutionMode.DISTRIBUTED:
            return self._filter_distributed_rust(condition)
        else:
            return self._filter_local_rust(condition)

    def _filter_local_rust(self, condition):
        """Rust parallel filter (Rayon)."""
        from parquetframe.pf_py import filter_parallel

        result = filter_parallel(
            self._native, condition, num_threads=self._exec_ctx.rust_threads or 0
        )
        return DataFrameProxy(result, self._exec_ctx)

    def _filter_distributed_rust(self, condition):
        """Distributed Rust filter (Ray/Dask workers)."""
        if self._exec_ctx.distributed_backend == "ray":
            from parquetframe.distributed.ray_ops import distributed_filter

            result = distributed_filter(
                self._native,
                condition,
                num_nodes=self._exec_ctx.distributed_nodes,
                rust_threads=self._exec_ctx.rust_threads,
            )
        else:
            from parquetframe.distributed.dask_ops import distributed_filter

            result = distributed_filter(
                self._native,
                condition,
                num_workers=self._exec_ctx.distributed_nodes,
                rust_threads=self._exec_ctx.rust_threads,
            )

        return DataFrameProxy(result, self._exec_ctx)

    # =========================================================================
    # Narwhals-Based Operations (Backend Agnostic)
    # =========================================================================

    def filter(self, *predicates):
        """
        Generic filter using narwhals.

        Provides backend-agnostic filtering when Rust not available
        or for complex predicates.
        """
        if not NARWHALS_AVAILABLE:
            raise RuntimeError(
                "Narwhals not available. Install with: pip install narwhals"
            )

        result = self._nw.filter(*predicates)
        return DataFrameProxy(result.to_native(), self._exec_ctx)

    def select(self, *cols):
        """Column selection via narwhals."""
        if not NARWHALS_AVAILABLE:
            # Fallback to direct backend
            if self._backend == "pandas":
                return DataFrameProxy(self._native[list(cols)], self._exec_ctx)
            else:
                raise RuntimeError("Narwhals required for Polars/Dask select")

        result = self._nw.select(*cols)
        return DataFrameProxy(result.to_native(), self._exec_ctx)

    def group_by(self, *cols):
        """Group by operation via narwhals."""
        if not NARWHALS_AVAILABLE:
            raise RuntimeError("Narwhals not available")

        # Return narwhals GroupBy (can wrap in future)
        return self._nw.group_by(*cols)

    # =========================================================================
    # Properties and Utilities
    # =========================================================================

    @property
    def native(self):
        """Access underlying native DataFrame."""
        return self._native

    @property
    def backend(self) -> str:
        """Get backend type."""
        return self._backend

    @property
    def execution_mode(self) -> ExecutionMode:
        """Get current execution mode."""
        return self._exec_ctx.mode

    def set_execution_mode(self, mode: str):
        """Change execution mode for this proxy."""
        self._exec_ctx = self._exec_ctx.resolve(mode)
        return self

    def collect(self):
        """
        Materialize lazy operations.

        For Polars LazyFrame or Dask DataFrame.
        """
        if isinstance(self._native, pl.LazyFrame):
            return DataFrameProxy(self._native.collect(), self._exec_ctx)
        elif DASK_AVAILABLE and isinstance(self._native, dd.DataFrame):
            return DataFrameProxy(self._native.compute(), self._exec_ctx)
        return self

    def __repr__(self):
        return (
            f"DataFrameProxy(\n"
            f"  backend={self._backend},\n"
            f"  mode={self._exec_ctx.mode.value},\n"
            f"  rust={self._rust_available},\n"
            f"  df={self._native.__repr__()}\n"
            f")"
        )

    # =========================================================================
    # Delegation to Native DataFrame
    # =========================================================================

    def __getattr__(self, name):
        """Delegate unknown attributes to native DataFrame."""
        if name.startswith("_"):
            raise AttributeError(f"No attribute '{name}'")
        return getattr(self._native, name)


__all__ = ["DataFrameProxy"]
