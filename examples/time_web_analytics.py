"""
Web Analytics using ParquetFrame TIME Module

This example demonstrates:
- Website traffic time-series analysis
- Hourly/daily traffic patterns
- Session analytics with rolling windows
- Time-based cohort analysis
- Request rate limiting detection
"""

import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

try:
    from parquetframe._rustic import time_resample_sum
except ImportError:
    print("Warning: Rust backend not available. Skipping TIME module examples.")
    exit(0)

# Generate simulated web traffic data
np.random.seed(42)
start_time = datetime(2024, 1, 1, 0, 0, 0)

# Create realistic web traffic pattern (higher during business hours)
num_requests = 50000
timestamps = []
current_time = start_time

for _i in range(num_requests):
    # Add realistic time gaps (busier during day)
    hour = current_time.hour
    if 9 <= hour <= 17:  # Business hours
        gap = np.random.exponential(scale=2)  # More frequent
    else:
        gap = np.random.exponential(scale=10)  # Less frequent

    current_time += timedelta(seconds=gap)
    timestamps.append(current_time)

# Create request data
web_traffic = pd.DataFrame(
    {
        "timestamp": timestamps,
        "user_id": np.random.choice(
            range(1, 1001), size=num_requests
        ),  # 1000 unique users
        "page_view_duration": np.abs(
            np.random.gamma(2, 30, size=num_requests)
        ),  # seconds
        "endpoint": np.random.choice(
            ["/home", "/products", "/api/data", "/checkout", "/profile"],
            size=num_requests,
            p=[0.4, 0.25, 0.15, 0.1, 0.1],
        ),
        "status_code": np.random.choice(
            [200, 404, 500], size=num_requests, p=[0.95, 0.04, 0.01]
        ),
    }
)

print("=" * 80)
print("WEB ANALYTICS WITH PARQUETFRAME TIME")
print("=" * 80)
print(f"\nAnalyzing {len(web_traffic):,} web requests")
print(
    f"Time range: {web_traffic['timestamp'].min()} to {web_traffic['timestamp'].max()}"
)
print(f"Unique users: {web_traffic['user_id'].nunique():,}")
print()

print("📊 TRAFFIC PATTERNS")
print("-" * 80)

# Resample to hourly request counts
web_traffic["count"] = 1
ts_ms = web_traffic["timestamp"].astype("int64") // 10**6
counts_array = web_traffic["count"].values

hourly_counts = time_resample_sum(
    ts_ms.values,
    counts_array,
    60 * 60 * 1000,  # 1 hour in milliseconds
)

hourly_df = pd.DataFrame(
    {
        "timestamp": pd.to_datetime(hourly_counts["timestamps"], unit="ms"),
        "requests": hourly_counts["values"],
    }
)

print(f"Total requests:            {len(web_traffic):>12,}")
print(f"Peak hour requests:        {hourly_df['requests'].max():>12,.0f}")
print(f"Average requests/hour:     {hourly_df['requests'].mean():>12,.1f}")
print(f"Min requests/hour:         {hourly_df['requests'].min():>12,.0f}")

# Identify peak hours
hourly_analysis = web_traffic.groupby(web_traffic["timestamp"].dt.hour).size()
peak_hour = hourly_analysis.idxmax()
peak_requests = hourly_analysis.max()

print(f"\nPeak traffic hour:         {peak_hour}:00 ({peak_requests:,} requests)")

print()
print("⏱️  SESSION ANALYTICS")
print("-" * 80)

# Calculate session durations (group by user, consider session timeout of 30 min)
web_traffic_sorted = web_traffic.sort_values(["user_id", "timestamp"])
web_traffic_sorted["time_diff"] = web_traffic_sorted.groupby("user_id")[
    "timestamp"
].diff()
web_traffic_sorted["new_session"] = (
    web_traffic_sorted["time_diff"] > timedelta(minutes=30)
) | (web_traffic_sorted["time_diff"].isna())
web_traffic_sorted["session_id"] = web_traffic_sorted.groupby("user_id")[
    "new_session"
].cumsum()

