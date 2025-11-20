import pandas as pd


def test_geo_buffer():
    df = pd.DataFrame({"lon": [0.0, 1.0], "lat": [0.0, 1.0]})

    # Initialize accessor (normally done via pd.api.extensions.register_dataframe_accessor)
    # But we can use it directly for testing if needed, or use df.geo

    # Ensure accessor is registered
    try:
        _ = df.geo
    except AttributeError:
        print("Geo accessor not registered automatically?")

    # Buffer by 1.0 degree
    buffers = df.geo.buffer("lon", "lat", 1.0)

    assert len(buffers) == 2
    assert len(buffers[0]) > 0
    # Check if it looks like a polygon (list of tuples)
    assert isinstance(buffers[0], list)
    assert isinstance(buffers[0][0], tuple)
    print("Buffer test passed!")


def test_haversine():
    df = pd.DataFrame({"lon1": [0.0], "lat1": [0.0], "lon2": [0.0], "lat2": [1.0]})

    df_dist = df.geo.haversine_distance("lon1", "lat1", "lon2", "lat2")
    dist = df_dist["distance_m"][0]
    # 1 degree lat is approx 111km
    assert 110000 < dist < 112000
    print(f"Haversine test passed: {dist} m")


if __name__ == "__main__":
    test_geo_buffer()
    test_haversine()
