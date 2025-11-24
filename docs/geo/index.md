# GeoSpatial Operations

ParquetFrame provides a `.geo` accessor for geospatial operations on GeoDataFrames.

## Quick Start

```python
import geopandas as gpd
import parquetframe.geo  # Register accessor

# Load spatial data
gdf = gpd.read_file("cities.geojson")

# Use .geo accessor
buffered = gdf.geo.buffer(1000)  # 1km buffer
area = gdf.geo.area()
centroids = gdf.geo.centroid()
```

## Installation

```bash
pip install geopandas
```

## Basic Operations

### Buffer

Create buffer around geometries:

```python
# Buffer by distance
buffered = gdf.geo.buffer(1000)  # meters

# Variable buffer
gdf['buffer'] = gdf.geo.buffer(gdf['radius'])
```

### Area & Length

```python
# Calculate area
area = gdf.geo.area()

# Calculate perimeter/length
length = gdf.geo.length()
```

### Centroids

```python
# Get centroids
centroids = gdf.geo.centroid()
```

## Spatial Relationships

### Distance

```python
from shapely.geometry import Point

# Distance to a point
point = Point(-74, 40)
distances = gdf.geo.distance(point)

# Distance between two GeoDataFrames
distances = gdf1.geo.distance(gdf2)
```

### Contains/Within

```python
from shapely.geometry import Polygon

# Create polygon
polygon = Polygon([(-120, 30), (-100, 30), (-100, 40), (-120, 40)])

# Check if points are within polygon
within = gdf.geo.within(polygon)

# Filter points within polygon
filtered = gdf[within]
```

### Intersection

```python
# Spatial predicates
intersects = gdf.geo.intersects(other_geom)
contains = gdf.geo.contains(other_geom)
```

## Spatial Operations

### Intersection & Union

```python
# Intersection
intersection = gdf.geo.intersection(other_gdf)

# Union
union = gdf.geo.union(other_gdf)
```

### Spatial Join

```python
# Join based on spatial relationship
joined = cities.geo.sjoin(
    states,
    how='left',
    predicate='within'
)

# Available predicates:
# - 'intersects'
# - 'contains'
# - 'within'
# - 'crosses'
# - 'overlaps'
```

## Coordinate Reference Systems

### Transform CRS

```python
# From WGS84 to Web Mercator
web_mercator = gdf.geo.to_crs('EPSG:3857')

# To custom CRS
projected = gdf.geo.to_crs('+proj=aea +lat_1=29.5 +lat_2=45.5')
```

## Complete Example

```python
import geopandas as gpd
from shapely.geometry import Point, Polygon
import parquetframe.geo

# Create cities
cities = gpd.GeoDataFrame({
    'name': ['NYC', 'LA', 'Chicago'],
    'population': [8336000, 3979000, 2693000],
    'geometry': [
        Point(-74, 40),
        Point(-118, 34),
        Point(-88, 42)
    ]
}, crs='EPSG:4326')

# Create regions
states = gpd.GeoDataFrame({
    'state': ['NY', 'CA', 'IL'],
    'geometry': [
        Polygon([(-79, 40), (-72, 40), (-72, 45), (-79, 45)]),
        Polygon([(-124, 32), (-114, 32), (-114, 42), (-124, 42)]),
        Polygon([(-91, 37), (-87, 37), (-87, 42), (-91, 42)]),
    ]
}, crs='EPSG:4326')

# Buffer cities by 100km (in Web Mercator)
cities_buffered = cities.geo.to_crs('EPSG:3857')
cities_buffered = cities_buffered.geo.buffer(100000)  # 100km

# Spatial join
cities_with_state = cities.geo.sjoin(states, predicate='within')
print(cities_with_state[['name', 'state']])

# Calculate areas
print(f"Buffer areas: {cities_buffered.geo.area()}")
```

## Examples

See [`examples/geo/basic_operations.py`](../../examples/geo/basic_operations.py) for complete examples including:
- Basic geospatial operations
- Spatial joins
- CRS transformations
- Spatial analysis

## Performance Notes

Current implementation uses GeoPandas/Shapely. Future versions will leverage the Rust `pf-geo-core` backend for:
- Faster spatial operations
- Parallel processing
- H3/S2 spatial indexing

## API Reference

### .geo.buffer()

```python
gdf.geo.buffer(distance: float) -> GeoDataFrame
```

Create buffer around geometries.

### .geo.area()

```python
gdf.geo.area() -> Series
```

Calculate area of geometries.

### .geo.distance()

```python
gdf.geo.distance(other) -> Series
```

Calculate distance to other geometry.

### .geo.sjoin()

```python
gdf.geo.sjoin(other, how='inner', predicate='intersects') -> GeoDataFrame
```

Spatial join with another GeoDataFrame.

### .geo.to_crs()

```python
gdf.geo.to_crs(crs: str) -> GeoDataFrame
```

Transform to different CRS.