# Session statistics
sessions = web_traffic_sorted.groupby(["user_id", "session_id"]).agg(
    {"timestamp": ["min", "max", "count"], "page_view_duration": "sum"}
)

sessions.columns = ["session_start", "session_end", "page_views", "total_duration"]
sessions["session_length"] = (
    sessions["session_end"] - sessions["session_start"]
).dt.total_seconds() / 60

print(f"Total sessions:            {len(sessions):>12,}")
print(f"Avg session length:        {sessions['session_length'].mean():>12.1f} minutes")
print(f"Avg pages per session:     {sessions['page_views'].mean():>12.1f}")
print(f"Avg time on site:          {sessions['total_duration'].mean():>12.1f} seconds")

# Bounce rate (single-page sessions)
bounces = (sessions["page_views"] == 1).sum()
bounce_rate = bounces / len(sessions)
print(f"Bounce rate:               {bounce_rate:>12.1%}")

print()
print("🚦 ERROR ANALYSIS")
print("-" * 80)

# Error rates by endpoint
error_by_endpoint = (
    web_traffic.groupby(["endpoint", "status_code"]).size().unstack(fill_value=0)
)
error_by_endpoint["error_rate"] = (
    error_by_endpoint.get(404, 0) + error_by_endpoint.get(500, 0)
) / error_by_endpoint.sum(axis=1)

print("Endpoint Error Rates:")
print(f"{'Endpoint':<20} {'Total':<10} {'Errors':<10} {'Rate':<10}")
print("-" * 50)
for endpoint in error_by_endpoint.index:
    total = error_by_endpoint.loc[endpoint].sum()
    errors = error_by_endpoint.loc[endpoint].get(404, 0) + error_by_endpoint.loc[
        endpoint
    ].get(500, 0)
    rate = error_by_endpoint.loc[endpoint, "error_rate"]
    print(f"{endpoint:<20} {total:<10.0f} {errors:<10.0f} {rate:<10.1%}")

print()
print("👥 USER ENGAGEMENT")
print("-" * 80)

# User activity analysis
user_activity = web_traffic.groupby("user_id").agg(
    {"timestamp": ["min", "max", "count"], "page_view_duration": "mean"}
)

user_activity.columns = ["first_seen", "last_seen", "total_requests", "avg_duration"]
user_activity["days_active"] = (
    user_activity["last_seen"] - user_activity["first_seen"]
).dt.total_seconds() / 86400

# Segment users by activity
user_activity["segment"] = pd.cut(
    user_activity["total_requests"],
    bins=[0, 10, 50, 1000],
    labels=["Low", "Medium", "High"],
)

print("User Segments:")
for segment in ["Low", "Medium", "High"]:
    count = (user_activity["segment"] == segment).sum()
    avg_requests = user_activity[user_activity["segment"] == segment][
        "total_requests"
    ].mean()
    print(f"  {segment:<10} {count:>6} users  (avg {avg_requests:>6.1f} requests)")

# Top users
print("\nTop 5 Most Active Users:")
top_users = user_activity.nlargest(5, "total_requests")[
    ["total_requests", "avg_duration"]
]
for user_id, row in top_users.iterrows():
    print(
        f"  User {user_id:>4}: {row['total_requests']:>4.0f} requests, avg {row['avg_duration']:>5.1f}s per page"
    )

print()
print("⚡ TIME MODULE PERFORMANCE")
print("-" * 80)

# Benchmark TIME resampling
start = time.time()
for _ in range(100):
    _ = time_resample_sum(ts_ms.values, counts_array, 60 * 60 * 1000)
time_duration = time.time() - start

start = time.time()
for _ in range(100):
    _ = web_traffic.set_index("timestamp").resample("1h")["count"].sum()
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
print(
    f"• Processed {len(web_traffic):,} requests from {web_traffic['user_id'].nunique():,} users"
)
print(f"• Peak hour: {peak_hour}:00 with {peak_requests:,} requests")
print(
    f"• Average session: {sessions['page_views'].mean():.1f} pages, {sessions['session_length'].mean():.1f} minutes"
)
print(f"• Bounce rate: {bounce_rate:.1%}")
print(f"• TIME module is {speedup:.1f}x faster than pandas for hourly resampling")
