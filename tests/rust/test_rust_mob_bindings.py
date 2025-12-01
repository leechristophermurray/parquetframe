"""Tests for Rust MOB (Mobility) bindings."""

import numpy as np
import pytest

try:
    from parquetframe import _rustic

    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    _rustic = None


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestMobGeofencing:
    """Test geofencing operations."""

    def sample_square_fence(self):
        """Create a simple square geofence."""
        return [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (0.0, 10.0),
            (0.0, 0.0),
        ]

    def test_geofence_check_within(self):
        """Test within geofence check."""
        fence = self.sample_square_fence()

        # Point inside
        assert _rustic.mob.mob_geofence_check_within(5.0, 5.0, fence) is True

        # Point outside
        assert _rustic.mob.mob_geofence_check_within(15.0, 15.0, fence) is False

    def test_geofence_check_outside(self):
        """Test outside geofence check."""
        fence = self.sample_square_fence()

        # Point inside
        assert _rustic.mob.mob_geofence_check_outside(5.0, 5.0, fence) is False

        # Point outside
        assert _rustic.mob.mob_geofence_check_outside(15.0, 15.0, fence) is True

    def test_geofence_detect_enter(self):
        """Test fence entry detection."""
        fence = self.sample_square_fence()

        # Path: outside -> inside -> inside
        lons = np.array([-5.0, 5.0, 6.0], dtype=np.float64)
        lats = np.array([5.0, 5.0, 5.0], dtype=np.float64)

        enters = _rustic.mob.mob_geofence_detect_enter(lons, lats, fence)

        assert len(enters) == 1
        assert enters[0] == 1  # Entry at index 1

    def test_geofence_detect_exit(self):
        """Test fence exit detection."""
        fence = self.sample_square_fence()

        # Path: inside -> inside -> outside
        lons = np.array([5.0, 6.0, 15.0], dtype=np.float64)
        lats = np.array([5.0, 5.0, 5.0], dtype=np.float64)

        exits = _rustic.mob.mob_geofence_detect_exit(lons, lats, fence)

        assert len(exits) == 1
        assert exits[0] == 2  # Exit at index 2

    def test_geofence_multiple_transitions(self):
        """Test multiple enter/exit transitions."""
        fence = self.sample_square_fence()

        # Path: outside -> inside -> outside -> inside
        lons = np.array([-5.0, 5.0, 15.0, 5.0], dtype=np.float64)
        lats = np.array([5.0, 5.0, 5.0, 5.0], dtype=np.float64)

        enters = _rustic.mob.mob_geofence_detect_enter(lons, lats, fence)
        assert len(enters) == 2
        assert enters[0] == 1
        assert enters[1] == 3

        exits = _rustic.mob.mob_geofence_detect_exit(lons, lats, fence)
        assert len(exits) == 1
        assert exits[0] == 2

    def test_geofence_empty_arrays(self):
        """Test with empty input arrays."""
        fence = self.sample_square_fence()
        lons = np.array([], dtype=np.float64)
        lats = np.array([], dtype=np.float64)

        enters = _rustic.mob.mob_geofence_detect_enter(lons, lats, fence)
        assert len(enters) == 0

        exits = _rustic.mob.mob_geofence_detect_exit(lons, lats, fence)
        assert len(exits) == 0


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestMobRoutes:
    """Test route reconstruction operations."""

    def test_reconstruct_simple_route(self):
        """Test basic route reconstruction."""
        lons = np.array([0.0, 1.0, 2.0, 3.0], dtype=np.float64)
        lats = np.array([0.0, 1.0, 2.0, 3.0], dtype=np.float64)

        route_coords = _rustic.mob.mob_reconstruct_route(lons, lats)

        assert len(route_coords) == 4
        assert route_coords[0] == (0.0, 0.0)
        assert route_coords[3] == (3.0, 3.0)

    def test_route_start_point(self):
        """Test getting route start point."""
        lons = np.array([10.0, 11.0, 12.0], dtype=np.float64)
        lats = np.array([20.0, 21.0, 22.0], dtype=np.float64)

        start = _rustic.mob.mob_route_start_point(lons, lats)

        assert start == (10.0, 20.0)

    def test_route_end_point(self):
        """Test getting route end point."""
        lons = np.array([10.0, 11.0, 12.0], dtype=np.float64)
        lats = np.array([20.0, 21.0, 22.0], dtype=np.float64)

        end = _rustic.mob.mob_route_end_point(lons, lats)

        assert end == (12.0, 22.0)

    def test_route_point_count(self):
        """Test counting route points."""
        lons = np.array([0.0, 1.0, 2.0, 3.0, 4.0], dtype=np.float64)
        lats = np.array([0.0, 1.0, 2.0, 3.0, 4.0], dtype=np.float64)

        count = _rustic.mob.mob_route_point_count(lons, lats)

        assert count == 5

    def test_route_minimum_points(self):
        """Test route with minimum number of points."""
        lons = np.array([0.0, 1.0], dtype=np.float64)
        lats = np.array([0.0, 1.0], dtype=np.float64)

        route_coords = _rustic.mob.mob_reconstruct_route(lons, lats)

        assert len(route_coords) == 2

    def test_route_insufficient_points(self):
        """Test that single point raises error."""
        lons = np.array([0.0], dtype=np.float64)
        lats = np.array([0.0], dtype=np.float64)

        with pytest.raises(ValueError, match="at least 2 points"):
            _rustic.mob.mob_reconstruct_route(lons, lats)

    def test_route_mismatched_arrays(self):
        """Test that mismatched arrays raise error."""
        lons = np.array([0.0, 1.0, 2.0], dtype=np.float64)
        lats = np.array([0.0, 1.0], dtype=np.float64)

        with pytest.raises(ValueError, match="same length"):
            _rustic.mob.mob_reconstruct_route(lons, lats)


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestMobAccessor:
    """Test the .mob accessor on pandas DataFrames."""

    def test_mob_accessor_import(self):
        """Test that mob accessor can be imported and used."""
        import pandas as pd

        # Import the accessor to register it with pandas
        import parquetframe.mob  # noqa: F401

        # Create a simple DataFrame
        df = pd.DataFrame(
            {
                "lon": [0.0, 5.0, 15.0],
                "lat": [5.0, 5.0, 5.0],
            }
        )

        # Access the .mob accessor
        assert hasattr(df, "mob")

    def test_mob_geofence_within_accessor(self):
        """Test geofencing with accessor."""
        import pandas as pd

        # Import the accessor to register it with pandas
        import parquetframe.mob  # noqa: F401

        fence = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]

        df = pd.DataFrame(
            {
                "lon": [5.0, 15.0, 7.0],
                "lat": [5.0, 5.0, 7.0],
            }
        )

        result = df.mob.geofence_check("lon", "lat", fence, op="within")

        assert "geofence_within" in result.columns
        assert result["geofence_within"].tolist() == [True, False, True]

    def test_mob_route_reconstruction_accessor(self):
        """Test route reconstruction with accessor."""
        import pandas as pd

        # Import the accessor to register it with pandas
        import parquetframe.mob  # noqa: F401

        df = pd.DataFrame(
            {
                "lon": [0.0, 1.0, 2.0, 3.0],
                "lat": [0.0, 1.0, 2.0, 3.0],
            }
        )

        result = df.mob.reconstruct_routes("lon", "lat")

        assert "route_coords" in result.columns
        route = result["route_coords"].iloc[0]
        assert len(route) == 4
        assert route[0] == (0.0, 0.0)
