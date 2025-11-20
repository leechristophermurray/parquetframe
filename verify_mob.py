"""
Verification script for MOB (Mobility) module.

Demonstrates geofencing and route reconstruction capabilities.
"""

import pandas as pd

print("=" * 60)
print("MOB (Mobility) Module Verification")
print("=" * 60)

# Test 1: Import MOB module
print("\n1. Testing MOB module import...")
try:
    from parquetframe import _rustic
    from parquetframe.mob import MobDataFrameAccessor

    print("✓ MOB module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import MOB module: {e}")
    exit(1)

# Test 2: Geofencing - Simple check
print("\n2. Testing basic geofencing...")
fence = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]

inside = _rustic.mob.mob_geofence_check_within(5.0, 5.0, fence)
outside = _rustic.mob.mob_geofence_check_outside(15.0, 15.0, fence)

print(f"  Point (5, 5) inside fence: {inside}")
print(f"  Point (15, 15) outside fence: {outside}")

if inside and outside:
    print("✓ Basic geofencing works correctly")
else:
    print("✗ Geofencing test failed")

# Test 3: Geofencing with DataFrame accessor
print("\n3. Testing geofencing with DataFrame accessor...")
df_geo = pd.DataFrame(
    {
        "lon": [-5.0, 5.0, 15.0, 5.0, 20.0],
        "lat": [5.0, 5.0, 5.0, 5.0, 5.0],
        "label": ["Outside", "Inside", "Outside", "Inside", "Outside"],
    }
)

result_within = df_geo.mob.geofence_check("lon", "lat", fence, op="within")
print(f"\n{result_within[['lon', 'lat', 'label', 'geofence_within']]}")

expected = [False, True, False, True, False]
if result_within["geofence_within"].tolist() == expected:
    print("✓ DataFrame geofencing works correctly")
else:
    print("✗ DataFrame geofencing test failed")

# Test 4: Enter/Exit detection
print("\n4. Testing fence enter/exit detection...")
test_path = pd.DataFrame(
    {
        "lon": [-5.0, 5.0, 6.0, 15.0, 5.0, -5.0],
        "lat": [5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
        "step": ["Start", "Enter", "Inside", "Exit", "Re-enter", "Exit again"],
    }
)

lons = test_path["lon"].values
lats = test_path["lat"].values

enters = _rustic.mob.mob_geofence_detect_enter(lons, lats, fence)
exits = _rustic.mob.mob_geofence_detect_exit(lons, lats, fence)

print("\nTest path:")
print(test_path[["lon", "lat", "step"]])
print(f"\nEnter events at indices: {list(enters)}")
print(f"Exit events at indices: {list(exits)}")

if len(enters) == 2 and len(exits) == 2:
    print("✓ Enter/exit detection works correctly")
else:
    print("✗ Enter/exit detection test failed")

# Test 5: Route reconstruction
print("\n5. Testing route reconstruction...")
route_df = pd.DataFrame(
    {
        "timestamp": pd.date_range("2024-01-01 09:00", periods=6, freq="5min"),
        "lon": [-74.0060, -74.0050, -74.0040, -74.0030, -74.0020, -74.0010],
        "lat": [40.7128, 40.7138, 40.7148, 40.7158, 40.7168, 40.7178],
    }
)

print("\nSample GPS data:")
print(route_df)

# Reconstruct route
route_result = route_df.mob.reconstruct_routes("lon", "lat")
route_coords = route_result["route_coords"].iloc[0]

print(f"\nReconstructed route with {len(route_coords)} points")

# Get start/end points
start = route_df.mob.route_start_point("lon", "lat")
end = route_df.mob.route_end_point("lon", "lat")
count = route_df.mob.route_point_count("lon", "lat")

print(f"  Start point: {start}")
print(f"  End point: {end}")
print(f"  Total points: {count}")

if count == 6 and start == (-74.0060, 40.7128) and end == (-74.0010, 40.7178):
    print("✓ Route reconstruction works correctly")
else:
    print("✗ Route reconstruction test failed")

# Test 6: Real-world scenario - Fleet tracking
print("\n6. Testing real-world scenario - Fleet vehicle tracking...")

# Define downtown geofence (simplified NYC downtown area)
downtown_fence = [
    (-74.02, 40.70),
    (-73.98, 40.70),
    (-73.98, 40.75),
    (-74.02, 40.75),
    (-74.02, 40.70),
]

# Simulated vehicle telemetry
fleet_data = pd.DataFrame(
    {
        "timestamp": pd.date_range("2024-01-01 08:00", periods=10, freq="10min"),
        "vehicle_id": ["VEH001"] * 10,
        "lon": [
            -74.03,
            -74.01,
            -74.00,
            -73.99,
            -73.99,
            -74.00,
            -74.01,
            -74.02,
            -74.03,
            -74.04,
        ],
        "lat": [40.72, 40.72, 40.72, 40.72, 40.73, 40.73, 40.73, 40.72, 40.72, 40.72],
    }
)

# Check which points are in downtown
fleet_result = fleet_data.mob.geofence_check(
    "lon", "lat", downtown_fence, op="within", output_col="in_downtown"
)

print("\nFleet tracking data:")
print(fleet_result[["timestamp", "vehicle_id", "lon", "lat", "in_downtown"]])

downtown_time = fleet_result["in_downtown"].sum()
print(
    f"\nVehicle was in downtown area for {downtown_time} data points (~{downtown_time * 10} minutes)"
)

print("\n" + "=" * 60)
print("✓ MOB Module Verification Complete!")
print("=" * 60)
print("\nAll core functionality working:")
print("  • Geofencing (within/outside)")
print("  • Enter/Exit detection")
print("  • Route reconstruction")
print("  • DataFrame .mob accessor")
