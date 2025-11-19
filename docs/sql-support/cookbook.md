# SQL Cookbook

Real-world SQL recipes and patterns for common data analysis tasks using ParquetFrame's multi-format SQL engine.

## 📚 Table of Contents

- [ETL Operations](#etl-operations)
- [Data Analysis Patterns](#data-analysis-patterns)
- [Cross-Format Joins](#cross-format-joins)
- [Time Series Analysis](#time-series-analysis)
- [Window Functions](#window-functions)
- [Data Quality & Validation](#data-quality-validation)
- [Performance Optimization](#performance-optimization)
- [Advanced Analytics](#advanced-analytics)

## ETL Operations

### Basic ETL Pipeline

Transform data from multiple sources into a clean, analysis-ready format:

```python
import parquetframe as pf

# Extract from different sources
raw_users = pf.read("raw_users.csv")          # CSV from CRM
raw_events = pf.read("user_events.jsonl")     # JSON Lines from logs
raw_products = pf.read("products.parquet")    # Parquet from warehouse

# Transform with SQL
cleaned_users = raw_users.sql("""
    SELECT
        user_id,
        TRIM(UPPER(name)) as name,
        LOWER(email) as email,
        CASE
            WHEN age BETWEEN 18 AND 65 THEN age
            ELSE NULL
        END as age,
        COALESCE(country, 'Unknown') as country,
        created_at::TIMESTAMP as created_at
    FROM df
    WHERE email IS NOT NULL
        AND email LIKE '%@%'
        AND LENGTH(name) > 0
""")

# Aggregate events data
user_activity = raw_events.sql("""
    SELECT
        user_id,
        COUNT(*) as total_events,
        COUNT(DISTINCT event_type) as unique_event_types,
        MIN(event_timestamp) as first_event,
        MAX(event_timestamp) as last_event,
        SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as purchase_events
    FROM df
    WHERE event_timestamp >= '2024-01-01'
    GROUP BY user_id
    HAVING total_events >= 5
""")

# Join and create final dataset
user_profiles = cleaned_users.sql("""
    SELECT
        u.user_id,
        u.name,
        u.email,
        u.age,
        u.country,
        a.total_events,
        a.unique_event_types,
        a.purchase_events,
        DATEDIFF('day', a.first_event, a.last_event) as engagement_days,
        CASE
            WHEN a.purchase_events > 10 THEN 'high_value'
            WHEN a.purchase_events > 2 THEN 'medium_value'
            ELSE 'low_value'
        END as customer_segment
    FROM df u
    LEFT JOIN activity a ON u.user_id = a.user_id
    ORDER BY a.total_events DESC NULLS LAST
""", activity=user_activity)

# Load the result
user_profiles.save("user_profiles_clean.parquet")
```

### Data Deduplication

Remove duplicate records with various strategies:

```python
# Method 1: Keep first occurrence
deduplicated_users = users.sql("""
    SELECT DISTINCT ON (email) *
    FROM df
    ORDER BY email, created_at ASC
""")

# Method 2: Keep most recent record
latest_users = users.sql("""
    SELECT *
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY email
                   ORDER BY updated_at DESC
               ) as rn
        FROM df
    ) ranked
    WHERE rn = 1
""")

# Method 3: Aggregate duplicates
merged_users = users.sql("""
    SELECT
        email,
        MAX(name) as name,
        MAX(created_at) as created_at,
        COUNT(*) as duplicate_count,
        STRING_AGG(DISTINCT source, ', ') as sources
    FROM df
    GROUP BY email
    HAVING COUNT(*) >= 1
""")
```

## Data Analysis Patterns

### Customer Segmentation Analysis

```python
# RFM Analysis (Recency, Frequency, Monetary)
orders = pf.read("orders.parquet")

rfm_analysis = orders.sql("""
    WITH customer_metrics AS (
        SELECT
            customer_id,
            DATEDIFF('day', MAX(order_date), CURRENT_DATE) as recency_days,
            COUNT(DISTINCT order_id) as frequency,
            SUM(order_amount) as monetary_value,
            AVG(order_amount) as avg_order_value
        FROM df
        WHERE order_date >= '2023-01-01'
        GROUP BY customer_id
    ),
    percentiles AS (
        SELECT
            *,
            NTILE(5) OVER (ORDER BY recency_days DESC) as recency_score,
            NTILE(5) OVER (ORDER BY frequency ASC) as frequency_score,
            NTILE(5) OVER (ORDER BY monetary_value ASC) as monetary_score
        FROM customer_metrics
    )
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary_value,
        avg_order_value,
        recency_score,
        frequency_score,
        monetary_score,
        (recency_score + frequency_score + monetary_score) as rfm_score,
        CASE
            WHEN (recency_score + frequency_score + monetary_score) >= 13 THEN 'Champions'
            WHEN (recency_score + frequency_score + monetary_score) >= 10 THEN 'Loyal Customers'
            WHEN (recency_score + frequency_score + monetary_score) >= 7 THEN 'Potential Loyalists'
            WHEN recency_score >= 4 AND frequency_score <= 2 THEN 'New Customers'
            WHEN recency_score <= 2 THEN 'At Risk'
            ELSE 'Others'
        END as customer_segment
    FROM percentiles
    ORDER BY rfm_score DESC
""")

# Segment summary
segment_summary = rfm_analysis.sql("""
    SELECT
        customer_segment,
        COUNT(*) as customer_count,
        AVG(monetary_value) as avg_monetary_value,
        AVG(frequency) as avg_frequency,
        AVG(recency_days) as avg_recency_days,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as segment_percentage
    FROM df
    GROUP BY customer_segment
    ORDER BY avg_monetary_value DESC
""")
```

### Cohort Analysis

```python
# Monthly cohort analysis
cohort_analysis = orders.sql("""
    WITH user_cohorts AS (
        SELECT
            customer_id,
            DATE_TRUNC('month', MIN(order_date)) as cohort_month
        FROM df
        GROUP BY customer_id
    ),
    user_activities AS (
        SELECT
            o.customer_id,
            DATE_TRUNC('month', o.order_date) as activity_month,
            uc.cohort_month,
            DATEDIFF('month', uc.cohort_month, DATE_TRUNC('month', o.order_date)) as period_number
        FROM df o
        JOIN user_cohorts uc ON o.customer_id = uc.customer_id
    ),
    cohort_table AS (
        SELECT
            cohort_month,
            period_number,
            COUNT(DISTINCT customer_id) as users_count
        FROM user_activities
        GROUP BY cohort_month, period_number
    ),
    cohort_sizes AS (
        SELECT
            cohort_month,
            COUNT(DISTINCT customer_id) as cohort_size
        FROM user_cohorts
        GROUP BY cohort_month
    )
    SELECT
        ct.cohort_month,
        cs.cohort_size,
        ct.period_number,
        ct.users_count,
        ROUND(ct.users_count * 100.0 / cs.cohort_size, 2) as retention_rate
    FROM cohort_table ct
    JOIN cohort_sizes cs ON ct.cohort_month = cs.cohort_month
    WHERE ct.period_number <= 12  -- First 12 months
    ORDER BY ct.cohort_month, ct.period_number
""")
```

## Cross-Format Joins

### E-commerce Analytics Across Multiple Sources

```python
# Load data from different systems and formats
customers = pf.read("customers.csv")           # CRM system (CSV)
orders = pf.read("orders.jsonl")              # Transaction logs (JSON Lines)
products = pf.read("products.parquet")        # Product catalog (Parquet)
reviews = pf.read("reviews.json")             # Review system (JSON)

# Complex cross-format analysis
ecommerce_insights = customers.sql("""
    WITH customer_stats AS (
        SELECT
            c.customer_id,
            c.customer_name,
            c.email,
            c.registration_date,
            c.customer_segment,
            COUNT(DISTINCT o.order_id) as total_orders,
            SUM(o.order_amount) as total_spent,
            AVG(o.order_amount) as avg_order_value,
            MIN(o.order_date) as first_order_date,
            MAX(o.order_date) as last_order_date
        FROM df c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
        WHERE o.order_status = 'completed'
        GROUP BY c.customer_id, c.customer_name, c.email,
                 c.registration_date, c.customer_segment
    ),
    product_preferences AS (
        SELECT
            o.customer_id,
            p.category,
            COUNT(*) as category_orders,
            SUM(o.quantity * p.price) as category_spending,
            ROW_NUMBER() OVER (
                PARTITION BY o.customer_id
                ORDER BY COUNT(*) DESC
            ) as category_rank
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        GROUP BY o.customer_id, p.category
    ),
    review_sentiment AS (
        SELECT
            customer_id,
            COUNT(*) as review_count,
            AVG(CASE WHEN rating >= 4 THEN 1.0 ELSE 0.0 END) as positive_review_rate,
            AVG(rating) as avg_rating
        FROM reviews
        GROUP BY customer_id
    )
    SELECT
        cs.customer_id,
        cs.customer_name,
        cs.email,
        cs.customer_segment,
        cs.total_orders,
        cs.total_spent,
        cs.avg_order_value,
        DATEDIFF('day', cs.first_order_date, cs.last_order_date) as customer_lifetime_days,
        pp.category as favorite_category,
        pp.category_spending as favorite_category_spending,
        rs.review_count,
        rs.avg_rating,
        rs.positive_review_rate,
        CASE
            WHEN cs.total_spent > 1000 AND rs.avg_rating >= 4.5 THEN 'VIP'
            WHEN cs.total_spent > 500 AND rs.avg_rating >= 4.0 THEN 'Premium'
            WHEN cs.total_orders >= 5 THEN 'Regular'
            ELSE 'New'
        END as loyalty_tier
    FROM customer_stats cs
    LEFT JOIN product_preferences pp ON cs.customer_id = pp.customer_id AND pp.category_rank = 1
    LEFT JOIN review_sentiment rs ON cs.customer_id = rs.customer_id
    WHERE cs.total_orders > 0
    ORDER BY cs.total_spent DESC
""", orders=orders, products=products, reviews=reviews)
```

### Supply Chain Analysis

```python
# Load supply chain data from different sources
suppliers = pf.read("suppliers.csv")          # Supplier master data
inventory = pf.read("inventory.parquet")      # Warehouse system
shipments = pf.read("shipments.json")         # Logistics system

supply_chain_kpis = suppliers.sql("""
    SELECT
        s.supplier_id,
        s.supplier_name,
        s.country as supplier_country,
        s.supplier_tier,
        COUNT(DISTINCT i.product_id) as products_supplied,
        SUM(i.quantity_on_hand) as total_inventory,
        AVG(sh.delivery_days) as avg_delivery_days,
        COUNT(sh.shipment_id) as total_shipments,
        SUM(CASE WHEN sh.on_time_delivery = true THEN 1 ELSE 0 END) * 100.0 / COUNT(sh.shipment_id) as on_time_delivery_rate,
        AVG(sh.shipping_cost) as avg_shipping_cost,
        SUM(i.quantity_on_hand * i.unit_cost) as inventory_value
    FROM df s
    LEFT JOIN inventory i ON s.supplier_id = i.supplier_id
    LEFT JOIN shipments sh ON s.supplier_id = sh.supplier_id
    WHERE sh.shipment_date >= '2024-01-01'
    GROUP BY s.supplier_id, s.supplier_name, s.country, s.supplier_tier
    ORDER BY inventory_value DESC
""", inventory=inventory, shipments=shipments)
```

## Time Series Analysis

### Sales Trend Analysis

```python
sales_data = pf.read("daily_sales.parquet")

sales_trends = sales_data.sql("""
    WITH daily_metrics AS (
        SELECT
            DATE_TRUNC('day', sale_date) as day,
            SUM(sale_amount) as daily_sales,
            COUNT(DISTINCT customer_id) as daily_customers,
            COUNT(*) as daily_transactions,
            AVG(sale_amount) as avg_transaction_value
        FROM df
        WHERE sale_date >= '2024-01-01'
        GROUP BY DATE_TRUNC('day', sale_date)
    ),
    moving_averages AS (
        SELECT
            *,
            AVG(daily_sales) OVER (
                ORDER BY day
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) as sales_7day_ma,
            AVG(daily_sales) OVER (
                ORDER BY day
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) as sales_30day_ma,
            LAG(daily_sales, 7) OVER (ORDER BY day) as sales_7days_ago,
            LAG(daily_sales, 365) OVER (ORDER BY day) as sales_1year_ago
        FROM daily_metrics
    )
    SELECT
        day,
        daily_sales,
        daily_customers,
        daily_transactions,
        avg_transaction_value,
        sales_7day_ma,
        sales_30day_ma,
        CASE
            WHEN sales_7days_ago > 0 THEN
                (daily_sales - sales_7days_ago) / sales_7days_ago * 100
            ELSE NULL
        END as wow_growth_rate,
        CASE
            WHEN sales_1year_ago > 0 THEN
                (daily_sales - sales_1year_ago) / sales_1year_ago * 100
            ELSE NULL
        END as yoy_growth_rate,
        CASE
            WHEN daily_sales > sales_7day_ma * 1.2 THEN 'High'
            WHEN daily_sales < sales_7day_ma * 0.8 THEN 'Low'
            ELSE 'Normal'
        END as performance_vs_trend
    FROM moving_averages
    ORDER BY day
""")
```

### Seasonality Detection

```python
# Detect seasonal patterns in data
seasonality_analysis = sales_data.sql("""
    SELECT
        EXTRACT(month FROM sale_date) as month,
        EXTRACT(dow FROM sale_date) as day_of_week,
        EXTRACT(hour FROM sale_timestamp) as hour_of_day,
        COUNT(*) as transaction_count,
        SUM(sale_amount) as total_sales,
        AVG(sale_amount) as avg_transaction_value,
        -- Monthly seasonality index
        AVG(SUM(sale_amount)) OVER () as overall_avg_daily_sales,
        SUM(sale_amount) / AVG(SUM(sale_amount)) OVER () as seasonality_index
    FROM df
    WHERE sale_date >= '2023-01-01'
    GROUP BY
        EXTRACT(month FROM sale_date),
        EXTRACT(dow FROM sale_date),
        EXTRACT(hour FROM sale_timestamp)
    ORDER BY month, day_of_week, hour_of_day
""")
```

## Window Functions

### Advanced Analytics with Window Functions

```python
# Customer lifetime value analysis with window functions
customer_analytics = orders.sql("""
    WITH customer_orders AS (
        SELECT
            customer_id,
            order_date,
            order_amount,
            -- Running totals
            SUM(order_amount) OVER (
                PARTITION BY customer_id
                ORDER BY order_date
            ) as cumulative_spent,
            -- Order sequence
            ROW_NUMBER() OVER (
                PARTITION BY customer_id
                ORDER BY order_date
            ) as order_sequence,
            -- Time between orders
            LAG(order_date) OVER (
                PARTITION BY customer_id
                ORDER BY order_date
            ) as prev_order_date,
            -- Rolling averages
            AVG(order_amount) OVER (
                PARTITION BY customer_id
                ORDER BY order_date
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ) as rolling_3_order_avg
        FROM df
        WHERE order_date >= '2023-01-01'
    ),
    customer_metrics AS (
        SELECT
            customer_id,
            order_date,
            order_amount,
            cumulative_spent,
            order_sequence,
            DATEDIFF('day', prev_order_date, order_date) as days_since_last_order,
            rolling_3_order_avg,
            -- Percentile rankings
            PERCENT_RANK() OVER (ORDER BY cumulative_spent) as spending_percentile,
            NTILE(10) OVER (ORDER BY cumulative_spent) as spending_decile,
            -- First and last values
            FIRST_VALUE(order_date) OVER (
                PARTITION BY customer_id
                ORDER BY order_date
            ) as first_order_date,
            LAST_VALUE(order_date) OVER (
                PARTITION BY customer_id
                ORDER BY order_date
                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
            ) as last_order_date
        FROM customer_orders
    )
    SELECT
        customer_id,
        COUNT(*) as total_orders,
        MAX(cumulative_spent) as total_lifetime_value,
        AVG(order_amount) as avg_order_value,
        AVG(days_since_last_order) as avg_days_between_orders,
        MAX(spending_decile) as spending_decile,
        MAX(spending_percentile) as spending_percentile,
        MIN(first_order_date) as first_order_date,
        MAX(last_order_date) as last_order_date,
        DATEDIFF('day', MIN(first_order_date), MAX(last_order_date)) as customer_lifespan_days
    FROM customer_metrics
    GROUP BY customer_id
    ORDER BY total_lifetime_value DESC
""")
```

## Data Quality & Validation

### Comprehensive Data Quality Checks

```python
# Multi-dimensional data quality assessment
data_quality_report = raw_data.sql("""
    WITH quality_metrics AS (
        SELECT
            'completeness' as metric_type,
            'user_id' as column_name,
            COUNT(*) as total_rows,
            COUNT(user_id) as non_null_count,
            COUNT(DISTINCT user_id) as distinct_count,
            ROUND(COUNT(user_id) * 100.0 / COUNT(*), 2) as completeness_rate,
            COUNT(*) - COUNT(DISTINCT user_id) as duplicate_count
        FROM df

        UNION ALL

        SELECT
            'completeness' as metric_type,
            'email' as column_name,
            COUNT(*) as total_rows,
            COUNT(email) as non_null_count,
            COUNT(DISTINCT email) as distinct_count,
            ROUND(COUNT(email) * 100.0 / COUNT(*), 2) as completeness_rate,
            COUNT(*) - COUNT(DISTINCT email) as duplicate_count
        FROM df

        UNION ALL

        SELECT
            'validity' as metric_type,
            'email' as column_name,
            COUNT(*) as total_rows,
            COUNT(CASE WHEN email LIKE '%@%.%' THEN 1 END) as valid_count,
            0 as distinct_count,
            ROUND(COUNT(CASE WHEN email LIKE '%@%.%' THEN 1 END) * 100.0 / COUNT(*), 2) as validity_rate,
            0 as duplicate_count
        FROM df
        WHERE email IS NOT NULL

        UNION ALL

        SELECT
            'range_check' as metric_type,
            'age' as column_name,
            COUNT(*) as total_rows,
            COUNT(CASE WHEN age BETWEEN 0 AND 120 THEN 1 END) as valid_count,
            0 as distinct_count,
            ROUND(COUNT(CASE WHEN age BETWEEN 0 AND 120 THEN 1 END) * 100.0 / COUNT(*), 2) as validity_rate,
            0 as duplicate_count
        FROM df
        WHERE age IS NOT NULL
    )
    SELECT
        metric_type,
        column_name,
        total_rows,
        non_null_count,
        distinct_count,
        CASE
            WHEN metric_type = 'completeness' THEN completeness_rate
            ELSE validity_rate
        END as quality_score,
        duplicate_count,
        CASE
            WHEN quality_score >= 95 THEN 'Excellent'
            WHEN quality_score >= 80 THEN 'Good'
            WHEN quality_score >= 60 THEN 'Fair'
            ELSE 'Poor'
        END as quality_grade
    FROM quality_metrics
    ORDER BY metric_type, column_name
""")
```

### Anomaly Detection

```python
# Statistical anomaly detection using SQL
anomaly_detection = sales_data.sql("""
    WITH sales_stats AS (
        SELECT
            AVG(daily_sales) as mean_sales,
            STDDEV(daily_sales) as stddev_sales,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY daily_sales) as q1,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY daily_sales) as q3
        FROM (
            SELECT
                DATE_TRUNC('day', sale_date) as day,
                SUM(sale_amount) as daily_sales
            FROM df
            GROUP BY DATE_TRUNC('day', sale_date)
        ) daily_totals
    ),
    daily_sales_with_stats AS (
        SELECT
            day,
            daily_sales,
            s.mean_sales,
            s.stddev_sales,
            s.q1,
            s.q3,
            s.q3 - s.q1 as iqr,
            ABS(daily_sales - s.mean_sales) / s.stddev_sales as z_score
        FROM (
            SELECT
                DATE_TRUNC('day', sale_date) as day,
                SUM(sale_amount) as daily_sales
            FROM df
            GROUP BY DATE_TRUNC('day', sale_date)
        ) daily_totals
        CROSS JOIN sales_stats s
    )
    SELECT
        day,
        daily_sales,
        z_score,
        CASE
            WHEN ABS(z_score) > 3 THEN 'Extreme Outlier'
            WHEN ABS(z_score) > 2 THEN 'Moderate Outlier'
            WHEN daily_sales < (q1 - 1.5 * iqr) OR daily_sales > (q3 + 1.5 * iqr) THEN 'IQR Outlier'
            ELSE 'Normal'
        END as anomaly_type,
        CASE
            WHEN daily_sales > mean_sales + 2 * stddev_sales THEN 'Unusually High'
            WHEN daily_sales < mean_sales - 2 * stddev_sales THEN 'Unusually Low'
            ELSE 'Normal Range'
        END as anomaly_direction
    FROM daily_sales_with_stats
    WHERE ABS(z_score) > 1.5 OR
          daily_sales < (q1 - 1.5 * iqr) OR
          daily_sales > (q3 + 1.5 * iqr)
    ORDER BY ABS(z_score) DESC
""")
```

## Performance Optimization

### Query Performance Patterns

```python
# Optimized aggregation with partitioning
optimized_aggregation = large_dataset.sql("""
    -- Use column store benefits with selective projections
    SELECT
        customer_segment,
        product_category,
        COUNT(*) as transaction_count,
        SUM(amount) as total_amount,
        AVG(amount) as avg_amount
    FROM df
    WHERE
        transaction_date >= '2024-01-01'
        AND amount > 0  -- Early filtering
        AND customer_segment IN ('premium', 'gold', 'platinum')  -- Selective filtering
    GROUP BY customer_segment, product_category
    HAVING COUNT(*) >= 100  -- Post-aggregation filtering
    ORDER BY total_amount DESC
    LIMIT 100  -- Limit early
""",
context=pf.QueryContext(
    predicate_pushdown=True,
    projection_pushdown=True,
    memory_limit="2GB"
))

# Use indexes and partitioning hints for large datasets
partitioned_analysis = large_dataset.sql("""
    -- Partition-aware query for time series data
    SELECT
        DATE_TRUNC('month', order_date) as month,
        region,
        SUM(order_amount) as monthly_revenue,
        COUNT(DISTINCT customer_id) as unique_customers,
        COUNT(*) as order_count
    FROM df
    WHERE
        order_date >= '2024-01-01'
        AND order_date < '2024-07-01'  -- Explicit date range for partitioning
        AND region IN ('US', 'EU', 'APAC')  -- Selective filtering
    GROUP BY 1, 2  -- Use ordinal positions for clarity
    ORDER BY 1, 3 DESC
""",
profile=True  # Enable query profiling
)

# Print performance metrics
if hasattr(partitioned_analysis, 'execution_time'):
    print(f"Query executed in {partitioned_analysis.execution_time:.3f}s")
    print(f"Returned {partitioned_analysis.row_count} rows")
```

### Memory-Efficient Processing

```python
# Stream processing for large datasets
def process_large_dataset_in_chunks():
    """Process large dataset using streaming SQL approach."""

    # Use Dask for large datasets
    large_data = pf.read("very_large_dataset.parquet", islazy=True)

    # Process in temporal chunks
    monthly_results = []

    for year in [2023, 2024]:
        for month in range(1, 13):
            chunk_result = large_data.sql(f"""
                SELECT
                    '{year}-{month:02d}' as period,
                    customer_segment,
                    COUNT(*) as transactions,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount
                FROM df
                WHERE
                    EXTRACT(year FROM transaction_date) = {year}
                    AND EXTRACT(month FROM transaction_date) = {month}
                GROUP BY customer_segment
            """)

            # Convert to pandas for aggregation
            monthly_results.append(chunk_result.to_pandas())

    # Combine results
    import pandas as pd
    final_result = pd.concat(monthly_results, ignore_index=True)

    return pf.ParquetFrame(final_result)
```

## Advanced Analytics

### Statistical Analysis

```python
# Advanced statistical analysis using SQL
statistical_analysis = sales_data.sql("""
    WITH transaction_stats AS (
        SELECT
            customer_id,
            COUNT(*) as transaction_count,
            SUM(amount) as total_spent,
            AVG(amount) as avg_transaction,
            STDDEV(amount) as stddev_transaction,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount) as median_transaction,
            MIN(amount) as min_transaction,
            MAX(amount) as max_transaction,
            -- Coefficient of variation
            CASE
                WHEN AVG(amount) > 0 THEN STDDEV(amount) / AVG(amount)
                ELSE NULL
            END as cv
        FROM df
        WHERE transaction_date >= '2024-01-01'
        GROUP BY customer_id
        HAVING COUNT(*) >= 5  -- Minimum sample size
    ),
    customer_segments AS (
        SELECT
            *,
            -- Statistical scoring
            CASE
                WHEN cv <= 0.3 THEN 'Consistent Spender'
                WHEN cv <= 0.6 THEN 'Variable Spender'
                ELSE 'Irregular Spender'
            END as spending_pattern,
            -- Percentile ranking
            PERCENT_RANK() OVER (ORDER BY total_spent) as spending_percentile,
            PERCENT_RANK() OVER (ORDER BY transaction_count) as frequency_percentile,
            PERCENT_RANK() OVER (ORDER BY avg_transaction) as avg_amount_percentile
        FROM transaction_stats
    )
    SELECT
        spending_pattern,
        COUNT(*) as customer_count,
        ROUND(AVG(total_spent), 2) as avg_total_spent,
        ROUND(AVG(avg_transaction), 2) as avg_transaction_amount,
        ROUND(AVG(transaction_count), 1) as avg_transaction_count,
        ROUND(AVG(cv), 3) as avg_coefficient_of_variation,
        -- Business metrics
        ROUND(SUM(total_spent), 2) as segment_total_revenue,
        ROUND(AVG(spending_percentile), 3) as avg_spending_percentile
    FROM customer_segments
    GROUP BY spending_pattern
    ORDER BY avg_total_spent DESC
""")
```

### Predictive Analytics Setup

```python
# Prepare features for machine learning
ml_features = customer_data.sql("""
    WITH customer_features AS (
        SELECT
            c.customer_id,
            -- Demographics
            c.age,
            c.gender,
            c.country,
            c.city,
            -- Transactional features
            COUNT(o.order_id) as total_orders,
            SUM(o.order_amount) as total_spent,
            AVG(o.order_amount) as avg_order_value,
            STDDEV(o.order_amount) as order_value_stddev,
            -- Temporal features
            DATEDIFF('day', MIN(o.order_date), MAX(o.order_date)) as customer_lifetime_days,
            DATEDIFF('day', MAX(o.order_date), CURRENT_DATE) as days_since_last_order,
            -- Behavioral features
            COUNT(DISTINCT DATE_TRUNC('month', o.order_date)) as active_months,
            COUNT(DISTINCT p.category) as unique_categories,
            MODE() WITHIN GROUP (ORDER BY p.category) as preferred_category,
            -- Derived features
            AVG(o.order_amount) / NULLIF(STDDEV(o.order_amount), 0) as spending_consistency,
            COUNT(o.order_id) / NULLIF(DATEDIFF('day', MIN(o.order_date), MAX(o.order_date)), 0) * 365 as annual_order_frequency
        FROM df c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
        LEFT JOIN products p ON o.product_id = p.product_id
        WHERE o.order_date >= '2023-01-01'
        GROUP BY c.customer_id, c.age, c.gender, c.country, c.city
        HAVING COUNT(o.order_id) >= 3  -- Minimum transaction history
    ),
    feature_engineering AS (
        SELECT
            *,
            -- Categorical encoding
            CASE
                WHEN age < 25 THEN 'young'
                WHEN age < 35 THEN 'adult'
                WHEN age < 50 THEN 'middle_age'
                ELSE 'senior'
            END as age_group,
            -- Binning
            CASE
                WHEN total_spent <= 100 THEN 'low_value'
                WHEN total_spent <= 500 THEN 'medium_value'
                WHEN total_spent <= 1000 THEN 'high_value'
                ELSE 'premium_value'
            END as value_segment,
            -- Target variable (for churn prediction)
            CASE
                WHEN days_since_last_order > 90 THEN 1
                ELSE 0
            END as churn_risk
        FROM customer_features
    )
    SELECT * FROM feature_engineering
""", orders=orders, products=products)

# Export for ML pipeline
ml_features.save("customer_ml_features.parquet")
```

## Tips and Best Practices

### SQL Query Optimization Tips

1. **Use explicit column selection** instead of `SELECT *`
2. **Apply filters early** using WHERE clauses before JOINs
3. **Use appropriate data types** in comparisons
4. **Leverage indexes** with ORDER BY and GROUP BY
5. **Use LIMIT** for exploratory queries
6. **Profile your queries** with `profile=True` parameter

### Cross-Format Considerations

1. **Data type consistency**: Ensure compatible types across formats
2. **NULL handling**: Be explicit about NULL value treatment
3. **Performance**: Parquet > ORC > JSON > CSV for analytical queries
4. **Memory usage**: Use `islazy=True` for large datasets
5. **Schema validation**: Verify column names and types before JOINs

### Error Handling Patterns

```python
# Robust query execution with error handling
def safe_sql_query(dataframe, query, **kwargs):
    """Execute SQL query with comprehensive error handling."""
    try:
        # Validate query first
        from parquetframe.sql import validate_sql_query
        is_valid, warnings = validate_sql_query(query)

        if not is_valid:
            print(f"Query validation warnings: {warnings}")
            return None

        # Execute with profiling
        result = dataframe.sql(query, profile=True, **kwargs)

        # Check result
        if hasattr(result, 'execution_time'):
            print(f"Query executed successfully in {result.execution_time:.3f}s")
            print(f"Returned {result.row_count} rows")
            return result.data
        else:
            print(f"Query executed successfully, returned {len(result)} rows")
            return result

    except Exception as e:
        print(f"Query failed: {str(e)}")
        return None

# Usage
result = safe_sql_query(sales_data, """
    SELECT category, SUM(amount) as total
    FROM df
    GROUP BY category
    ORDER BY total DESC
""")
```

This cookbook provides comprehensive patterns for real-world SQL usage with ParquetFrame. Each recipe is designed to be production-ready and follows best practices for performance and maintainability.
