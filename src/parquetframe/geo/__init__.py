"""
ParquetFrame Geospatial Module

Provides geospatial operations for DataFrames with Rust acceleration.
"""

import pandas as pd

from parquetframe._rustic import geo as _geo


class GeoAccessor:
    """Accessor for geospatial operations on DataFrames."""

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def haversine_distance(
        self,
        lon1_col: str,
        lat1_col: str,
        lon2_col: str,
        lat2_col: str,
        output_col: str | None = None,
    ) -> pd.DataFrame:
        """
        Calculate Haversine distance between point pairs.

        Args:
            lon1_col: Column name for first point longitude
            lat1_col: Column name for first point latitude
            lon2_col: Column name for second point longitude
            lat2_col: Column name for second point latitude
            output_col: Name for output column (default: 'distance_m')

        Returns:
            DataFrame with distance column added (in meters)
        """
        if output_col is None:
            output_col = "distance_m"

        df = self._df.copy()
        distances = []

        for _, row in df.iterrows():
            dist = _geo.geo_haversine_distance(
                row[lon1_col], row[lat1_col], row[lon2_col], row[lat2_col]
            )
            distances.append(dist)

        df[output_col] = distances
        return df

    def buffer(
        self,
        lon_col: str,
        lat_col: str,
        distance: float,
    ) -> list[list[tuple[float, float]]]:
        """
        Create circular buffers around points.

        Args:
            lon_col: Column name for longitude
            lat_col: Column name for latitude
            distance: Buffer distance (in degrees for WGS84)

        Returns:
            List of polygon coordinates for each point
        """
        buffers = []

        for _, row in self._df.iterrows():
            poly_coords = _geo.geo_buffer_point(row[lon_col], row[lat_col], distance)
            buffers.append(poly_coords)

        return buffers

    def point_in_polygon(
        self,
        lon_col: str,
        lat_col: str,
        polygon_coords: list[tuple[float, float]],
        output_col: str | None = None,
    ) -> pd.DataFrame:
        """
        Check if points are within a polygon.

        Args:
            lon_col: Column name for longitude
            lat_col: Column name for latitude
            polygon_coords: Polygon boundary as list of (lon, lat) tuples
            output_col: Name for output column (default: 'in_polygon')

        Returns:
            DataFrame with boolean column added
        """
        if output_col is None:
            output_col = "in_polygon"

        df = self._df.copy()
        results = []

        for _, row in df.iterrows():
            inside = _geo.geo_point_in_polygon(
                row[lon_col], row[lat_col], polygon_coords
            )
            results.append(inside)

        df[output_col] = results
        return df

    def transform_coords(
        self,
        lon_col: str,
        lat_col: str,
        from_epsg: int = 4326,
        to_epsg: int = 3857,
        output_lon_col: str | None = None,
        output_lat_col: str | None = None,
    ) -> pd.DataFrame:
        """
        Transform coordinates from one CRS to another.

        Args:
            lon_col: Column name for longitude
            lat_col: Column name for latitude
            from_epsg: Source EPSG code (default: 4326 WGS84)
            to_epsg: Target EPSG code (default: 3857 Web Mercator)
            output_lon_col: Name for transformed longitude (default: 'lon_transformed')
            output_lat_col: Name for transformed latitude (default: 'lat_transformed')

        Returns:
            DataFrame with transformed coordinate columns added
        """
        if output_lon_col is None:
            output_lon_col = "lon_transformed"
        if output_lat_col is None:
            output_lat_col = "lat_transformed"

        df = self._df.copy()
        transformed_lons = []
        transformed_lats = []

        for _, row in df.iterrows():
            lon_new, lat_new = _geo.geo_transform_coords(
                row[lon_col], row[lat_col], from_epsg, to_epsg
            )
            transformed_lons.append(lon_new)
            transformed_lats.append(lat_new)

        df[output_lon_col] = transformed_lons
        df[output_lat_col] = transformed_lats
        return df

    @staticmethod
    def read_geojson(geojson_str: str) -> list[tuple[float, float]]:
        """
        Read point coordinates from GeoJSON string.

        Args:
            geojson_str: GeoJSON string

        Returns:
            List of (lon, lat) tuples
        """
        return _geo.geo_read_geojson(geojson_str)

    @staticmethod
    def write_geojson(points: list[tuple[float, float]]) -> str:
        """
        Write points to GeoJSON string.

        Args:
            points: List of (lon, lat) tuples

        Returns:
            GeoJSON FeatureCollection string
        """
        return _geo.geo_write_geojson(points)


# Register the accessor
@pd.api.extensions.register_dataframe_accessor("geo")
class GeoDataFrameAccessor(GeoAccessor):
    """Pandas DataFrame accessor for geospatial operations."""

    pass


__all__ = ["GeoAccessor", "GeoDataFrameAccessor"]
