# Monitoring & Metrics

ParquetFrame exposes several metrics to help you monitor the health and performance of your data pipelines.

## I/O Metrics

Track the volume and speed of data ingestion and egress.

| Metric Name | Type | Description |
| :--- | :--- | :--- |
| `pf_bytes_read_total` | Counter | Total bytes read from all sources |
| `pf_bytes_written_total` | Counter | Total bytes written to all destinations |
| `pf_read_latency_seconds` | Histogram | Time taken to read files |
| `pf_write_latency_seconds` | Histogram | Time taken to write files |

## Data Quality Metrics

Monitor the quality of data passing through your pipelines.

| Metric Name | Type | Description |
| :--- | :--- | :--- |
| `pf_rows_processed_total` | Counter | Total rows processed |
| `pf_null_values_total` | Counter | Count of null values encountered (by column) |
| `pf_schema_drift_errors` | Counter | Number of times schema validation failed |
| `pf_type_inference_fallback` | Counter | Number of times type inference fell back to object |

## Performance Counters

Internal performance indicators.

| Metric Name | Type | Description |
| :--- | :--- | :--- |
| `pf_rust_acceleration_active` | Gauge | 1 if Rust backend is active, 0 otherwise |
| `pf_cache_hits_total` | Counter | Number of metadata cache hits |
| `pf_cache_misses_total` | Counter | Number of metadata cache misses |

## Integration

Metrics are exposed via the standard Python `logging` module by default. We are planning integration with:
- **Prometheus**: Via `prometheus_client`
- **StatsD**: For aggregation
- **OpenTelemetry**: For distributed tracing
