"""
IoT Sensor Data Analysis using ParquetFrame TIME Module

This example demonstrates:
- Multi-sensor time-series data processing
- Resampling to different time intervals
- Rolling window calculations
- Anomaly detection
- As-of joins for event correlation
"""

from datetime import datetime

import numpy as np
import pandas as pd

# Generate simulated IoT sensor data (temperature, humidity, pressure)
np.random.seed(42)
start_time = datetime(2024, 1, 1, 0, 0, 0)
timestamps = pd.date_range(start=start_time, periods=10000, freq="1min")

# Simulate 3 sensors with realistic patterns
sensor_data = pd.DataFrame(
    {
        "timestamp": timestamps,
        # Temperature sensor (°C) - daily cycle + noise
        "temperature": 20
        + 5 * np.sin(2 * np.pi * np.arange(len(timestamps)) / (24 * 60))
        + np.random.randn(len(timestamps)) * 0.5,
        # Humidity sensor (%) - inverse correlation with temp
        "humidity": 60
        - 10 * np.sin(2 * np.pi * np.arange(len(timestamps)) / (24 * 60))
        + np.random.randn(len(timestamps)) * 2,
        # Pressure sensor (hPa)
        "pressure": 1013 + np.random.randn(len(timestamps)) * 0.3,
    }
)

# Add some anomalies
anomaly_indices = np.random.choice(len(sensor_data), size=20, replace=False)
sensor_data.loc[anomaly_indices, "temperature"] += np.random.uniform(10, 15, size=20)

print("=" * 80)
print("IOT SENSOR DATA ANALYSIS WITH PARQUETFRAME TIME")
print("=" * 80)
print(f"\nAnalyzing {len(timestamps)} sensor readings")
print(f"Time range: {timestamps[0]} to {timestamps[-1]}")
print("Sampling frequency: 1 minute")
print()

# Import ParquetFrame TIME operations
from parquetframe._rustic import time_resample_mean, time_rolling_mean, time_rolling_std

print("📊 RESAMPLING TO DIFFERENT INTERVALS")
print("-" * 80)

# Resample to 15-minute intervals
ts_ms = sensor_data["timestamp"].astype("int64") // 10**6  # Convert to milliseconds
temp_array = sensor_data["temperature"].values

resampled_15min = time_resample_mean(
    ts_ms.values,
    temp_array,
    15 * 60 * 1000,  # 15 minutes in milliseconds
)

print(f"Original data points:      {len(sensor_data):>8,}")
print(f"15-min resampled:          {len(resampled_15min['values']):>8,}")
print(
    f"Reduction factor:          {len(sensor_data) / len(resampled_15min['values']):>8.1f}x"
)

# Resample to hourly
resampled_hourly = time_resample_mean(
    ts_ms.values,
    temp_array,
    60 * 60 * 1000,  # 1 hour in milliseconds
)

print(f"Hourly resampled:          {len(resampled_hourly['values']):>8,}")
print(
    f"Reduction factor:          {len(sensor_data) / len(resampled_hourly['values']):>8.1f}x"
)

print()
print("📈 ROLLING WINDOW CALCULATIONS")
print("-" * 80)

# Calculate rolling statistics for anomaly detection
window_size = 60  # 1-hour window

rolling_mean_temp = time_rolling_mean(temp_array, window_size)
rolling_std_temp = time_rolling_std(temp_array, window_size)

# Detect anomalies (values > 3 standard deviations from rolling mean)
sensor_data["rolling_mean"] = rolling_mean_temp
sensor_data["rolling_std"] = rolling_std_temp
sensor_data["z_score"] = (
    sensor_data["temperature"] - sensor_data["rolling_mean"]
) / sensor_data["rolling_std"]
sensor_data["is_anomaly"] = abs(sensor_data["z_score"]) > 3

num_anomalies = sensor_data["is_anomaly"].sum()

print(f"Window size:               {window_size} samples (1 hour)")
print(f"Anomalies detected:        {num_anomalies}")
print(f"Anomaly rate:              {num_anomalies/len(sensor_data)*100:.2f}%")

# Show sample anomalies
print("\nDetected Temperature Anomalies:")
anomalies = sensor_data[sensor_data["is_anomaly"]][
    ["timestamp", "temperature", "rolling_mean", "z_score"]
].head(5)
for _, row in anomalies.iterrows():
    print(
        f"  {row['timestamp']}  {row['temperature']:>6.2f}°C (expected: {row['rolling_mean']:>6.2f}°C, z={row['z_score']:>5.2f})"
    )

print()
print("🔗 SENSOR CORRELATION ANALYSIS")
print("-" * 80)

# Calculate correlation between sensors
corr_temp_humidity = sensor_data[["temperature", "humidity"]].corr().iloc[0, 1]
corr_temp_pressure = sensor_data[["temperature", "pressure"]].corr().iloc[0, 1]

print(f"Temperature vs Humidity:   {corr_temp_humidity:>7.3f} (inverse relationship)")
print(f"Temperature vs Pressure:   {corr_temp_pressure:>7.3f}")

print()
print("📉 STATISTICAL SUMMARY")
print("-" * 80)

# Hourly statistics
hourly_stats = sensor_data.groupby(sensor_data["timestamp"].dt.hour).agg(
    {
        "temperature": ["mean", "std", "min", "max"],
        "humidity": ["mean", "std"],
    }
)

print("\nHourly Temperature Statistics (sample hours):")
print("Hour  Mean    Std     Min     Max")
print("-" * 40)
for hour in [0, 6, 12, 18]:
    stats = hourly_stats.loc[hour, "temperature"]
    print(
        f"{hour:>4}  {stats['mean']:>6.2f}  {stats['std']:>6.2f}  {stats['min']:>6.2f}  {stats['max']:>6.2f}"
    )

print()
print("⚡ PERFORMANCE METRICS")
print("-" * 80)

# Demonstrate TIME module performance vs pandas
import time

# TIME module resampling
start = time.time()
for _ in range(100):
    _ = time_resample_mean(ts_ms.values, temp_array, 15 * 60 * 1000)
time_duration = time.time() - start

# Pandas resampling
start = time.time()
for _ in range(100):
    _ = sensor_data.set_index("timestamp")["temperature"].resample("15min").mean()
pandas_duration = time.time() - start

speedup = pandas_duration / time_duration

print(f"TIME module (100 iterations): {time_duration:>8.3f}s")
print(f"Pandas (100 iterations):      {pandas_duration:>8.3f}s")
print(f"Speedup:                      {speedup:>8.1f}x faster")

print()
print("=" * 80)
print("✅ Analysis complete!")
print("=" * 80)
print("\nKey Insights:")
print(f"• Processed {len(sensor_data):,} sensor readings")
print(f"• Detected {num_anomalies} temperature anomalies using rolling statistics")
print(
    f"• Temperature and humidity show {abs(corr_temp_humidity):.2f} correlation (inverse)"
)
print(f"• TIME module is {speedup:.1f}x faster than pandas for resampling")
