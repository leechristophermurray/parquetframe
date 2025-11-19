"""
Tests for Giza YAML Parser.
"""

import pytest
import pandas as pd
import yaml
from parquetframe.dac import GizaParser, Dashboard, Metric, Table

@pytest.fixture
def sample_data():
    return {
        "sales": pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=5),
            "amount": [100, 200, 300, 400, 500],
            "region": ["N", "N", "S", "S", "E"]
        })
    }

@pytest.fixture
def sample_yaml(tmp_path):
    content = """
version: giza/v1
dashboard:
  name: "Test Dash"
sources:
  - name: sales
    table: "sales_tbl"
metrics:
  - name: total_rev
    sql: "SUM(amount)"
charts:
  - name: "Rev KPI"
    type: "kpi"
    source: "sales"
    metrics: ["total_rev"]
"""
    p = tmp_path / "test.giza.yml"
    p.write_text(content)
    return str(p)

def test_parser_structure(sample_data, sample_yaml):
    parser = GizaParser(sample_data)
    dash = parser.parse_file(sample_yaml)
    
    assert isinstance(dash, Dashboard)
    assert dash.title == "Test Dash"
    assert len(dash.pages) == 1
    
    # Check layout auto-generation
    page = dash.pages[0]
    assert len(page.children) > 0  # Should have rows

def test_metric_parsing(sample_data):
    yaml_spec = {
        "version": "giza/v1",
        "metrics": [
            {"name": "m1", "sql": "SUM(amount)", "format": "usd"}
        ],
        "charts": []
    }
    parser = GizaParser(sample_data)
    parser.parse(yaml_spec)
    
    assert "m1" in parser.metrics
    assert parser.metrics["m1"].format == "usd"

def test_kpi_generation(sample_data):
    yaml_spec = {
        "version": "giza/v1",
        "metrics": [{"name": "rev", "sql": "SUM(amount)"}],
        "charts": [
            {
                "name": "KPI",
                "type": "kpi",
                "source": "sales",
                "metrics": ["rev"]
            }
        ]
    }
    parser = GizaParser(sample_data)
    dash = parser.parse(yaml_spec)
    
    # Dig into layout to find widget
    # Page -> Row -> Column -> Widget
    widget = dash.pages[0].children[0].children[0].children[0]
    assert isinstance(widget, Metric)
    assert widget.label == "rev"
    assert widget.value == "1500"  # Sum of [100..500]

def test_invalid_version(sample_data):
    with pytest.raises(ValueError):
        GizaParser(sample_data).parse({"version": "v2"})

if __name__ == "__main__":
    # Manual run
    test_parser_structure(sample_data(), "test.yml")
    print("Tests passed")
