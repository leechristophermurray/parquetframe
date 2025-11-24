"""
Unit tests for execution context and mode selection.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from parquetframe.core.execution import (
    ExecutionMode,
    ExecutionContext,
    ExecutionPlanner,
    set_execution_config,
    get_execution_context,
)


class TestExecutionMode:
    """Test ExecutionMode enum."""

    def test_modes_exist(self):
        assert ExecutionMode.AUTO.value == "auto"
        assert ExecutionMode.LOCAL.value == "local"
        assert ExecutionMode.DISTRIBUTED.value == "distributed"
        assert ExecutionMode.HYBRID.value == "hybrid"


class TestExecutionContext:
    """Test ExecutionContext configuration."""

    def test_default_creation(self):
        ctx = ExecutionContext()
        assert ctx.mode == ExecutionMode.AUTO
        assert ctx.rust_threads == 0
        assert ctx.distributed_backend == "ray"
        assert ctx.distributed_nodes == 1

    def test_custom_creation(self):
        ctx = ExecutionContext(
            mode=ExecutionMode.LOCAL,
            rust_threads=16,
            distributed_backend="dask",
            distributed_nodes=4,
        )
        assert ctx.mode == ExecutionMode.LOCAL
        assert ctx.rust_threads == 16
        assert ctx.distributed_backend == "dask"
        assert ctx.distributed_nodes == 4

    def test_from_env(self):
        """Test creating context from environment variables."""
        with patch.dict(
            os.environ,
            {
                "PF_EXECUTION_MODE": "distributed",
                "PF_RUST_THREADS": "32",
                "PF_DISTRIBUTED_BACKEND": "ray",
                "PF_DISTRIBUTED_NODES": "8",
            },
        ):
            ctx = ExecutionContext.from_env()
            assert ctx.mode == ExecutionMode.DISTRIBUTED
            assert ctx.rust_threads == 32
            assert ctx.distributed_backend == "ray"
            assert ctx.distributed_nodes == 8

    def test_auto_detect_small_data(self):
        """Small data should use local mode."""
        ctx = ExecutionContext.auto_detect(data_size_gb=0.5, available_nodes=1)
        assert ctx.mode == ExecutionMode.LOCAL
        assert ctx.rust_threads == 4

    def test_auto_detect_medium_data(self):
        """Medium data should use local with all cores."""
        ctx = ExecutionContext.auto_detect(data_size_gb=5.0, available_nodes=1)
        assert ctx.mode == ExecutionMode.LOCAL
        assert ctx.rust_threads == 0  # All cores

    def test_auto_detect_large_data_with_cluster(self):
        """Large data + cluster should use hybrid."""
        ctx = ExecutionContext.auto_detect(data_size_gb=50.0, available_nodes=8)
        assert ctx.mode == ExecutionMode.HYBRID
        assert ctx.distributed_nodes == 8
        assert ctx.rust_threads == 16

    def test_auto_detect_very_large_data_with_cluster(self):
        """Very large data + cluster should use distributed."""
        ctx = ExecutionContext.auto_detect(data_size_gb=200.0, available_nodes=16)
        assert ctx.mode == ExecutionMode.DISTRIBUTED
        assert ctx.distributed_nodes == 16
        assert ctx.rust_threads == 8

    def test_resolve_with_override(self):
        """Test mode override."""
        ctx = ExecutionContext(mode=ExecutionMode.AUTO)
        new_ctx = ctx.resolve("local")
        assert new_ctx.mode == ExecutionMode.LOCAL


class TestExecutionPlanner:
    """Test ExecutionPlanner intelligent selection."""

    @patch("parquetframe.core.execution.ExecutionPlanner.check_distributed_available")
    def test_check_ray_available(self, mock_check):
        """Test Ray cluster detection."""
        with patch("parquetframe.core.execution.ray") as mock_ray:
            mock_ray.is_initialized.return_value = True
            mock_ray.nodes.return_value = [1, 2, 3, 4]  # 4 nodes

            available, num_nodes = ExecutionPlanner.check_distributed_available()
            assert available is True
            assert num_nodes == 4

    @patch("parquetframe.core.execution.ExecutionPlanner.check_distributed_available")
    def test_plan_with_user_preference(self, mock_check):
        """User preference should override auto-detection."""
        mock_check.return_value = (True, 8)

        ctx = ExecutionPlanner.plan_execution(
            operation="filter",
            data_size_gb=1.0,
            user_preference=ExecutionMode.DISTRIBUTED,
        )
        assert ctx.mode == ExecutionMode.DISTRIBUTED

    @patch("parquetframe.core.execution.ExecutionPlanner.check_distributed_available")
    def test_plan_auto_no_cluster(self, mock_check):
        """No cluster available should use local."""
        mock_check.return_value = (False, 1)

        ctx = ExecutionPlanner.plan_execution(
            operation="filter", data_size_gb=5.0, user_preference=None
        )
        assert ctx.mode == ExecutionMode.LOCAL


class TestGlobalConfig:
    """Test global execution configuration."""

    def test_set_and_get_config(self):
        """Test setting global config."""
        set_execution_config(
            mode="distributed", rust_threads=64, distributed_backend="dask"
        )

        ctx = get_execution_context()
        assert ctx.mode == ExecutionMode.DISTRIBUTED
        assert ctx.rust_threads == 64
        assert ctx.distributed_backend == "dask"
