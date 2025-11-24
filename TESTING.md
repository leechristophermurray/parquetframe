# Testing Guide

## Local Testing with Virtual Environment

### Setup

```bash
# Create virtual environment
python3 -m venv .venv

# Activate
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# Install package and test dependencies
pip install -e .
pip install -r requirements-test.txt
```

### Run Tests

```bash
# Run all new feature tests
pytest tests/test_new_features.py -v

# Run with coverage
pytest tests/test_new_features.py -v --cov=parquetframe --cov-report=term-missing

# Run specific test class
pytest tests/test_new_features.py::TestSQLEngine -v

# Run parallel
pytest tests/test_new_features.py -v -n auto
```

## Tox Testing (Recommended)

Tox provides isolated testing environments for multiple Python versions.

### Install Tox

```bash
pip install tox
```

### Run Tests

```bash
# Run tests for all Python versions
tox

# Run for specific Python version
tox -e py311

# Run with minimal dependencies
tox -e minimal

# Run full test suite
tox -e full

# Format code
tox -e format

# Lint code
tox -e lint
```

### Available Tox Environments

- `py310`, `py311`, `py312`, `py313` - Test on different Python versions
- `minimal` - Test with minimal dependencies (SQL only)
- `full` - Full test suite with coverage report
- `lint` - Code quality checks (black, ruff, mypy)
- `format` - Auto-format code
- `docs` - Build documentation

## Test Organization

```
tests/
├── test_new_features.py       # New feature tests (SQL, time, geo, fin)
├── test_sql.py               # SQL engine tests
├── test_timeseries.py        # Time series tests
├── knowlogy/                 # Knowlogy tests
├── tetnus/                   # Tetnus ML tests
└── integration/              # Integration tests
    └── test_todo_kanban.py   # Kanban app tests
```

## Running Specific Tests

```bash
# SQL tests only
pytest tests/test_new_features.py::TestSQLEngine -v

# Time series tests
pytest tests/test_new_features.py::TestTimeSeriesAccessor -v

# Financial tests
pytest tests/test_new_features.py::TestFinanceAccessor -v

# GeoSpatial tests (requires geopandas)
pytest tests/test_new_features.py::TestGeoSpatialAccessor -v

# Integration tests
pytest tests/test_new_features.py::TestIntegration -v
```

## Test Coverage

Generate coverage report:

```bash
# Terminal report
pytest tests/test_new_features.py --cov=parquetframe --cov-report=term-missing

# HTML report
pytest tests/test_new_features.py --cov=parquetframe --cov-report=html
# Open htmlcov/index.html in browser
```

## Continuous Integration

Tests run automatically on:
- Push to main
- Pull requests
- Python 3.10, 3.11, 3.12, 3.13

## Troubleshooting

### Import Errors

If you get `ModuleNotFoundError`:

```bash
# Reinstall in development mode
pip install -e .
```

### GeoPandas Not Found

GeoPandas tests are skipped if not installed:

```bash
pip install geopandas shapely
```

### DataFusion/DuckDB Issues

SQL tests fallback to DuckDB if DataFusion not available:

```bash
pip install duckdb
# or
pip install datafusion
```

## Best Practices

1. **Always use virtual environment** for isolation
2. **Run tox** before committing to test multiple Python versions
3. **Check coverage** to ensure new code is tested
4. **Use `-v` flag** for verbose output
5. **Run `tox -e format`** before committing

## Quick Commands

```bash
# Setup and run tests
python3 -m venv .venv
source .venv/bin/activate
pip install -e . && pip install -r requirements-test.txt
pytest tests/test_new_features.py -v

# Or use tox
pip install tox
tox -e py311

# Format and lint
tox -e format
tox -e lint
```
