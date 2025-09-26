"""
"Tests for BioFrame functionality in ParquetFrame."
"""

from unittest.mock import patch

import pandas as pd
import pytest

from parquetframe.core import ParquetFrame

# Check if bioframe is available using the same check as the actual module
try:
    from parquetframe.bio import BIOFRAME_AVAILABLE
except ImportError:
    # Fallback check if bio module can't be imported
    try:
        import bioframe  # noqa: F401

        BIOFRAME_AVAILABLE = True
    except ImportError:
        BIOFRAME_AVAILABLE = False


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

    @pytest.fixture
    def overlapping_intervals(self):
        """Create overlapping genomic intervals for cluster/merge testing."""
        return pd.DataFrame(
            {
                "chrom": ["chr1", "chr1", "chr1", "chr1", "chr2"],
                "start": [100, 140, 180, 250, 500],
                "end": [150, 200, 220, 300, 600],
                "name": ["region1", "region2", "region3", "region4", "region5"],
            }
        )

    @pytest.fixture
    def genome_info(self):
        """Create genome information for complement operations."""
        return pd.DataFrame(
            {
                "chrom": ["chr1", "chr2"],
                "start": [0, 0],
                "end": [10000, 5000],
            }
        )

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

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
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

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_cluster_pandas(self, overlapping_intervals):
        """Test cluster operation on pandas DataFrame."""
        pf = ParquetFrame(overlapping_intervals, islazy=False)

        result = pf.bio.cluster(min_dist=0)

        assert isinstance(result, ParquetFrame)
        assert not result.islazy
        assert len(result) <= len(overlapping_intervals)  # Should reduce overlaps
        assert "chrom" in result.columns
        assert "start" in result.columns
        assert "end" in result.columns

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_cluster_dask(self, overlapping_intervals):
        """Test cluster operation on Dask DataFrame."""
        pf = ParquetFrame(overlapping_intervals, islazy=False)
        pf.to_dask()

        result = pf.bio.cluster(min_dist=0)

        assert isinstance(result, ParquetFrame)
        assert result.islazy  # Should maintain Dask backend

        # Compute result to verify structure
        computed_result = result.to_pandas()
        assert "chrom" in computed_result.columns
        assert "start" in computed_result.columns
        assert "end" in computed_result.columns

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_cluster_with_groupby(self, overlapping_intervals):
        """Test cluster operation with additional grouping."""
        # Add a strand column for grouping
        df = overlapping_intervals.copy()
        df["strand"] = ["+", "+", "-", "-", "+"]
        pf = ParquetFrame(df, islazy=False)

        result = pf.bio.cluster(on="strand", min_dist=10)

        assert isinstance(result, ParquetFrame)
        assert not result.islazy

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_overlap_pandas(self, genomic_data):
        """Test overlap operation between two pandas DataFrames."""
        intervals_df, peaks_df = genomic_data
        pf1 = ParquetFrame(intervals_df, islazy=False)
        pf2 = ParquetFrame(peaks_df, islazy=False)

        result = pf1.bio.overlap(pf2, how="inner")

        assert isinstance(result, ParquetFrame)
        assert not result.islazy
        # Should have overlapping intervals
        assert len(result) > 0

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_overlap_dask_with_broadcast(self, genomic_data):
        """Test overlap operation with Dask DataFrame using broadcast."""
        intervals_df, peaks_df = genomic_data
        pf1 = ParquetFrame(intervals_df, islazy=False)
        pf1.to_dask()
        pf2 = ParquetFrame(peaks_df, islazy=False)

        result = pf1.bio.overlap(pf2, broadcast=True)

        assert isinstance(result, ParquetFrame)
        assert result.islazy  # Should maintain Dask backend

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_overlap_dask_without_broadcast(self, genomic_data):
        """Test overlap operation with Dask DataFrame without broadcast (warning)."""
        intervals_df, peaks_df = genomic_data
        pf1 = ParquetFrame(intervals_df, islazy=False)
        pf1.to_dask()
        pf2 = ParquetFrame(peaks_df, islazy=False)

        with pytest.warns(UserWarning, match="Parallel overlap without broadcasting"):
            result = pf1.bio.overlap(pf2, broadcast=False)

        assert isinstance(result, ParquetFrame)
        assert not result.islazy  # Should convert to pandas

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_overlap_invalid_input(self, genomic_data):
        """Test overlap operation with invalid input type."""
        intervals_df, _ = genomic_data
        pf = ParquetFrame(intervals_df)

        with pytest.raises(TypeError, match="must be a ParquetFrame instance"):
            pf.bio.overlap(intervals_df)  # Pass DataFrame instead of ParquetFrame

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_complement_pandas(self, genomic_data, genome_info):
        """Test complement operation on pandas DataFrame."""
        intervals_df, _ = genomic_data
        pf = ParquetFrame(intervals_df, islazy=False)

        result = pf.bio.complement(view_df=genome_info)

        assert isinstance(result, ParquetFrame)
        assert not result.islazy
        assert len(result) > 0  # Should have complement intervals

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_complement_dask_conversion(self, genomic_data, genome_info):
        """Test complement operation on Dask DataFrame (converts to pandas)."""
        intervals_df, _ = genomic_data
        pf = ParquetFrame(intervals_df, islazy=False)
        pf.to_dask()

        with pytest.warns(UserWarning, match="Complement operation on lazy DataFrames"):
            result = pf.bio.complement(view_df=genome_info)

        assert isinstance(result, ParquetFrame)
        assert not result.islazy  # Should convert to pandas

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_merge_pandas(self, overlapping_intervals):
        """Test merge operation on pandas DataFrame."""
        pf = ParquetFrame(overlapping_intervals, islazy=False)

        result = pf.bio.merge(min_dist=0)

        assert isinstance(result, ParquetFrame)
        assert not result.islazy
        assert len(result) <= len(overlapping_intervals)  # Should reduce overlaps

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_merge_dask(self, overlapping_intervals):
        """Test merge operation on Dask DataFrame."""
        pf = ParquetFrame(overlapping_intervals, islazy=False)
        pf.to_dask()

        result = pf.bio.merge(min_dist=0)

        assert isinstance(result, ParquetFrame)
        assert result.islazy  # Should maintain Dask backend

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_closest_pandas(self, genomic_data):
        """Test closest operation between two pandas DataFrames."""
        intervals_df, peaks_df = genomic_data
        pf1 = ParquetFrame(intervals_df, islazy=False)
        pf2 = ParquetFrame(peaks_df, islazy=False)

        result = pf1.bio.closest(pf2)

        assert isinstance(result, ParquetFrame)
        assert not result.islazy
        assert len(result) == len(intervals_df)  # Should return same number of rows

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_closest_dask_conversion(self, genomic_data):
        """Test closest operation with Dask DataFrame (converts to pandas)."""
        intervals_df, peaks_df = genomic_data
        pf1 = ParquetFrame(intervals_df, islazy=False)
        pf1.to_dask()
        pf2 = ParquetFrame(peaks_df, islazy=False)

        with pytest.warns(UserWarning, match="Closest operation requires computing"):
            result = pf1.bio.closest(pf2)

        assert isinstance(result, ParquetFrame)
        assert not result.islazy  # Should convert to pandas

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_closest_invalid_input(self, genomic_data):
        """Test closest operation with invalid input type."""
        intervals_df, _ = genomic_data
        pf = ParquetFrame(intervals_df)

        with pytest.raises(TypeError, match="must be a ParquetFrame instance"):
            pf.bio.closest(intervals_df)  # Pass DataFrame instead of ParquetFrame

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_empty_dataframe_handling(self):
        """Test bio operations on empty DataFrames."""
        empty_df = pd.DataFrame(columns=["chrom", "start", "end"])
        pf = ParquetFrame(empty_df)

        # Cluster on empty DataFrame
        result = pf.bio.cluster()
        assert isinstance(result, ParquetFrame)
        assert len(result) == 0

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_bio_error_handling(self, genomic_data):
        """Test error handling in bio operations."""
        intervals_df, _ = genomic_data

        # Create invalid data (missing required columns)
        invalid_df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        pf = ParquetFrame(invalid_df)

        # Should raise ValueError for bioframe operations on invalid data
        with pytest.raises(ValueError, match="Bioframe .* failed"):
            pf.bio.cluster()

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_bio_accessor_initialization(self, genomic_data):
        """Test BioAccessor initialization."""
        intervals_df, _ = genomic_data
        pf = ParquetFrame(intervals_df, islazy=False)

        bio_accessor = pf.bio
        assert bio_accessor._pf is pf
        assert bio_accessor._df is pf._df
        assert bio_accessor._is_lazy == pf.islazy

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_bio_accessor_lazy_detection(self, genomic_data):
        """Test that BioAccessor correctly detects lazy vs eager backends."""
        intervals_df, _ = genomic_data

        # Test pandas backend
        pf_pandas = ParquetFrame(intervals_df, islazy=False)
        bio_pandas = pf_pandas.bio
        assert not bio_pandas._is_lazy

        # Test Dask backend
        pf_dask = ParquetFrame(intervals_df, islazy=False)
        pf_dask.to_dask()
        bio_dask = pf_dask.bio
        assert bio_dask._is_lazy


