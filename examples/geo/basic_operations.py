"""
GeoSpatial Operations Examples

Demonstrates geospatial operations using the .geo accessor.
"""

import pandas as pd
import numpy as np


def basic_operations():
    """Basic geospatial operations."""
    try:
        import geopandas as gpd
        from shapely.geometry import Point, Polygon
    except ImportError:
        print("⚠️  GeoPandas not installed.")
        print("Install with: pip install geopandas")
        return

    # Import accessor
    import parquetframe.geo  # noqa

    print("=" * 60)
    print("Basic GeoSpatial Operations")
    print("=" * 60)

    # Create sample points (cities)
    cities = gpd.GeoDataFrame(
        {
            "name": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"],
            "population": [8336000, 3979000, 2693000, 2320000, 1680000],
            "geometry": [
                Point(-74.0060, 40.7128),  # NYC
                Point(-118.2437, 34.0522),  # LA
                Point(-87.6298, 41.8781),  # Chicago
                Point(-95.3698, 29.7604),  # Houston
                Point(-112.0740, 33.4484),  # Phoenix
            ],
        },
        crs="EPSG:4326",
    )

    print("\nCities:")
    print(cities)

    # Buffer (create 1-degree radius around cities)
    buffered = cities.geo.buffer(1.0)
    print("\nBuffered cities (1 degree):")
    print(f"Original area: {cities.geo.area().head()}")
    print(f"Buffered area: {buffered.geo.area().head()}")

    # Centroids
    centroids = cities.geo.centroid()
    print("\nCentroids:")
    print(centroids.geometry.head())

    # Calculate distance
    ny_point = cities.loc[cities["name"] == "New York", "geometry"].iloc[0]
    distances = cities.geo.distance(ny_point)
    print("\nDistance from New York:")
    print(distances)


def spatial_joins():
    """Spatial join operations."""
    try:
        import geopandas as gpd
        from shapely.geometry import Point, Polygon
    except ImportError:
        return

    import parquetframe.geo  # noqa

    print("\n" + "=" * 60)
    print("Spatial Joins")
    print("=" * 60)

    # Create regions (states)
    states = gpd.GeoDataFrame(
        {
            "state": ["California", "Texas", "New York"],
            "geometry": [
                Polygon([(-124, 32), (-114, 32), (-114, 42), (-124, 42)]),  # CA
                Polygon([(-106, 26), (-94, 26), (-94, 36), (-106, 36)]),  # TX
                Polygon([(-79, 40), (-72, 40), (-72, 45), (-79, 45)]),  # NY
            ],
        },
        crs="EPSG:4326",
    )

    # Create points (cities)
    cities = gpd.GeoDataFrame(
        {
            "city": ["Los Angeles", "Houston", "New York", "Phoenix"],
            "geometry": [
                Point(-118, 34),
                Point(-95, 30),
                Point(-74, 41),
                Point(-112, 33),
            ],
        },
        crs="EPSG:4326",
    )

    # Spatial join - find which state each city is in
    joined = cities.geo.sjoin(states, how="left", predicate="within")
    print("\nCities with their states:")
    print(joined[["city", "state"]])


def coordinate_transformations():
    """CRS transformations."""
    try:
        import geopandas as gpd
        from shapely.geometry import Point
    except ImportError:
        return

    import parquetframe.geo  # noqa

    print("\n" + "=" * 60)
    print("Coordinate Transformations")
    print("=" * 60)

    # Create points in WGS84 (lat/lon)
    points = gpd.GeoDataFrame(
        {"name": ["Point A", "Point B"], "geometry": [Point(-118, 34), Point(-74, 41)]},
        crs="EPSG:4326",
    )

    print("\nOriginal (WGS84):")
    print(points.geometry)

    # Transform to Web Mercator
    web_mercator = points.geo.to_crs("EPSG:3857")
    print("\nWeb Mercator:")
    print(web_mercator.geometry)


def spatial_analysis():
    """Spatial analysis operations."""
    try:
        import geopandas as gpd
        from shapely.geometry import Point, Polygon
    except ImportError:
        return

    import parquetframe.geo  # noqa

    print("\n" + "=" * 60)
    print("Spatial Analysis")
    print("=" * 60)

    # Create a polygon (region of interest)
    roi = Polygon([(-120, 30), (-100, 30), (-100, 40), (-120, 40)])

    # Create random points
    np.random.seed(42)
    n_points = 20
    points = gpd.GeoDataFrame(
        {
            "id": range(n_points),
            "value": np.random.randint(10, 100, n_points),
            "geometry": [
                Point(x, y)
                for x, y in zip(
                    np.random.uniform(-125, -95, n_points),
                    np.random.uniform(25, 45, n_points),
                )
            ],
        },
        crs="EPSG:4326",
    )

    # Check which points are within ROI
    within_roi = points.geo.within(roi)
    print(f"\nTotal points: {len(points)}")
    print(f"Points within ROI: {within_roi.sum()}")

    # Filter points within ROI
    filtered = points[within_roi]
    print(f"\nFiltered points:")
    print(filtered)

    # Calculate area and centroid of ROI
    roi_gdf = gpd.GeoDataFrame({"geometry": [roi]}, crs="EPSG:4326")
    print(f"\nROI area: {roi_gdf.geo.area().iloc[0]:.2f}")
    print(f"ROI centroid: {roi_gdf.geo.centroid().geometry.iloc[0]}")


def main():
    """Run all examples."""
    try:
        import geopandas as gpd
    except ImportError:
        print("=" * 60)
        print("⚠️  GeoPandas not installed!")
        print("=" * 60)
        print("\nInstall with:")
        print("  pip install geopandas")
        print("\nOr:")
        print("  conda install geopandas")
        return

    basic_operations()
    spatial_joins()
    coordinate_transformations()
    spatial_analysis()

    print("\n" + "=" * 60)
    print("✅ All geospatial examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
