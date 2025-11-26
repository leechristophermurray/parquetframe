"""
Sensor Data Analysis Example

Demonstrates TIME operations for IoT sensor data processing.
"""

import numpy as np
import pandas as pd

from parquetframe.time import resample, rolling_window

# Generate sample sensor data (simulating temperature and humidity sensors)
np.random.seed(42)
n_samples = 50_000

# Create high-frequency sensor data (1 reading per second)
sensor_data = pd.DataFrame(
    {
        "timestamp": pd.date_range("2024-01-01", periods=n_samples, freq="1s"),
        "temperature": 20 + np.cumsum(np.random.randn(n_samples) * 0.1),
        "humidity": 50 + np.cumsum(np.random.randn(n_samples) * 0.5),
        "sensor_id": np.random.choice(
            ["sensor_001", "sensor_002", "sensor_003"], n_samples
        ),
    }
)

print("🌡️  Sensor Data Analysis with ParquetFrame TIME\n")
print("=" * 70)

# Example 1: Downsample to 5-minute averages for storage efficiency
print("\n1️⃣  Downsampling sensor data (1s → 5min)...")
print("-" * 70)

downsampled = resample(sensor_data, time_column="timestamp", freq="5min", agg="mean")

print(f"Original readings: {len(sensor_data):,} rows (at 1s intervals)")
print(f"Downsampled: {len(downsampled):,} rows (at 5min intervals)")
print(f"Storage reduction: {(1 - len(downsampled) / len(sensor_data)) * 100:.1f}%")
print("\nSample downsampled data:")
print(downsampled.head())

# Example 2: Detect temperature spikes with rolling statistics
print("\n\n2️⃣  Detecting temperature anomalies...")
print("-" * 70)

# Calculate rolling mean and std
rolling_mean = rolling_window(
    sensor_data, time_column="timestamp", window_size=300, agg="mean"
)
rolling_std = rolling_window(
    sensor_data, time_column="timestamp", window_size=300, agg="std"
)

# Find anomalies (temperature > mean + 2*std)
anomalies = sensor_data[
    (
        sensor_data["temperature"]
        > rolling_mean["temperature"] + 2 * rolling_std["temperature"]
    )
    | (
        sensor_data["temperature"]
        < rolling_mean["temperature"] - 2 * rolling_std["temperature"]
    )
]

print(f"Anomalies detected: {len(anomalies)} out of {len(sensor_data):,} readings")
print(f"Anomaly rate: {len(anomalies) / len(sensor_data) * 100:.2f}%")
if len(anomalies) > 0:
    print("\nSample anomalies:")
    print(anomalies[["timestamp", "temperature", "sensor_id"]].head())

# Example 3: Calculate moving average for smoothing noisy data
print("\n\n3️⃣  Smoothing sensor data with moving averages...")
print("-" * 70)

# 60-second moving average
smoothed = rolling_window(
    sensor_data, time_column="timestamp", window_size=60, agg="mean"
)

print(f"Smoothed {len(smoothed):,} data points")
print(f"Original temperature std: {sensor_data['temperature'].std():.3f}")
print(f"Smoothed temperature std: {smoothed['temperature'].std():.3f}")
print(
    f"Noise reduction: {(1 - smoothed['temperature'].std() / sensor_data['temperature'].std()) * 100:.1f}%"
)

# Example 4: Aggregate daily statistics
print("\n\n4️⃣  Daily aggregation (min/max/avg)...")
print("-" * 70)

daily_stats = resample(sensor_data, time_column="timestamp", freq="1d", agg="mean")

print(f"Daily statistics for {len(daily_stats)} days:")
print(daily_stats)

print("\n" + "=" * 70)
print(
    "✅ Analysis complete! Rust TIME provides fast, efficient sensor data processing."
)