@patch("parquetframe.bio.BIOFRAME_AVAILABLE", False)
def test_bio_unavailable_error():
    """Test behavior when bioframe is not available."""
    df = pd.DataFrame({"chrom": ["chr1"], "start": [100], "end": [200]})
    pf = ParquetFrame(df)

    with pytest.raises(ImportError, match="bioframe is required"):
        _ = pf.bio


class TestBioIntegration:
    """Test bio functionality integration with real-world scenarios."""

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_genomic_workflow_pipeline(self):
        """Test a complete genomic analysis pipeline."""
        # Create sample genomic data
        genes = pd.DataFrame(
            {
                "chrom": ["chr1", "chr1", "chr1", "chr2", "chr2"],
                "start": [1000, 2000, 3000, 1000, 2000],
                "end": [1500, 2500, 3500, 1500, 2500],
                "gene_name": ["GENE1", "GENE2", "GENE3", "GENE4", "GENE5"],
            }
        )

        peaks = pd.DataFrame(
            {
                "chrom": ["chr1", "chr1", "chr2"],
                "start": [1200, 3200, 1200],
                "end": [1300, 3300, 1300],
                "peak_id": ["peak1", "peak2", "peak3"],
            }
        )

        genes_pf = ParquetFrame(genes)
        peaks_pf = ParquetFrame(peaks)

        # Find gene-peak overlaps
        overlaps = genes_pf.bio.overlap(peaks_pf, how="inner")
        assert len(overlaps) > 0

        # Cluster nearby genes
        clustered_genes = genes_pf.bio.cluster(min_dist=100)
        assert len(clustered_genes) <= len(genes)

        # Find closest peaks to genes
        closest_peaks = genes_pf.bio.closest(peaks_pf)
        assert len(closest_peaks) == len(genes)

    @pytest.mark.skipif(not BIOFRAME_AVAILABLE, reason="bioframe not available")
    def test_large_scale_parallel_processing(self):
        """Test bio operations on larger datasets with Dask backend."""
        # Create larger dataset
        n_intervals = 1000
        large_intervals = pd.DataFrame(
            {
                "chrom": [f"chr{i % 5 + 1}" for i in range(n_intervals)],
                "start": [i * 100 for i in range(n_intervals)],
                "end": [i * 100 + 50 for i in range(n_intervals)],
                "name": [f"interval_{i}" for i in range(n_intervals)],
            }
        )

        pf_large = ParquetFrame(large_intervals, islazy=False)
        pf_large.to_dask(npartitions=4)

        # Test cluster operation on large Dask DataFrame
        clustered = pf_large.bio.cluster(min_dist=25)
        assert clustered.islazy

        # Compute result to verify it works
        result = clustered.to_pandas()
        assert len(result) > 0
