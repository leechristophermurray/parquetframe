"""
Tests for BioFrame functionality in ParquetFrame.
"""

from unittest.mock import patch

import pandas as pd
import pytest

from parquetframe.core import ParquetFrame


class TestBioAccessor:
    """Test the bio accessor functionality."""

    @pytest.fixture
    def genomic_data(self):
        """Create sample genomic interval data for testing."""
        intervals_df = pd.DataFrame(
            {
                "chrom": ["chr1", "chr1", "chr1", "chr2", "chr2"],
                "start": [100, 200, 250, 1000, 1050],
                "end": [150, 220, 300, 1100, 1200],
                "name": ["gene1", "gene2", "gene3", "gene4", "gene5"],
                "score": [10, 20, 15, 30, 25],
            }
        )

        peaks_df = pd.DataFrame(
            {
                "chrom": ["chr1", "chr1", "chr2"],
                "start": [110, 275, 1080],
                "end": [130, 285, 1090],
                "peak_id": ["peak1", "peak2", "peak3"],
                "intensity": [100, 200, 150],
            }
        )

        return intervals_df, peaks_df

    def test_bio_availability_check(self):
        """Test that bioframe availability is properly checked."""
        try:
            import bioframe  # noqa: F401

            from parquetframe.bio import BIOFRAME_AVAILABLE

            assert BIOFRAME_AVAILABLE
        except ImportError:
            from parquetframe.bio import BIOFRAME_AVAILABLE

            assert not BIOFRAME_AVAILABLE

    @patch("parquetframe.bio.BIOFRAME_AVAILABLE", False)
    def test_bio_accessor_unavailable(self, genomic_data):
        """Test bio accessor behavior when bioframe is not available."""
        intervals_df, _ = genomic_data
        pf = ParquetFrame(intervals_df)

        with pytest.raises(ImportError, match="bioframe is required"):
            _ = pf.bio

    @pytest.mark.skipif(
        condition=lambda: not hasattr(pytest, "importorskip")
        or not pytest.importorskip("bioframe"),
        reason="bioframe not available",
    )
    def test_bio_accessor_available(self, genomic_data):
        """Test bio accessor when bioframe is available."""
        intervals_df, _ = genomic_data
        pf = ParquetFrame(intervals_df)

        bio_accessor = pf.bio
        assert bio_accessor is not None
        assert hasattr(bio_accessor, "cluster")
        assert hasattr(bio_accessor, "overlap")
        assert hasattr(bio_accessor, "complement")
        assert hasattr(bio_accessor, "merge")
        assert hasattr(bio_accessor, "closest")


@patch("parquetframe.bio.BIOFRAME_AVAILABLE", False)
def test_bio_unavailable_error():
    """Test behavior when bioframe is not available."""
    df = pd.DataFrame({"chrom": ["chr1"], "start": [100], "end": [200]})

    pf = ParquetFrame(df)

    with pytest.raises(ImportError, match="bioframe is required"):
        _ = pf.bio
