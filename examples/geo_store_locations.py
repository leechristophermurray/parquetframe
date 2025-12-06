"""
Store Location Analysis using ParquetFrame GEO Module

Demonstrates:
- Loading location data
- Distance calculations between stores
- Finding stores within radius
- CRS transformations
"""

import numpy as np
import pandas as pd

# Transform from WGS84 (4326) to Web Mercator (3857)
from parquetframe._rustic.geo import geo_transform_coords

# Sample store location data
np.random.seed(42)
stores = pd.DataFrame(
    {
        "store_id": range(1, 11),
        "name": [f"Store {i}" for i in range(1, 11)],
        "lon": np.random.uniform(-122.5, -122.3, 10),  # San Francisco area
        "lat": np.random.uniform(37.7, 37.8, 10),
    }
)

print("=" * 80)
print("STORE LOCATION ANALYSIS WITH PARQUETFRAME GEO")
print("=" * 80)
print(f"\nAnalyzing {len(stores)} store locations in San Francisco")
print()

# Calculate distance from headquarters to all stores
hq_lon, hq_lat = -122.4, 37.75

print("📍 DISTANCE FROM HQ")
print("-" * 80)

# Using GEO accessor
distances = []
for _, store in stores.iterrows():
    from parquetframe._rustic.geo import geo_haversine_distance

    dist = geo_haversine_distance(hq_lon, hq_lat, store["lon"], store["lat"])
    distances.append(dist / 1000)  # Convert to km

stores["distance_from_hq_km"] = distances
stores_sorted = stores.sort_values("distance_from_hq_km")

print("\nStores by distance from HQ:")
for _, store in stores_sorted.head(5).iterrows():
    print(f"  {store['name']:<12} {store['distance_from_hq_km']:>6.2f} km")

print()
print("🔍 STORES WITHIN 5KM RADIUS")
print("-" * 80)

nearby_stores = stores[stores["distance_from_hq_km"] <= 5.0]
print(f"Found {len(nearby_stores)} stores within 5km of HQ")

print()
print("🗺️  CRS TRANSFORMATION")
print("-" * 80)


transformed = []
for _, store in stores.iterrows():
    x, y = geo_transform_coords(store["lon"], store["lat"], 4326, 3857)
    transformed.append({"store_id": store["store_id"], "x_meters": x, "y_meters": y})

print("Sample transformed coordinates (Web Mercator):")
for t in transformed[:3]:
    print(
        f"  Store {t['store_id']}: x={t['x_meters']:>12,.0f}m, y={t['y_meters']:>11,.0f}m"
    )

print()
print("=" * 80)
print("✅ Analysis complete!")
print("=" * 80)
print("\nKey Insights:")
print(
    f"• Nearest store: {stores_sorted.iloc[0]['name']} ({stores_sorted.iloc[0]['distance_from_hq_km']:.2f} km)"
)
print(
    f"• Farthest store: {stores_sorted.iloc[-1]['name']} ({stores_sorted.iloc[-1]['distance_from_hq_km']:.2f} km)"
)
print(f"• {len(nearby_stores)} stores within 5km delivery radius")
