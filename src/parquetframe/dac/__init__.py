"""
Dashboard as Code (DaC) module.

Declarative framework for building interactive data dashboards.
"""

from .dashboard import Dashboard, Page
from .layout import Row, Column, Container
from .widgets import Widget, Chart, Table, Metric, Markdown
from .parser import GizaParser

__all__ = [
    "Dashboard",
    "Page",
    "Row",
    "Column",
    "Container",
    "Widget",
    "Chart",
    "Table",
    "Metric",
    "Markdown",
    "GizaParser",
]
