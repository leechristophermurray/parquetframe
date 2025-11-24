"""
Unit tests for metrics collection.
"""

import time

from parquetframe.core.metrics import MetricsCollector, get_metrics_collector


class TestMetricsCollector:
    """Test metrics collection functionality."""

    def test_record_metric(self):
        """Test recording a simple metric."""
        collector = MetricsCollector()
        collector.record("test_metric", 1.0, tag="value")

        summary = collector.get_summary()
        assert "test_metric" in summary
        assert summary["test_metric"]["count"] == 1
        assert summary["test_metric"]["avg"] == 1.0

    def test_timer_context(self):
        """Test timer context manager."""
        collector = MetricsCollector()

        with collector.timer("test_timer", operation="sleep"):
            time.sleep(0.01)

        summary = collector.get_summary()
        assert "test_timer" in summary
        assert summary["test_timer"]["count"] == 1
        assert summary["test_timer"]["avg"] >= 0.01

    def test_global_collector(self):
        """Test global collector singleton."""
        collector = get_metrics_collector()
        collector.clear()

        collector.record("global_metric", 42.0)

        summary = collector.get_summary()
        assert "global_metric" in summary
        assert summary["global_metric"]["max"] == 42.0

    def test_disable_enable(self):
        """Test enabling/disabling collection."""
        collector = MetricsCollector()
        collector.disable()

        collector.record("ignored", 1.0)
        assert len(collector.get_summary()) == 0

        collector.enable()
        collector.record("captured", 1.0)
        assert "captured" in collector.get_summary()
