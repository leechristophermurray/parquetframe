# Enhanced Kanban Analytics

This enhanced version of the todo/kanban app showcases **all ParquetFrame features** in a real-world application.

## Features Demonstrated

### 1. SQL Analytics (`parquetframe.sql`)

```python
from parquetframe.sql import sql

# Analyze completion rates by priority
completion_by_priority = sql("""
    SELECT 
        priority,
        COUNT(*) as total_tasks,
        SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as completed,
        CAST(SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100 as completion_rate
    FROM tasks_df
    GROUP BY priority
    ORDER BY completion_rate DESC
""", tasks_df=tasks_df)
```

### 2. Time Series Analysis (`.ts` accessor)

```python
import parquetframe.time

# Daily task creation with 7-day rolling average
tasks_df = tasks_df.set_index('created_at')
daily_created = tasks_df.ts.resample('1D', agg='count')
rolling_avg = tasks_df.ts.rolling('7D', agg='mean')
```

### 3. Financial-Style Metrics (`.fin` accessor)

```python
import parquetframe.finance

# Team velocity trends (like stock analysis)
daily['velocity_sma_7'] = daily.fin.sma('count', window=7)
daily['velocity_trend'] = daily.fin.ema('count', span=5)
daily['momentum'] = daily.fin.rsi('count', period=14)
```

### 4. Burndown Chart

```python
# Generate burndown with smoothing
burndown = analytics.generate_burndown_chart(board_id, user_id)
# Uses .ts.rolling() for smoothed trend
```

## Running the Demo

```python
python -m examples.integration.todo_kanban.analytics_enhanced
```

## Output

The demo shows:
- **Completion Rate by Priority**: SQL aggregation analysis
- **Team Velocity**: Financial indicators applied to task completion
- **Burndown Chart**: Time series analysis of remaining work

## Real-World Applications

### Project Management
- Track sprint ve Velocity
- Predict completion dates
- Identify bottlenecks

### Team Analytics
- Measure productivity trends
- Analyze workload distribution
- Forecast resource needs

### Business Intelligence
- Generate executive dashboards
- Trend analysis
- Performance metrics

## Advanced Features

### SQL Queries
```python
# Complex multi-table analysis
result = sql("""
    SELECT 
        u.username,
        COUNT(DISTINCT t.task_id) as tasks_completed,
        AVG(DATEDIFF(day, t.created_at, t.updated_at)) as avg_completion_time
    FROM users u
    JOIN tasks t ON u.user_id = t.assigned_to
    WHERE t.status = 'done'
    GROUP BY u.username
    ORDER BY tasks_completed DESC
""", users=users_df, tasks=tasks_df)
```

### Time Series Forecasting
```python
# Predict future completion based on historical trends
historical = daily_created.ts.resample('1W', agg='sum')
forecast = historical.ts.rolling('4W', agg='mean')
```

### Performance Metrics
```python
# Calculate team "Sharpe ratio" for consistent delivery
returns = daily_velocity.fin.returns('count')
volatility = daily_velocity.fin.volatility('count', window=20)
consistency_score = returns.mean() / volatility.mean()
```

## Integration with Other Features

- **Knowlogy**: Query project management best practices
- **RAG**: AI-powered insights on team performance
- **Tetnus**: ML predictions for deadline estimation
- **GeoSpatial**: Team location analysis (if location data available)

## See Also

- [SQL Documentation](../../../docs/sql/index.md)
- [Time Series Guide](../../../docs/time/index.md)
- [Financial Analysis](../../../docs/finance/index.md)
- [API Reference](../../../docs/api_reference.md)
