"""
Demo of Dashboard as Code (DaC) feature.
"""

import pandas as pd
import numpy as np
from parquetframe.dac import Dashboard, Page, Row, Column, Metric, Table, Markdown, Chart

# Create sample data
dates = pd.date_range("2024-01-01", periods=30, freq="D")
df = pd.DataFrame({
    "Date": dates,
    "Sales": np.random.randint(100, 500, size=30),
    "Visitors": np.random.randint(1000, 5000, size=30),
})

# Create a simple plot (using pandas plotting backend which returns matplotlib axes usually, 
# but here we will just mock a plot or use a simple HTML string for demo if no plotting lib installed)
# For this demo, let's assume we might not have plotly installed in the env, so we'll simulate a chart.
# In a real scenario, we would pass a plotly fig object.

class MockFigure:
    def to_html(self, **kwargs):
        return '<div style="background: #eee; height: 100%; display: flex; align-items: center; justify-content: center;">Mock Chart Visualization</div>'

# Build Dashboard
dashboard = Dashboard(title="Sales Overview")
page = Page("Main")

# Header
page.add(Row([
    Column(12, children=[Markdown("# Monthly Sales Report\nOverview of performance for January 2024.")])
]))

# Metrics Row
total_sales = df["Sales"].sum()
total_visitors = df["Visitors"].sum()

page.add(Row([
    Column(6, children=[Metric("Total Sales", f"${total_sales:,}", delta="+12%")]),
    Column(6, children=[Metric("Total Visitors", f"{total_visitors:,}", delta="-5%", delta_color="inverse")]),
]))

# Content Row
page.add(Row([
    Column(8, children=[
        Markdown("## Sales Trend"),
        Chart(MockFigure(), height="300px")
    ]),
    Column(4, children=[
        Markdown("## Recent Data"),
        Table(df.tail(5))
    ])
]))

# Add page and save
dashboard.add_page(page)
dashboard.save("dac_demo.html")

print("Dashboard saved to dac_demo.html")
