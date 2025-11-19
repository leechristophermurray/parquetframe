"""
Giza YAML Parser for Dashboard as Code.

Parses *.giza.yml files into Dashboard objects.
"""

import yaml
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import pandas as pd

from .dashboard import Dashboard, Page
from .layout import Row, Column
from .widgets import Metric, Chart, Table, Markdown


@dataclass
class GizaSource:
    name: str
    table: str
    time_column: Optional[str] = None


@dataclass
class GizaMetric:
    name: str
    label: str
    sql: str
    format: Optional[str] = None


class GizaParser:
    """Parses Giza YAML files into Dashboard objects."""

    def __init__(self, data_context: Dict[str, pd.DataFrame]):
        """
        Args:
            data_context: Dictionary mapping source names to DataFrames.
        """
        self.data_context = data_context
        self.sources: Dict[str, GizaSource] = {}
        self.metrics: Dict[str, GizaMetric] = {}

    def parse_file(self, filepath: str) -> Dashboard:
        """Parse a Giza YAML file."""
        with open(filepath, "r") as f:
            spec = yaml.safe_load(f)
        return self.parse(spec)

    def parse(self, spec: Dict[str, Any]) -> Dashboard:
        """Parse a Giza dictionary spec."""
        # Validate version
        if spec.get("version") != "giza/v1":
            raise ValueError(f"Unsupported Giza version: {spec.get('version')}")

        # Parse definitions
        self._parse_sources(spec.get("sources", []))
        self._parse_metrics(spec.get("metrics", []))

        # Create Dashboard
        dash_spec = spec.get("dashboard", {})
        dashboard = Dashboard(
            title=dash_spec.get("name", "Untitled Dashboard")
        )

        # Create default page
        page = Page("Main")
        
        # Parse charts and add to layout
        charts_spec = spec.get("charts", [])
        layout_spec = dash_spec.get("layout")

        if layout_spec:
            # Custom layout not fully implemented in this MVP, 
            # falling back to auto-layout (grid of 2 columns)
            pass

        # Auto-layout: 2 charts per row
        current_row = []
        for i, chart_spec in enumerate(charts_spec):
            widget = self._create_widget(chart_spec)
            current_row.append(Column(6, children=[widget]))
            
            if len(current_row) == 2:
                page.add(Row(current_row))
                current_row = []
        
        if current_row:
            page.add(Row(current_row))

        dashboard.add_page(page)
        return dashboard

    def _parse_sources(self, sources: List[Dict[str, Any]]):
        for s in sources:
            self.sources[s["name"]] = GizaSource(
                name=s["name"],
                table=s["table"],
                time_column=s.get("time_column")
            )

    def _parse_metrics(self, metrics: List[Dict[str, Any]]):
        for m in metrics:
            self.metrics[m["name"]] = GizaMetric(
                name=m["name"],
                label=m.get("label", m["name"]),
                sql=m["sql"],
                format=m.get("format")
            )

    def _create_widget(self, spec: Dict[str, Any]) -> Any:
        chart_type = spec["type"]
        name = spec["name"]
        source_name = spec["source"]
        metric_names = spec["metrics"]
        
        # Get data
        df = self.data_context.get(source_name)
        if df is None:
            return Markdown(f"**Error**: Source '{source_name}' not found.")

        # Apply filters (Mock implementation - real SQL parsing is complex)
        # In a real implementation, we would use DataFusion or pandas query
        
        # Create Widget based on type
        if chart_type == "kpi":
            # For KPI, take the first metric and aggregate
            metric_name = metric_names[0]
            metric = self.metrics.get(metric_name)
            label = metric.label if metric else metric_name
            
            # Simple aggregation simulation (since we don't have full SQL engine here)
            # In production, this would execute the SQL expression
            value = 0
            if metric and "SUM" in metric.sql:
                col = metric.sql.replace("SUM(", "").replace(")", "").strip()
                # Try to find column in df
                if col in df.columns:
                    value = df[col].sum()
            elif metric and "COUNT" in metric.sql:
                value = len(df)
            else:
                # Fallback for demo
                value = "N/A"

            # Format
            fmt = metric.format if metric else None
            display_value = str(value)
            if fmt == "usd":
                display_value = f"${value:,.2f}"
            elif fmt == "integer":
                display_value = f"{value:,}"

            return Metric(label, display_value)

        elif chart_type == "table":
            # Return raw table
            cols = spec.get("dimensions", []) + metric_names
            # Filter columns that exist
            valid_cols = [c for c in cols if c in df.columns]
            return Table(df[valid_cols].head(10))

        elif chart_type in ["line", "bar"]:
            # Return chart placeholder or simple plot
            # For MVP, we return a Chart widget with a description
            return Chart(
                f"Chart: {name} ({chart_type}) - {', '.join(metric_names)}",
                height="300px"
            )

        return Markdown(f"Unknown chart type: {chart_type}")
