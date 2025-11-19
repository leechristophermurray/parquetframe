"""
Tests for Dashboard as Code (DaC).
"""

import pytest
import pandas as pd
from parquetframe.dac import Dashboard, Page, Row, Column, Metric, Table, Markdown, Chart, Container


def test_layout_structure():
    """Test layout hierarchy construction."""
    row = Row([
        Column(6, children=[Markdown("Left")]),
        Column(6, children=[Markdown("Right")])
    ])
    
    assert len(row.children) == 2
    assert isinstance(row.children[0], Column)
    assert row.children[0].width == 6
    assert isinstance(row.children[0].children[0], Markdown)


def test_dashboard_rendering():
    """Test full dashboard rendering."""
    dashboard = Dashboard("Test Dash")
    page = Page("Page 1")
    page.add(Row([Column(12, children=[Metric("KPI", 100)])]))
    dashboard.add_page(page)
    
    html = dashboard.render()
    
    assert "<!DOCTYPE html>" in html
    assert "Test Dash" in html
    assert "KPI" in html
    assert "100" in html
    assert "dac-metric" in html


def test_widget_rendering():
    """Test individual widget rendering."""
    # Metric
    m = Metric("Sales", "$100", delta="+10%")
    html = m.render()
    assert "Sales" in html
    assert "$100" in html
    assert "+10%" in html
    assert "dac-text-green" in html
    
    # Markdown
    md = Markdown("# Title")
    html = md.render()
    assert "<h1>Title</h1>" in html
    
    # Table
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    t = Table(df)
    html = t.render()
    assert "<table" in html
    assert "dac-table" in html
    assert "<th>A</th>" in html


def test_chart_rendering():
    """Test chart widget."""
    # Mock figure
    class MockFig:
        def __str__(self):
            return "MockChart"
            
    c = Chart(MockFig())
    html = c.render()
    assert "MockChart" in html
    assert "dac-chart" in html


def test_container_nesting():
    """Test deep nesting of containers."""
    c = Container()
    c.add(Row().add(Column().add(Markdown("Deep"))))
    
    html = c.render()
    assert "Deep" in html
    assert "dac-container" in html
    assert "dac-row" in html
    assert "dac-col" in html

if __name__ == "__main__":
    # Manual run
    test_layout_structure()
    test_dashboard_rendering()
    test_widget_rendering()
    test_chart_rendering()
    test_container_nesting()
    print("All DaC tests passed!")
