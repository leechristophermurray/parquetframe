"""
Demo of YAML-based Dashboard as Code.
"""

import numpy as np
import pandas as pd

from parquetframe.dac import GizaParser

# Mock Data Context
# In production, this would be connected to DataFusion/Parquet files
df_sales = pd.DataFrame(
    {
        "date": pd.date_range("2024-01-01", periods=100),
        "amount": np.random.randint(100, 1000, 100),
        "region": np.random.choice(["North", "South", "East", "West"], 100),
    }
)

data_context = {"sales": df_sales}

# Parse YAML
parser = GizaParser(data_context)
dashboard = parser.parse_file("examples/sales_dashboard.giza.yml")

# Save
dashboard.save("dac_yaml_demo.html")
print("Dashboard saved to dac_yaml_demo.html")
